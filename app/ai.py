import asyncio
import json
import random
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


SYSTEM_PROMPT = """
You are Agent A, the Lead Generation Agent for a furnished 30+ day rental in
Northeast Dallas, Texas.

Search broadly for public evidence of housing demand, then classify each signal
before property-fit scoring. Return up to five distinct signals from one search.

Lead types:
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
not turn a rental advertisement into a demand lead. Missing budget must not by
itself disqualify a genuine demand signal. Prefer recent, specific, Dallas-area
evidence. Return an empty candidates array when no supported signal is found.
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


async def extract_candidate(query: str) -> dict | None:
    """Run one campaign-level search and return its best supported signal.

    The model may discover up to five signals in a single web-search call. They
    are deduplicated and scored locally; the highest-value supported candidate
    is returned to preserve compatibility with the existing campaign runner.
    """
    client, model = _client_and_model()

    response = await _create_response_with_transient_retry(
        client,
        model=model,
        instructions=SYSTEM_PROMPT,
        input=(
            "Run one broad campaign-level discovery search using all intent, "
            "location, profession, and duration predicates in this query. "
            "Return up to five distinct supported signals. Query: " + query
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
    if not raw_candidates:
        return None

    source_urls = _source_urls(response)
    source_url_set = set(source_urls)
    used_sources = set()
    seen_keys = set()
    candidates = []

    for item in raw_candidates:
        if item.get("lead_type") == "REJECT":
            continue

        source_url = item.get("source_url")
        if source_url not in source_url_set:
            source_url = next(
                (url for url in source_urls if url not in used_sources),
                None,
            )
        if source_url:
            used_sources.add(source_url)
        item["source_url"] = source_url

        evidence_key = " ".join(str(item.get("evidence", "")).lower().split())
        dedupe_key = source_url or evidence_key
        if not dedupe_key or dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)

        score = score_lead(item)
        item["score"] = score.score
        item["classification"] = score.classification
        item["score_reasons"] = score.reasons
        item["ai_confidence"] = item.get("confidence")
        candidates.append(item)

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
    return candidates[0]


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
