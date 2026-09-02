#!/usr/bin/env bash
set -euo pipefail

command -v az >/dev/null || { echo "Azure CLI is required."; exit 1; }

az account show --output table

echo
echo "Checking resource providers..."
for ns in Microsoft.Web Microsoft.DBforPostgreSQL; do
  echo "--- $ns ---"
  az provider show --namespace "$ns" --query "{namespace:namespace, registrationState:registrationState}" -o table
  done

echo
echo "Checking available Linux Python runtimes for App Service..."
az webapp list-runtimes --os-type linux | grep -E 'PYTHON\|3\.(1[2-4])' || true

echo
echo "Checking Azure Database for PostgreSQL SKUs/availability is subscription/region specific; create the server only after confirming the portal exposes it for this subscription."
echo
echo "No credentials are read by this script beyond the existing Azure CLI login session."
