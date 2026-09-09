from openai import AsyncOpenAI

from .config import settings


def _client_and_model() -> tuple[AsyncOpenAI, str]:
    # Prefer Microsoft Foundry / Azure OpenAI when configured.
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
            "Set AZURE_OPENAI_API_KEY/AZURE_OPENAI_ENDPOINT/"
            "AZURE_OPENAI_DEPLOYMENT or OPENAI_API_KEY/OPENAI_MODEL."
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

    if not response.output_text:
        return None

    import json

    return json.loads(response.output_text)
