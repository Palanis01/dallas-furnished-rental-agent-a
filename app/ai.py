import asyncio
import json
import logging
import random
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)

from .config import settings
from .scoring import score_lead

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are Agent A, the Lead Generation Agent for a furnished 30+ day rental in
Northeast Dallas, Texas.

Use broad discovery first, then strict qualification. For each campaign request,
perform several varied public-web searches rather than treating the campaign brief
as one literal Boolean query. Search separately for direct housing intent,
temporary assignments or relocations, and organizations that arrange housing.
Do not require every candidate to contain every profession, duration, location,
or housing phrase in the campaign brief.

Return up to five distinct signals and classify each one:
- DIRECT_HOUSING_LEAD: a person or organization explicitly seeking furnished or
  temporary Dallas-area housing for roughly 30 days or longer.
- ORGANIZATION_LEAD: a legitimate organization that arranges temporary housing
  for employees, patients, insured households, contractors, or traveling staff.
- ASSIGNMENT_SIGNAL: a verified Dallas-area assignment, contract, relocation, or
  other temporary-work signal likely to create 30+ day housing demand, even when
  no explicit housing request is present.
- REJECT: rental advertisements, generic market articles, irrelevant pages,
  unsupported claims, or other evidence that should not become a lead.

Use only evidence supported by public web-search sources. Never invent identity,
dates, budget, employer, occupation, housing need, or contact information. Do
not turn a rental advertisement into a demand lead. Missing budget, exact dates,
or an explicit housing request must not by itself disqualify a credible
ORGANIZATION_LEAD or ASSIGNMENT_SIGNAL. Prefer recent, specific Dallas-area
evidence. The source_url for each candidate must be the exact public page that
supports that candidate's evidence, not a related housing provider or general
website. Return an empty candidates array only when no supported signal exists.
"""

CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "lead_type": {
            "type": "string",
            "enum": [
                "DIRECT_HOUSING_LEAD",
                "ORGANIZATION_LEAD",
                "ASSIGNMENT_SIGNAL",
                "REJECT",
            ],
        },
        "name": {"type": ["string", "null"]},
        "occupation": {"type": ["string", "null"]},
        "assignment_location": {"type": ["string", "null"]},
        "move_in": {"type": ["string", "null"]},
        "move_out": {"type": ["string", "null"]},
        "stay_days": {"type": ["integer", "null"]},
        "budget": {"type": ["number", "null"]},
        "reason_for_stay": {"type": ["string", "null"]},
        "evidence": {"type": "string"},
        "source_url": {"type": ["string", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "lead_type",
        "name",
        "occupation",
        "assignment_location",
        "move_in",
        "move_out",
        "stay_days",
        "budget",
        "reason_for_stay",
        "evidence",
        "source_url",
        "confidence",
    ],
    "additionalProperties": False,
}

DISCOVERY_SCHEMA = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "maxItems": 5,
            "items": CANDIDATE_SCHEMA,
        }
    },
    "required": ["candidates"],
    "additionalProperties": False,
}

MAX_TRANSIENT_RETRIES = 4
BASE_BACKOFF_SECONDS = 4.0
MAX_BACKOFF_SECONDS = 45.0
MAX_OUTPUT_TOKENS = 2000
TRANSIENT_EXCEPTIONS = (
    RateLimitError,
    InternalServerError,
    APIConnectionError,
    APITimeoutError,
)


def _client_and_model() -> tuple[AsyncOpenAI, str]:
    if (
        settings.azure_openai_api_key
        and settings.azure_openai_endpoint
        and settings.azure_openai_deployment
    ):
        client = AsyncOpenAI(
            api_key=settings.azure_openai_api_key,
            base_url=settings.azure_openai_endpoint.rstrip("/") + "/",
            max_retries=0,
        )
        return client, settings.azure_openai_deployment

    if not settings.openai_api_key:
        raise RuntimeError(
            "No AI provider is configured. "
            "Set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_DEPLOYMENT, or configure direct OpenAI."
        )

    if not settings.openai_model:
        raise RuntimeError("OPENAI_MODEL is required for direct OpenAI fallback")

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        max_retries=0,
    )
    return client, settings.openai_model


def _retry_delay_seconds(exc: Exception, attempt: int) -> float:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)

    if headers:
        retry_after_ms = (
            headers.get("retry-after-ms")
            or headers.get("x-ms-retry-after-ms")
        )
        if retry_after_ms:
            try:
                return min(
                    MAX_BACKOFF_SECONDS,
                    max(0.0, float(retry_after_ms) / 1000.0),
                )
            except (TypeError, ValueError):
                pass

        retry_after = headers.get("retry-after")
        if retry_after:
            try:
                return min(
                    MAX_BACKOFF_SECONDS,
                    max(0.0, float(retry_after)),
                )
            except (TypeError, ValueError):
                try:
                    retry_at = parsedate_to_datetime(retry_after)
                    if retry_at.tzinfo is None:
                        retry_at = retry_at.replace(tzinfo=timezone.utc)
                    delay = (
                        retry_at - datetime.now(timezone.utc)
                    ).total_seconds()
                    return min(MAX_BACKOFF_SECONDS, max(0.0, delay))
                except (TypeError, ValueError, OverflowError):
                    pass

    exponential = BASE_BACKOFF_SECONDS * (2**attempt)
    jitter = random.uniform(0.0, 1.0)
    return min(MAX_BACKOFF_SECONDS, exponential + jitter)


async def _create_response_with_transient_retry(
    client: AsyncOpenAI,
    **kwargs,
):
    last_error = None

    for attempt in range(MAX_TRANSIENT_RETRIES + 1):
        try:
            return await client.responses.create(**kwargs)
        except TRANSIENT_EXCEPTIONS as exc:
            last_error = exc

            if attempt >= MAX_TRANSIENT_RETRIES:
                raise

            await asyncio.sleep(_retry_delay_seconds(exc, attempt))

    if last_error is not None:
        raise last_error

    raise RuntimeError("AI response request failed without an exception")


def _normalize_url(url: str) -> str:
    return url.strip().rstrip("/.,;)")


def _evidence_urls(evidence: str | None) -> list[str]:
    if not evidence:
        return []
    return [
        _normalize_url(url)
        for url in re.findall(r"https?://[^\s\]\[<>]+", evidence)
    ]


def _resolve_source_url(
    evidence: str | None,
    model_source_url: str | None,
    web_source_urls: list[str],
) -> str | None:
    """Return only a source URL that is both cited by evidence/model and web-grounded."""
    source_map = {_normalize_url(url): url for url in web_source_urls if url}

    for cited_url in _evidence_urls(evidence):
        if cited_url in source_map:
            return source_map[cited_url]

    if model_source_url:
        normalized_model_url = _normalize_url(model_source_url)
        if normalized_model_url in source_map:
            return source_map[normalized_model_url]

    return None


async def extract_candidate(query: str) -> dict | None:
    """Run one campaign-level search and return its best supported signal."""
    client, model = _client_and_model()

    response = await _create_response_with_transient_retry(
        client,
        model=model,
        instructions=SYSTEM_PROMPT,
        input=(
            "Treat the following as a discovery brief, not as a literal search string. "
            "Run multiple varied searches within this one web-search-enabled response. "
            "First search for explicit housing need; then temporary assignment/relocation "
            "signals; then organizations that coordinate temporary housing. Return up to "
            "five distinct supported signals and classify them. Campaign brief: " + query
        ),
        tools=[
            {
                "type": "web_search",
                "search_context_size": "medium",
            }
        ],
        tool_choice="required",
        reasoning={"effort": "low"},
        max_output_tokens=MAX_OUTPUT_TOKENS,
        text={
            "format": {
                "type": "json_schema",
                "name": "campaign_discovery",
                "strict": True,
                "schema": DISCOVERY_SCHEMA,
            }
        },
        include=["web_search_call.action.sources"],
    )

    data = json.loads(response.output_text)
    raw_candidates = data.get("candidates", [])
    source_urls = _source_urls(response)

    logger.info(
        "Discovery summary: raw_candidates=%d web_sources=%d",
        len(raw_candidates),
        len(source_urls),
    )

    if not raw_candidates:
        return None

    seen_keys = set()
    candidates = []
    rejected_count = 0
    duplicate_count = 0
    ungrounded_source_count = 0

    for item in raw_candidates:
        if item.get("lead_type") == "REJECT":
            rejected_count += 1
            continue

        source_url = _resolve_source_url(
            item.get("evidence"),
            item.get("source_url"),
            source_urls,
        )
        if not source_url:
            ungrounded_source_count += 1
        item["source_url"] = source_url

        evidence_key = " ".join(str(item.get("evidence", "")).lower().split())
        dedupe_key = source_url or evidence_key
        if not dedupe_key or dedupe_key in seen_keys:
            duplicate_count += 1
            continue
        seen_keys.add(dedupe_key)

        score = score_lead(item)
        item["score"] = score.score
        item["classification"] = score.classification
        item["score_reasons"] = score.reasons
        item["ai_confidence"] = item.get("confidence")
        candidates.append(item)

    logger.info(
        "Discovery qualification: accepted_candidates=%d rejected_candidates=%d "
        "duplicate_candidates=%d ungrounded_source_candidates=%d",
        len(candidates),
        rejected_count,
        duplicate_count,
        ungrounded_source_count,
    )

    if not candidates:
        return None

    lead_type_rank = {
        "DIRECT_HOUSING_LEAD": 3,
        "ORGANIZATION_LEAD": 2,
        "ASSIGNMENT_SIGNAL": 1,
    }
    candidates.sort(
        key=lambda item: (
            lead_type_rank.get(item.get("lead_type"), 0),
            item.get("score", 0),
            item.get("confidence", 0),
        ),
        reverse=True,
    )

    selected = candidates[0]
    logger.info(
        "Discovery selected: lead_type=%s classification=%s score=%s source_url=%s",
        selected.get("lead_type"),
        selected.get("classification"),
        selected.get("score"),
        selected.get("source_url"),
    )
    return selected


def _source_urls(response) -> list[str]:
    payload = response.model_dump() if hasattr(response, "model_dump") else {}
    urls = []
    seen = set()

    for item in payload.get("output", []):
        if item.get("type") != "web_search_call":
            continue

        action = item.get("action", {})
        for source in action.get("sources", []) or []:
            url = source.get("url")
            if url and url not in seen:
                seen.add(url)
                urls.append(url)

    return urls
