# Call Transcript Testing Suite

This directory contains tools for testing the call transcript, summary, and email features without making actual phone calls.

## Directory Structure

```
tests/test_transcripts/
├── README.md                    # This file
├── test_transcript.py          # Main test script
├── scenarios/
│   └── sample_conversation.txt # Example custom conversation
└── docs/
    ├── TESTING_TRANSCRIPTS.md         # Complete testing guide
    ├── CALL_SUMMARY_FEATURE.md        # AI summary feature docs
    ├── TRANSCRIPT_FEATURE_SUMMARY.md  # Complete technical docs
    ├── TRANSCRIPT_BEHAVIOR_NOTES.md   # Known limitations & tips
    ├── QUICK_START_TRANSCRIPTS.md     # Quick setup guide
    └── DEPLOYMENT_FIXES_SUMMARY.md    # Deployment fixes log
```

## Quick Start

### 1. List Available Test Scenarios

```bash
python tests/test_transcripts/test_transcript.py --list
```

### 2. Run a Test

```bash
# Activate environment
source .venv/bin/activate
source <(azd env get-values)

# Run test with predefined scenario
python tests/test_transcripts/test_transcript.py --scenario meeting_scheduled

# Or use a custom conversation
python tests/test_transcripts/test_transcript.py --custom tests/test_transcripts/scenarios/sample_conversation.txt
```

### 3. View Results

**HTML Email Preview:**
```bash
# Open most recent test email in browser
xdg-open call_logs/test_email_test-*.html
```

**Check JSON Output:**
```bash
cat call_logs/transcript_test-*.json | jq .
```

## Available Scenarios

- **`meeting_scheduled`** - Full meeting booking with contact details (13 messages)
- **`inquiry_only`** - Questions but no meeting scheduled (11 messages)
- **`technical_questions`** - Deep technical discussion (13 messages)
- **`short_call`** - Brief wrong number call (4 messages)
- **`detailed_meeting`** - Extended conversation with context (17 messages)

## What Gets Tested

✅ **Transcript Storage** - Creates realistic conversation transcripts  
✅ **AI Summary Generation** - Uses o4-mini to summarize calls  
✅ **Meeting Extraction** - Extracts Zoom meeting details into tables  
✅ **Email Formatting** - Generates HTML emails with summaries  
✅ **Email Sending** - Sends test emails (if configured)  
✅ **File Creation** - Saves JSON and HTML files

❌ **Does NOT Test:**
- Actual audio transcription (Whisper)
- ACS call handling
- WebSocket communication
- Real-time capture

## Output Files

All test outputs go to the project root `call_logs/` directory:
- `test_email_test-*.html` - HTML email previews
- `transcript_test-*.json` - Complete transcript data

## Creating Custom Scenarios

### Method 1: Add to test_transcript.py

Edit the `SCENARIOS` dictionary:
```python
"my_scenario": [
    ("assistant", "Your opening message..."),
    ("user", "Customer response..."),
    # ... more messages
],
```

### Method 2: Create a Custom File

Create a file in `scenarios/` directory:

**Format:**
```
# Lines starting with # are comments
user: Hello, I'm interested in the product
assistant: Great! I'd be happy to help...
user: Can we schedule a meeting?
assistant: Of course! What time works for you?
```

Then run:
```bash
python tests/test_transcripts/test_transcript.py --custom tests/test_transcripts/scenarios/my_test.txt
```

## Documentation

All documentation is in the `docs/` subdirectory:

- **[TESTING_TRANSCRIPTS.md](docs/TESTING_TRANSCRIPTS.md)** - Complete usage guide
- **[CALL_SUMMARY_FEATURE.md](docs/CALL_SUMMARY_FEATURE.md)** - AI summary feature details
- **[TRANSCRIPT_FEATURE_SUMMARY.md](docs/TRANSCRIPT_FEATURE_SUMMARY.md)** - Technical overview
- **[TRANSCRIPT_BEHAVIOR_NOTES.md](docs/TRANSCRIPT_BEHAVIOR_NOTES.md)** - Known limitations
- **[QUICK_START_TRANSCRIPTS.md](docs/QUICK_START_TRANSCRIPTS.md)** - Setup guide
- **[DEPLOYMENT_FIXES_SUMMARY.md](docs/DEPLOYMENT_FIXES_SUMMARY.md)** - Deployment history

## Development Workflow

Recommended workflow for developing transcript features:

```bash
# 1. Make code changes to backend files
vim src/app/backend/transcript_manager.py

# 2. Test locally with script (fast iteration)
source .venv/bin/activate && source <(azd env get-values)
python tests/test_transcripts/test_transcript.py --scenario meeting_scheduled

# 3. Review HTML output
xdg-open call_logs/test_email_test-*.html

# 4. Deploy when satisfied
bash ./azd-hooks/deploy.sh app cs-agent

# 5. Make 1-2 real test calls to verify end-to-end
python bulk_call.py
```

This approach lets you iterate quickly without waiting for deployments or making phone calls every time!

## Requirements

The test script requires:
- Python virtual environment activated
- Azure OpenAI credentials configured
- Email service configured (optional - tests work without it)

**Environment Variables:**
```bash
AZURE_OPENAI_ENDPOINT=https://cog-xxxxx.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here

# Optional for email testing
ACS_EMAIL_CONNECTION_STRING=...
ACS_EMAIL_SENDER=...
TRANSCRIPT_EMAIL_RECIPIENTS=...
```

## Troubleshooting

### Import Errors
**Fix:** Ensure you're running from project root and virtual environment is activated

### "No module named 'azure.communication.email'"
**Fix:** Install dependencies
```bash
pip install -r src/app/requirements.txt
```

### "AZURE_OPENAI_ENDPOINT not set"
**Fix:** Load environment variables
```bash
source <(azd env get-values)
```

### Email Not Sending
**Expected:** Tests skip email sending if credentials aren't configured. This is fine for local testing - you'll still get the HTML file to preview.

## Benefits

- ⚡ **Fast**: Test in seconds vs minutes for real calls
- 💰 **Cost-effective**: Only pays for summary generation (~$0.0002 per test)
- 🎯 **Reproducible**: Same test every time
- 🔄 **Iterative**: Quickly test changes
- 📝 **Documented**: Multiple realistic scenarios included

---

**Related Files:**
- Main app: `src/app/app.py`
- Backend: `src/app/backend/`
- Production logs: `call_logs/` (shared with test outputs)
