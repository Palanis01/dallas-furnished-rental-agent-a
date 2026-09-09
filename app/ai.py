import json

from openai import AsyncOpenAI

from .config import settings
from .scoring import score_lead


SYSTEM_PROMPT = """
You are Agent A, the Lead Generation Agent for a furnished 30+ day rental in
Northeast Dallas, Texas.

Use only evidence supported by public web sources returned by web search.
Never invent a person's identity, dates, budget, employer, occupation, or
housing need. A generic article, property listing, staffing-company page, or
job posting is not automatically a tenant lead. Return a candidate only when
the source provides a plausible, evidence-based housing-demand signal.
Do not infer protected characteristics or collect unnecessary sensitive data.
Do not provide or infer personal contact information unless it is explicitly
present in a public source and necessary for the lead-generation purpose.
"""

LEAD_SCHEMA = {
    "type": "object",
    "properties": {
        "is_candidate": {"type": "boolean"},
        "name": {"type": ["string", "null"]},
        "occupation": {"type": ["string", "null"]},
        "assignment_location": {"type": ["string", "null"]},
        "move_in": {"type": ["string", "null"]},
        "move_out": {"type": ["string", "null"]},
        "stay_days": {"type": ["integer", "null"]},
        "budget": {"type": ["number", "null"]},
        "reason_for_stay": {"type": ["string", "null"]},
        "evidence": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "is_candidate",
        "name",
        "occupation",
        "assignment_location",
        "move_in",
        "move_out",
        "stay_days",
        "budget",
        "reason_for_stay",
        "evidence",
        "confidence",
    ],
    "additionalProperties": False,
}


def _client_and_model() -> tuple[AsyncOpenAI, str]:
    # Prefer Microsoft Foundry / Azure OpenAI.
    if (
        settings.azure_openai_api_key
        and settings.azure_openai_endpoint
        and settings.azure_openai_deployment
    ):
        client = AsyncOpenAI(
            api_key=settings.azure_openai_api_key,
            base_url=settings.azure_openai_endpoint.rstrip("/") + "/",
        )
        return client, settings.azure_openai_deployment

    # Fallback to direct OpenAI.
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
    )
    return client, settings.openai_model


async def extract_candidate(query: str) -> dict | None:
    client, model = _client_and_model()

    response = await client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=(
            "Find public-web evidence relevant to this demand query and extract a "
            "potential 30+ day furnished-rental lead. Query: " + query
        ),
        tools=[
            {
                "type": "web_search",
                "search_context_size": "medium",
            }
        ],
        tool_choice="required",
        text={
            "format": {
                "type": "json_schema",
                "name": "lead_candidate",
                "strict": True,
                "schema": LEAD_SCHEMA,
            }
        },
        include=["web_search_call.action.sources"],
    )

    data = json.loads(response.output_text)

    if not data.get("is_candidate"):
        return None

    data["source_url"] = _first_source_url(response)

    score = score_lead(data)
    data["score"] = score.score
    data["classification"] = score.classification
    data["score_reasons"] = score.reasons
    data["ai_confidence"] = data.get("confidence")

    return data


def _first_source_url(response) -> str | None:
    payload = response.model_dump() if hasattr(response, "model_dump") else {}

    for item in payload.get("output", []):
        if item.get("type") != "web_search_call":
            continue

        action = item.get("action", {})

        for source in action.get("sources", []) or []:
            url = source.get("url")

            if url:
                return url

    return None
