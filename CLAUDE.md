# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-assisted call center solution using Azure Communication Services (ACS) and OpenAI Realtime API. Users interact with an AI agent through a web interface or phone calls. The system provides real-time voice conversations, call transcription, AI summarization, and email notifications.

## Commands

### Local Development

```bash
# Setup Python environment (one-time)
python -m venv .venv
source .venv/bin/activate
pip install -r src/app/requirements.txt

# Load environment variables from Azure
source <(azd env get-values)
azd env get-values > .env

# Run the application (default: localhost:8765)
python src/app/app.py

# For local development with phone calls, start ngrok tunnel first
ngrok http http://localhost:8765
# Then set ACS_CALLBACK_PATH and ACS_MEDIA_STREAMING_WEBSOCKET_PATH to ngrok URLs
```

### Testing

```bash
# List available test scenarios
python tests/test_transcripts/test_transcript.py --list

# Run a specific test scenario
python tests/test_transcripts/test_transcript.py --scenario meeting_scheduled
```

### Deployment

```bash
# Provision Azure resources
azd auth login
azd up

# Deploy application to Azure Container Apps
source <(azd env get-values | grep AZURE_ENV_NAME)
bash ./azd-hooks/deploy.sh app $AZURE_ENV_NAME

# Docker build
docker build -t customer-support-agent:latest ./src/app/
```

### Bulk Calling

```bash
python scripts/bulk_call/bulk_call.py
```

## Architecture

### Tech Stack

- **Backend:** Python 3.12, aiohttp (async web framework), gunicorn (production)
- **Frontend:** Vanilla HTML/JS/CSS with WebSocket client
- **AI:** Azure OpenAI (GPT-4o Realtime for voice, o4-mini for summarization)
- **Infrastructure:** Bicep (primary IaC), Terraform (recovery stack), Azure Container Apps

### Application Entry Point

`src/app/app.py` — Creates an aiohttp web application with these routes:

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Serves web UI (`static/index.html`) |
| `/realtime` | GET | WebSocket for browser-based voice conversations |
| `/realtime-acs` | GET | WebSocket for ACS phone call audio streams |
| `/call` | POST | Initiate outbound phone calls |
| `/acs` | POST | ACS outbound call webhook handler |
| `/acs/incoming` | POST | ACS inbound call webhook handler |
| `/update-voice` | POST | Change AI voice selection |
| `/source-phone-number` | GET | Get configured phone number |

### Core Backend Modules (`src/app/backend/`)

- **`rtmt.py` — RTMiddleTier**: Central middleware managing the OpenAI Realtime WebSocket protocol. Handles bidirectional message forwarding between clients (browser or ACS) and OpenAI, manages function calling, and captures transcripts during conversations.
- **`acs.py` — AcsCaller**: Manages phone calls via Azure Communication Services. Handles outbound/inbound call lifecycle, media streaming, call event tracking, and coordinates with TranscriptManager/EmailService/CallSummarizer on call completion.
- **`transcript_manager.py` — TranscriptManager**: Session-based transcript tracking with timestamps. Saves transcripts as JSON to `call_logs/`.
- **`call_summarizer.py` — CallSummarizer**: Uses GPT-4o-mini to generate call summaries and extract meeting information from transcripts.
- **`email_service.py` — EmailService**: Sends HTML-formatted transcript emails via ACS Email after calls complete.
- **`tools/rag/ai_search.py`**: RAG integration with Azure AI Search — provides `search_tool` and `report_grounding_tool` for the AI agent's function calling.
- **`azure.py`**: Azure credential management and fetching system prompts from Azure Storage.

### Data Flow

1. Client connects via WebSocket (`/realtime` for browser, `/realtime-acs` for phone)
2. RTMiddleTier opens a parallel WebSocket to OpenAI Realtime API
3. Audio/messages are forwarded bidirectionally between client and OpenAI
4. Function calls (RAG search) are intercepted and executed by RTMiddleTier
5. On call end: transcript is saved, AI summary generated, email sent

### System Prompt

The AI agent's behavior is controlled by `src/app/system_prompt.md`. At startup, the app first tries to fetch `system_prompt.md` from an Azure Storage `prompt` container; if unavailable, it falls back to the local file.

### Infrastructure

- **`infra/`**: Bicep templates for Azure resource provisioning (Container Apps, OpenAI, ACS, AI Search, Storage, Event Grid, monitoring)
- **`infra/recovery/`**: Terraform configuration and CLI scripts for resource cleanup/recreation
- **`azd-hooks/`**: Azure Developer CLI deployment hooks (build Docker image, push to ACR, update Container App)
- **`data/`**: Knowledge base documents (PDFs) indexed into Azure AI Search

### Key Environment Variables

Configuration is loaded from `.env` (locally) or `.azure/<env-name>/.env` (Azure). Critical variables:

- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME`, `AZURE_OPENAI_API_KEY` — LLM connection
- `ACS_CONNECTION_STRING`, `ACS_SOURCE_NUMBER` — Phone call support
- `ACS_CALLBACK_PATH`, `ACS_MEDIA_STREAMING_WEBSOCKET_PATH` — ACS webhook URLs (must be publicly reachable; use ngrok locally)
- `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_INDEX`, `AZURE_SEARCH_API_KEY`, `AZURE_SEARCH_SEMANTIC_CONFIGURATION` — RAG/knowledge base
- `ACS_EMAIL_CONNECTION_STRING`, `ACS_EMAIL_SENDER`, `TRANSCRIPT_EMAIL_RECIPIENTS` — Email transcript delivery
