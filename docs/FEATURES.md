# Features

## Implemented

| # | Feature | Description | Date |
|---|---------|-------------|------|
| 1 | **AI Voice Agent (Mackenzie)** | Real-time voice conversations via OpenAI gpt-4o-realtime. Handles greetings, FAQ, lead qualification, and consultation scheduling. | Pre-fork |
| 2 | **Phone Call Support** | Inbound and outbound PSTN calls via Azure Communication Services. Media streaming over WebSocket. | Pre-fork |
| 3 | **Web Browser Voice Chat** | Browser-based voice conversations via WebSocket at `/realtime`. No phone required. | Pre-fork |
| 4 | **RAG Knowledge Base Search** | `search` tool queries Azure AI Search with hybrid semantic + vector search over indexed PDF documents. | Pre-fork |
| 5 | **Source Grounding** | `report_grounding` tool cites knowledge base sources in the web UI. | Pre-fork |
| 6 | **Custom System Prompts** | Multiple archived prompts (Santorini, Gold Standard, EVITAVONNI, MacHenry Realtor). Azure Storage override at runtime. | Jan 2025 |
| 7 | **Bulk Calling Automation** | Outbound calls to a list of phone numbers with logging and error handling (`scripts/bulk_call/`). | Jan 2025 |
| 8 | **Call Transcription** | Automatic transcript capture during calls. Saves JSON files to `call_logs/` with timestamps and speaker labels. | Jan 2025 |
| 9 | **AI Call Summarization** | o4-mini generates post-call summaries with lead qualification table and consultation details extraction. | Jan 2025 |
| 10 | **Email Transcript Delivery** | HTML-formatted transcript + AI summary emailed to the team via ACS Email after each call ends. | Jan 2025 |
| 11 | **Frontend Rebranding** | Web UI styled to match realtordr.com (colors, logo, layout). | Feb 2025 |
| 12 | **Real-Time Property Search** | `property_search` tool queries the WordPress REST API at realtordr.com. Parses caller intent into API filters (type, city, status). Results summarized by o4-mini for voice. | Feb 2025 |
| 13 | **Property ID Lookup** | Direct lookup by ID (`55069`, `rdr-55069`, `property 55069`) via `GET /properties/{id}`. | Feb 2025 |
| 14 | **Taxonomy Cache** | Fetches WordPress taxonomy terms (property types, cities, statuses) at startup. Falls back to hardcoded IDs on failure. | Feb 2025 |
| 15 | **English-Default Language** | System prompt enforces English by default; switches to Spanish only if the caller initiates. | Feb 2025 |
| 16 | **Simplified Deploy Script** | One-command deploy (`scripts/deploy.sh`) — ACR build + container app update. | Feb 2025 |
| 17 | **Azure Recovery Stack** | Terraform + CLI scripts for resource cleanup and recreation (`infra/recovery/`). | Jan 2025 |
| 18 | **Auto Hang-Up (end_call)** | `end_call` tool lets the AI agent programmatically disconnect after saying goodbye. Triggers ACS `hang_up` for phone calls or closes the WebSocket for browser sessions. | Feb 2025 |

---

## Recommended

New function-calling tools and integrations to enhance Mackenzie's capabilities. Each recommendation includes effort estimate and priority.

### Tools — Caller Communication

| # | Feature | Description | Priority | Effort |  Status | Implemented |
|---|---------|-------------|----------|--------|---------|-------------|
| R1 | **Email Property Details to Caller** | New `send_property_email` tool. When a caller provides their email, Mackenzie can send them a formatted email with property details, photos, and listing links from the search results. Uses the existing `EmailService` and ACS Email infrastructure. | High | Small | Pending | — |
| R2 | **SMS Follow-Up** | New `send_sms` tool. Send the caller a text message via ACS SMS with property links, contact info, or consultation confirmation. ACS already supports SMS — just needs a new tool. | High | Small | Pending | — |

### Tools — Scheduling

| # | Feature | Description | Priority | Effort | Status | Implemented |
|---|---------|-------------|----------|--------|--------|-------------|
| R3 | **Calendar Booking** | New `book_consultation` tool. Actually create calendar events (Google Calendar or Microsoft 365) when Mackenzie schedules a consultation, instead of just verbally confirming. Send calendar invite to the caller's email. | High | Medium | Pending | — |

### Tools — Information & Calculators

| # | Feature | Description | Priority | Effort | Status | Implemented |
|---|---------|-------------|----------|--------|--------|-------------|
| R4 | **Mortgage Calculator** | New `mortgage_calculator` tool. Estimate monthly payments given price, down payment, rate, and term. Useful for callers exploring affordability. No external API needed — pure math. | Medium | Small | Pending | — |
| R5 | **Currency Converter** | New `convert_currency` tool. Convert property prices between USD, CAD, EUR, GBP, and DOP using a free exchange rate API (e.g., exchangerate-api.com). Helpful for international buyers. | Low | Small | Pending | — |
| R6 | **Area/Neighborhood Guide** | New `area_info` tool. Return curated info about DR neighborhoods (Cabarete, Sosua, Puerto Plata, etc.) — lifestyle, amenities, average prices, distance to airport. Could be a static JSON file or RAG-indexed content. | Low | Small | Pending | — |

### MCP Servers & External Integrations

| # | Feature | Description | Priority | Effort | Status | Implemented |
|---|---------|-------------|----------|--------|--------|-------------|
| R7 | **Calendly / Cal.com MCP** | Use a scheduling MCP server to check real-time availability and book consultations directly. Eliminates double-booking and manual follow-up. | Medium | Medium | Pending | — |

### Platform Enhancements

| # | Feature | Description | Priority | Effort | Status | Implemented |
|---|---------|-------------|----------|--------|--------|-------------|
| R8 | **Call Recording & Playback** | Store full audio recordings (ACS supports this natively) alongside transcripts. Enable playback from the web UI or email links. | Low | Medium | Pending | — |
| R9 | **Caller ID & Repeat Caller Recognition** | Match inbound phone numbers against previous call logs. If a repeat caller, give Mackenzie context: "Welcome back! Last time you were interested in villas in Cabarete." | High | Medium | Pending | — |
| R10 | **Real-Time Dashboard** | Web dashboard showing active calls, recent transcripts, lead pipeline, and property search analytics. | Low | Large | Pending | — |
| R11 | **Voicemail & Callback Queue** | When calls disconnect unexpectedly or the caller requests a callback, queue a follow-up task for the team with caller details and conversation context. | Medium | Medium | Pending | — |
