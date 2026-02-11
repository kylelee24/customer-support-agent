# Deployment

Two deployment paths exist depending on what changed.

## Quick Deploy (Code Changes Only)

Use `scripts/deploy.sh` when you've changed application code and the Azure infrastructure already exists.

```bash
bash scripts/deploy.sh
```

This script:
1. Builds the Docker image in Azure Container Registry (`az acr build`)
2. Updates the Container App with the new image (`az containerapp update`)
3. Tags the image with a timestamp (e.g., `app:0209195732`)

Hardcoded values in the script:
- Subscription: `aff3f8cf-511e-4af8-a2ae-ba765091e13a`
- Resource group: `rg-cs-agent`
- Registry: `crrqbabnxvnuxpe`
- Container app: `callcenterapp`

## Full Provisioning (New Environment)

Use this path when setting up a new Azure environment from scratch.

### 1. Provision Azure Resources

```bash
azd auth login
azd up
# Recommended values:
#   location: northeurope
#   aiResourceLocation: swedencentral
```

This provisions all resources via Bicep templates in `infra/` and runs the post-provision hooks in `azd-hooks/`.

### 2. Acquire a Phone Number

Phone number provisioning is manual:
1. Go to the Azure Portal > your Communication Services resource
2. Select **Phone numbers** > **Get**
3. Choose a country and **Toll free** number type
4. Purchase the number
5. Add to your environment: `azd env set ACS_SOURCE_NUMBER +1XXXXXXXXXX`

### 3. Deploy the Application

```bash
source <(azd env get-values | grep AZURE_ENV_NAME)
bash azd-hooks/deploy.sh app $AZURE_ENV_NAME
```

This script:
1. Discovers all Azure resources in the resource group
2. Builds and pushes the Docker image to ACR
3. Deploys the Container App via Bicep with all environment variables
4. Uploads knowledge base documents to blob storage
5. Outputs the application URI

### 4. Configure Inbound Calls

1. Go to the Azure Portal > **Event Grid System Topic** resource
2. Create an Event Subscription:
   - Event type: **Incoming Call**
   - Endpoint: `https://<YOUR_APP>.azurecontainerapps.io/acs/incoming`

## Local Development

### Prerequisites

- Python 3.12+
- Azure CLI with `communication` extension (`az extension add --name communication`)
- [ngrok](https://ngrok.com/) (for phone call testing)
- An existing Azure environment (provisioned via `azd up`)

### Setup

```bash
# Create and activate virtual environment (one-time)
python -m venv .venv
source .venv/bin/activate
pip install -r src/app/requirements.txt

# Load environment variables from Azure
source <(azd env get-values)
azd env get-values > .env
```

### Start ngrok (Required for Phone Calls)

```bash
ngrok http http://localhost:8765
```

Note the forwarding URL (e.g., `https://abc123.ngrok-free.app`) and set:

```bash
export ACS_CALLBACK_PATH="https://<NGROK_DOMAIN>/acs"
export ACS_MEDIA_STREAMING_WEBSOCKET_PATH="wss://<NGROK_DOMAIN>/realtime-acs"
```

### Run

```bash
python src/app/app.py
# Starts on localhost:8765
```

For inbound calls during local dev, create a separate Event Grid subscription pointing to your ngrok URL.

## Running Tests

```bash
# Install test dependencies (one-time)
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=term-missing

# Run a specific test file
pytest tests/test_transcript_manager.py -v
```

The test suite (110 tests) covers all backend modules using mocks — no Azure credentials or live services required.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME` | Yes | Deployment name for gpt-4o-realtime |
| `AZURE_OPENAI_API_KEY` | Yes* | API key (or use managed identity) |
| `AZURE_TENANT_ID` | No | Tenant ID for managed identity auth |
| `ACS_CONNECTION_STRING` | Yes | Azure Communication Services connection string |
| `ACS_SOURCE_NUMBER` | Yes | Phone number in E.164 format (e.g., `+14155551234`) |
| `ACS_CALLBACK_PATH` | Yes | Public URL for ACS call webhooks (e.g., `https://app.azurecontainerapps.io/acs`) |
| `ACS_MEDIA_STREAMING_WEBSOCKET_PATH` | Yes | Public WebSocket URL for ACS audio (e.g., `wss://app.azurecontainerapps.io/realtime-acs`) |
| `AZURE_SEARCH_ENDPOINT` | No | Azure AI Search endpoint (enables RAG) |
| `AZURE_SEARCH_INDEX` | No | Search index name (default: `voicerag-intvect`) |
| `AZURE_SEARCH_API_KEY` | No | Search API key |
| `AZURE_SEARCH_SEMANTIC_CONFIGURATION` | No | Semantic config name (default: `default`) |
| `ACS_EMAIL_CONNECTION_STRING` | No | ACS connection string for email (enables transcript emails) |
| `ACS_EMAIL_SENDER` | No | Verified sender address (e.g., `DoNotReply@xxx.azurecomm.net`) |
| `TRANSCRIPT_EMAIL_RECIPIENTS` | No | Comma-separated email list for transcript delivery |
| `HOST` | No | Server bind address (default: `localhost`) |
| `PORT` | No | Server port (default: `8765`) |

\* Either `AZURE_OPENAI_API_KEY` or managed identity via `AZURE_TENANT_ID` is required.

## System Prompt Override

At startup, the app tries to fetch `system_prompt.md` from the Azure Storage `prompt` container. If found, it overrides the local file at `src/app/system_prompt.md`. This allows updating the AI agent's behavior without redeploying.

To update the remote prompt:
```bash
az storage blob upload \
  --account-name <STORAGE_ACCOUNT> \
  --container-name prompt \
  --name system_prompt.md \
  --file src/app/system_prompt.md
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Property search returns 0 results / 403 | Cloudflare (WP Engine) blocking requests from Azure IPs | Ensure `API_HEADERS` includes a `User-Agent` header in `property_search.py` |
| No phone number available | ACS phone number not purchased or not set | Purchase a number in Azure Portal, set `ACS_SOURCE_NUMBER` |
| Taxonomy cache refresh failed | realtordr.com API unreachable at startup | Non-blocking; falls back to hardcoded IDs. Check network/firewall. |
| Email not sending | Missing `ACS_EMAIL_*` environment variables | Set `ACS_EMAIL_CONNECTION_STRING`, `ACS_EMAIL_SENDER`, `TRANSCRIPT_EMAIL_RECIPIENTS` |
| System prompt not updating | Azure Storage prompt overrides local file | Upload new prompt to `prompt` container, or delete the blob to use local file |
| Agent speaks Spanish unexpectedly | System prompt language rule not reaching model | Ensure system prompt includes the "Language Rule" section at the top |
