# Deploy Agent A to Azure App Service on Linux (no Entra required)

This deployment profile is designed for a minimal Microsoft Azure subscription where Microsoft Entra tenant/OIDC setup is unavailable.

## Recommended Azure layout

Use a **separate App Service resource** for Agent A. It can remain in the same Azure subscription and, preferably, in a separate resource group such as `rg-dallas-rental-agent-a`. This keeps the flight engine and rental agent operationally isolated while avoiding the cost of a second subscription.

Create a separate GitHub repository rather than mixing Agent A into the flight-engine repository. Recommended repository name:

`dallas-furnished-rental-agent-a`

## Azure services

Minimum production resources:

1. Azure App Service (Linux, Python 3.12)
2. Azure Database for PostgreSQL Flexible Server (recommended persistent database)
3. OpenAI API account/key for Agent A web search and structured extraction

Azure Database for PostgreSQL Flexible Server is a current Azure managed service. Use a currently supported PostgreSQL major version; do not create a new server on PostgreSQL 11/12/13. See Microsoft's current supported-version guidance.

## Why PostgreSQL remains the primary database

Agent A uses standard SQLAlchemy + psycopg and accepts a `DATABASE_URL`. Azure Database for PostgreSQL Flexible Server is directly supported by Azure, so no code change is required for PostgreSQL.

If your particular subscription blocks creation of the PostgreSQL resource, do not silently substitute SQLite for production. Instead, provision an Azure-supported managed relational database and add a tested SQLAlchemy dialect adapter as a separate release.

SQLite is for local development/testing only.

## 1. Create the App Service

Example Azure CLI:

```bash
az login

az group create \
  --name rg-dallas-rental-agent-a \
  --location eastus

az appservice plan create \
  --name asp-dallas-rental-agent-a \
  --resource-group rg-dallas-rental-agent-a \
  --is-linux \
  --sku B1

az webapp create \
  --name YOUR_UNIQUE_APP_NAME \
  --resource-group rg-dallas-rental-agent-a \
  --plan asp-dallas-rental-agent-a \
  --runtime "PYTHON:3.12"
```

## 2. Configure FastAPI startup

For Python 3.12, use the explicit startup command documented by Azure for FastAPI:

```bash
az webapp config set \
  --resource-group rg-dallas-rental-agent-a \
  --name YOUR_UNIQUE_APP_NAME \
  --startup-file "gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app"
```

## 3. Configure application settings

Set these values in Azure App Service > Environment variables. Do not commit them to GitHub.

```text
ENVIRONMENT=production
SCM_DO_BUILD_DURING_DEPLOYMENT=1
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@SERVER.postgres.database.azure.com:5432/agent_a?sslmode=require
AGENT_API_KEY=<long-random-secret>
OPENAI_API_KEY=<OpenAI-key>
OPENAI_MODEL=<model-enabled-for-your-account>
OPENAI_BASE_URL=https://api.openai.com/v1
```

The OpenAI model name is intentionally an environment variable. Do not assume a model is available in the user's account or region.

## 4. GitHub deployment without Entra/OIDC

Because this environment is intended for a subscription without Entra tenant/OIDC capability, use the Azure App Service **publish profile** as an encrypted GitHub Actions secret.

Create GitHub repository secret:

`AZURE_WEBAPP_PUBLISH_PROFILE`

Then change `AZURE_WEBAPP_NAME` in `.github/workflows/deploy-azure.yml`.

Push to `main` and the workflow will:

1. Install Python 3.12
2. Install dependencies
3. Run tests
4. Run Azure App Service build
5. Deploy to the named App Service

Azure documents publish-profile deployment as a supported GitHub Actions method; OIDC is an alternative but requires Entra configuration.

## 5. PostgreSQL

Create Azure Database for PostgreSQL Flexible Server in the same region as the App Service where practical.

Use a currently supported PostgreSQL major version. Microsoft currently lists 18, 17, 16, 15, 14, 13, 12 and 11 as available in the service documentation, but PostgreSQL 11–13 reached their standard support dates in 2026 and should not be selected for a new production server.

For a new production deployment, choose a currently supported major version such as PostgreSQL 16/17/18 subject to the Azure portal options available to your subscription.

## 6. Validate your actual subscription

The repository includes:

`scripts/azure_preflight.sh`

Run it after `az login` to inspect the current subscription and check whether the resource providers needed by Agent A are available.

It does **not** use or store your password.

```bash
bash scripts/azure_preflight.sh
```

## 7. Final smoke test

```bash
curl https://YOUR_APP.azurewebsites.net/health
```

Expected response:

```json
{"status":"ok","service":"Dallas Furnished Rental - Agent A"}
```

## Authentication note

Agent A V1.2.0 does not require Microsoft Entra ID. It uses:

- GitHub Actions → Azure App Service: publish-profile secret
- Agent A → OpenAI API: OpenAI API key
- Agent API endpoint → owner/scheduler: `X-Agent-Key`
- App → PostgreSQL: database connection string

This is intentionally compatible with the subscription constraint supplied for this project.

## API/software licensing note

The Python OpenAI client used by the package is an open-source SDK. The OpenAI hosted API itself is a commercial service and is not open-source. It is not technically possible to describe the hosted OpenAI API as open-source. The package therefore uses an open-source client library and avoids proprietary search SDKs such as the earlier direct Bing adapter.
