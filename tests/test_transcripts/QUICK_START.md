# Quick Start - Testing Call Transcripts

## TL;DR

Test the transcript feature without making phone calls:

```bash
cd /home/kyle/workspace/customer-support-agent
source .venv/bin/activate
source <(azd env get-values)

# Run a test
python tests/test_transcripts/test_transcript.py --scenario meeting_scheduled

# View the HTML email
xdg-open call_logs/test_email_test-*.html
```

## Available Commands

```bash
# List scenarios
python tests/test_transcripts/test_transcript.py --list

# Run predefined scenarios
python tests/test_transcripts/test_transcript.py --scenario meeting_scheduled
python tests/test_transcripts/test_transcript.py --scenario inquiry_only
python tests/test_transcripts/test_transcript.py --scenario technical_questions

# Use custom conversation
python tests/test_transcripts/test_transcript.py --custom tests/test_transcripts/scenarios/sample_conversation.txt

# Specify phone number
python tests/test_transcripts/test_transcript.py --scenario meeting_scheduled --phone +15551234567
```

## What You Get

✅ **Console Output**: Full transcript + AI summary  
✅ **HTML File**: `call_logs/test_email_*.html` (preview of email)  
✅ **JSON File**: `call_logs/transcript_test-*.json` (raw data)  
✅ **Email**: Sent to your configured address (if credentials set)

## Example Output

```
📊 AI-Generated Call Summary
Kyle contacted EVITAVONNI to schedule a Bluetooth Hard Hat demo...

🗓️ Scheduled Meeting
| Date          | Time       | Name | Email              | Phone        |
|---------------|------------|------|--------------------|--------------|
| Jan 21, 2026  | 3:00 PM EST| Kyle | kyle.a.lee24@...   | 647-969-9379 |

💬 Full Conversation
[All messages with timestamps]
```

## Adding Your Own Scenarios

Edit `tests/test_transcripts/test_transcript.py` and add to the `SCENARIOS` dictionary:

```python
"my_scenario": [
    ("assistant", "Hello!"),
    ("user", "Hi there!"),
    # ... more messages
],
```

## Files & Docs

- **Main Script**: `tests/test_transcripts/test_transcript.py`
- **Scenarios**: `tests/test_transcripts/scenarios/`
- **Documentation**: `tests/test_transcripts/docs/`
- **Output**: `call_logs/` (project root)

## Full Documentation

See [README.md](README.md) for complete details.
