import logging

from sqlalchemy.orm import Session

from .property import CAMPAIGN_QUERIES
from .ai import extract_candidate
from .models import Lead, SearchRun

logger = logging.getLogger(__name__)


async def run_campaign(
    db: Session,
    campaign: str,
    max_queries: int,
):
    queries = CAMPAIGN_QUERIES[campaign][:max_queries]
    stats = {
        "campaign": campaign,
        "queries": 0,
        "results": 0,
        "new_leads": 0,
        "provider_errors": 0,
        "no_candidate_queries": 0,
        "duplicate_leads": 0,
    }

    seen_urls = set()

    for query in queries:
        stats["queries"] += 1

        try:
            candidate = await extract_candidate(query)
        except Exception:
            stats["provider_errors"] += 1
            logger.exception(
                "Demand-signal search failed: campaign=%s query=%s",
                campaign,
                query,
            )
            db.add(
                SearchRun(
                    campaign=campaign,
                    query=query,
                    results_found=0,
                )
            )
            continue

        db.add(
            SearchRun(
                campaign=campaign,
                query=query,
                results_found=1 if candidate else 0,
            )
        )

        if not candidate:
            stats["no_candidate_queries"] += 1
            logger.info(
                "Demand-signal search completed with no qualifying candidate: "
                "campaign=%s query=%s",
                campaign,
                query,
            )
            continue

        stats["results"] += 1

        source_url = candidate.get("source_url")
        result_key = source_url or f"{campaign}:{query}"

        if result_key in seen_urls:
            stats["duplicate_leads"] += 1
            continue

        seen_urls.add(result_key)

        existing = None

        if source_url:
            existing = (
                db.query(Lead)
                .filter(Lead.url == source_url)
                .first()
            )

        if existing:
            stats["duplicate_leads"] += 1
            continue

        lead = Lead(
            name=candidate.get("name"),
            source="azure_openai_web_search",
            campaign=campaign,
            url=source_url,
            occupation=candidate.get("occupation"),
            assignment_location=candidate.get("assignment_location"),
            move_in=candidate.get("move_in"),
            move_out=candidate.get("move_out"),
            stay_days=candidate.get("stay_days"),
            budget=candidate.get("budget"),
            reason_for_stay=candidate.get("reason_for_stay"),
            evidence=candidate.get("evidence"),
            score=candidate.get("score", 0),
            classification=candidate.get("classification", "LOW"),
            ai_confidence=candidate.get("ai_confidence"),
            status="NEW",
            approved_for_contact=False,
        )

        db.add(lead)
        stats["new_leads"] += 1

    db.commit()

    status = "completed"
    if stats["provider_errors"] and stats["provider_errors"] == stats["queries"]:
        status = "provider_error"
    elif stats["provider_errors"]:
        status = "completed_with_errors"

    return {
        **stats,
        "status": status,
    }
