# Dallas Furnished Rental — Agent A: Lead Generation Agent v1.2.0

Agent A discovers public-web demand signals for a furnished 30+ day Northeast Dallas rental, extracts evidence-based candidate leads, scores them, and stores them for human review.

## V1.2.0 project direction

This release is designed for the user's stated environment:

- Azure App Service on Linux
- Python 3.12
- No Microsoft Entra tenant required
- GitHub repository → GitHub Actions → Azure App Service using an encrypted App Service publish profile
- Azure Database for PostgreSQL Flexible Server as the production database
- OpenAI public API for Responses API + web search + structured output

The flight-engine Agent should remain in its existing repository. Agent A should use a separate GitHub repository and, preferably, a separate Azure resource group while staying in the same subscription.

## What Agent A does

- Property Brain
- Healthcare demand discovery
- Corporate/IT demand discovery
- Relocation demand discovery
- Partner/referral demand discovery
- Social/public-web demand discovery
- OpenAI Responses API with `web_search`
- Structured lead extraction
- Deterministic lead scoring
- PostgreSQL/SQLite through SQLAlchemy
- FastAPI API
- Human approval state before future outreach
- GitHub Actions CI/CD
- Azure App Service Linux deployment
- Azure preflight script

## What it does NOT do yet

- log into Facebook, Instagram, TikTok, LinkedIn, Furnished Finder, Airbnb, Booking.com, or CircleRN
- scrape private social-media data
- automatically send unsolicited messages
- automatically publish advertisements
- approve or reject tenants
- perform tenant screening

Those functions belong in later versions and should use official platform APIs/OAuth where the platform provides them.

## Security

Never put passwords, API keys, database passwords, publish profiles, or OAuth tokens in source code, `.env` committed to Git, prompts, or documentation.

The package intentionally does not contain any user credentials.

## Local Linux setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set OPENAI_API_KEY and OPENAI_MODEL only when testing live AI calls
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Run tests:

```bash
pytest -q
```

## Azure deployment

Read `docs/DEPLOY_AZURE.md`.

For Python 3.12 FastAPI, Azure App Service requires a custom startup command. The package provides `startup.sh` and documents the command.

## Current API design

Agent A uses the OpenAI Python SDK's current Responses API and `web_search` tool. The SDK is open source; the hosted OpenAI API is a commercial service and is not open-source.

## Production database

Use Azure Database for PostgreSQL Flexible Server. SQLite is local-only.

The code accepts any SQLAlchemy-compatible URL, so the application is not hard-coded to one database host.

## QA

The repository includes unit tests, compile checks, static deprecated-pattern checks, workflow YAML validation, and a preflight script. A live Azure smoke test requires the user's actual Azure resources and cannot be truthfully claimed until those resources are supplied/configured.
