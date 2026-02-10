# Coding & Project Standards

## Python Style

- **Runtime**: Python 3.12
- **Async**: All I/O operations use `async`/`await`. The app runs on `aiohttp` with `gunicorn` in production.
- **Logging**: Use the shared logger: `logger = logging.getLogger("voicerag")`
- **Type hints**: Use standard library types (`dict`, `list`, `Optional`) rather than `typing.Dict`, `typing.List`.
- **Imports**: Standard library first, then third-party, then local (`backend.*`). No relative imports.
- **No classes where functions suffice**: Tools use factory functions (not class inheritance). Only use classes when managing state (e.g., `TranscriptManager`, `CallSummarizer`).

## Adding a New Function-Calling Tool

Follow the pattern established by `ai_search.py` and `property_search.py`:

### 1. Create the tool module

Place it under `src/app/backend/tools/<domain>/`. Example: `src/app/backend/tools/myservice/my_tool.py`

```python
from backend.tools.tools import Tool, ToolResult, ToolResultDirection

# 1. Define the OpenAI function schema
_my_tool_schema = {
    "type": "function",
    "name": "my_tool",
    "description": "What this tool does — be specific, the AI model reads this.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "What the parameter represents"
            }
        },
        "required": ["query"],
        "additionalProperties": False
    }
}

# 2. Implement the async handler
async def _my_tool(args: Any) -> ToolResult:
    query = args.get("query", "")
    # ... do work ...
    return ToolResult(result_text, ToolResultDirection.TO_SERVER)

# 3. Export a factory function
def my_tool(config_param) -> Tool:
    return Tool(
        schema=_my_tool_schema,
        target=lambda args: _my_tool(args)
    )
```

### 2. Register in `app.py`

```python
from backend.tools.myservice.my_tool import my_tool

# In create_app(), after other tool registrations:
rtmt.tools["my_tool"] = my_tool(config_param)
```

### 3. Update the system prompt

Add a section in `src/app/system_prompt.md` telling the AI when and how to use the tool.

### Tool Result Directions

| Direction | Behavior |
|-----------|----------|
| `TO_SERVER` | Result is sent back to OpenAI as function output — the AI reads it and responds to the caller |
| `TO_CLIENT` | Result is sent to the web client as a special message (not available for phone calls) |

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for |
|--------|---------|
| `feat:` | New features or capabilities |
| `fix:` | Bug fixes |
| `docs:` | Documentation changes |
| `refactor:` | Code restructuring without behavior change |
| `style:` | UI/formatting changes |
| `chore:` | Maintenance tasks (dependencies, configs) |

Examples from this repo:
```
feat: add real-time property search tool and update call summarizer
fix: broken transcript ai summary
docs: add CLAUDE.md with project guidance for Claude Code
style: update index.html and style.css for improved aesthetics
```

Keep the subject line under ~72 characters. Use the body for details when needed.

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Upstream base from Azure-Samples fork |
| `customize` | MacHenry Realtor customizations (active development branch) |

All feature work goes on `customize`. The `main` branch is kept as a reference point for the original fork.

## System Prompt Conventions

The system prompt at `src/app/system_prompt.md` follows this structure:

1. **Identity** — who the AI is (name, company, role)
2. **Language rule** — default English, switch to Spanish only if caller initiates
3. **Goals** — numbered list of objectives
4. **Company info** — contact details, hours, escalation
5. **FAQ** — common questions with answers
6. **Tool instructions** — how to use each function-calling tool
7. **Call guidelines** — greeting, qualifying, scheduling, handling unknowns
8. **Conversation boundaries** — what to discuss, what to redirect
9. **Tone & style** — personality guidelines
10. **Closing scripts** — how to end calls

The prompt can be overridden at runtime by uploading `system_prompt.md` to the Azure Storage `prompt` container — the app checks there first before falling back to the local file.

## File Organization

| Path | What goes here |
|------|---------------|
| `src/app/backend/` | Core backend modules (stateful services) |
| `src/app/backend/tools/<domain>/` | Function-calling tools, grouped by domain |
| `src/app/static/` | Frontend files (HTML, JS, CSS, images) |
| `src/app/system_prompt*.md` | System prompts (active + archived) |
| `scripts/` | Automation scripts (deploy, bulk call, data upload) |
| `tests/` | Test suites and test data |
| `infra/` | Bicep templates for Azure provisioning |
| `infra/recovery/` | Terraform + CLI for disaster recovery |
| `data/` | Knowledge base documents (PDFs indexed into AI Search) |
| `call_logs/` | Runtime output — transcripts, email previews, call logs |
| `docs/` | Project documentation |

## Error Handling in Voice Tools

Since tool results are spoken aloud to callers, errors must return **friendly, natural language**:

```python
# Good — caller hears a helpful message
return ToolResult(
    "I wasn't able to find any listings matching that criteria. "
    "You might want to try broadening your search.",
    ToolResultDirection.TO_SERVER
)

# Bad — caller hears a stack trace
raise Exception("API returned 403")
```

Always wrap external API calls in try/except and return a conversational fallback. Log the actual error with `logger.error()` for debugging.
