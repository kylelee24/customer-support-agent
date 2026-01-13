# Testing Call Transcripts Without Phone Calls

This guide shows you how to test the transcript, summary, and email features without making actual phone calls.

## Test Script: `test_transcript.py`

The test script simulates completed call transcripts and runs them through the complete pipeline:
- ✅ Creates realistic call transcripts
- ✅ Generates AI summaries with o4-mini
- ✅ Sends test emails
- ✅ Saves JSON and HTML files

## Quick Start

### 1. List Available Scenarios

```bash
python test_transcript.py --list
```

**Output:**
```
📋 Available Test Scenarios:

  • meeting_scheduled - Full conversation with Zoom meeting booked
  • inquiry_only - Customer asking questions, no meeting scheduled
  • technical_questions - Deep dive on product features
  • short_call - Brief call, wrong number
  • detailed_meeting - Extended conversation with meeting details
```

### 2. Run a Test Scenario

```bash
# Test with a meeting scheduled
python test_transcript.py --scenario meeting_scheduled

# Test with inquiry only
python test_transcript.py --scenario inquiry_only

# Test with technical questions
python test_transcript.py --scenario technical_questions
```

### 3. Use a Custom Conversation

Create a text file with your conversation:

**my_test.txt:**
```
user: Hello, I'm interested in the Bluetooth Hard Hat.
assistant: Great! I'd be happy to tell you about it. Would you like to schedule a demo?
user: Yes, next Monday at 2 PM please.
assistant: Perfect! What's your email?
user: kyle@example.com
```

Then run:
```bash
python test_transcript.py --custom my_test.txt
```

### 4. Specify a Phone Number

```bash
python test_transcript.py --scenario meeting_scheduled --phone +15551234567
```

## What the Test Script Does

### Step-by-Step Process:

```
1. Load environment variables (.env)
   ↓
2. Initialize services (TranscriptManager, CallSummarizer, EmailService)
   ↓
3. Create test call session with metadata
   ↓
4. Inject conversation messages into transcript
   ↓
5. Generate AI summary with o4-mini
   ↓
6. Format HTML email
   ↓
7. Send test email (if configured)
   ↓
8. Save files to call_logs/
```

### Output Files Created:

```
call_logs/
├── test_email_test-20260113-143000.html   # HTML preview of email
├── transcript_test-20260113-143000.json   # JSON transcript
```

## Example Output

```bash
$ python test_transcript.py --scenario meeting_scheduled

================================================================================
🧪 CALL TRANSCRIPT SIMULATOR
================================================================================

📝 Using scenario: meeting_scheduled
💬 Conversation has 13 messages

🔧 Initializing services...
  ✓ Transcript manager initialized
  ✓ Call summarizer initialized
  ✓ Email service initialized (recipients: kyle.a.lee24@gmail.com)

📞 Creating test call session: test-20260113-143000
  ✓ Session created with metadata
  ✓ Phone: +16479699379
  ✓ Duration: 2m 0s

💬 Injecting conversation into transcript...
  ✓ Injected 13 messages

================================================================================
📋 CAPTURED TRANSCRIPT
================================================================================
[timestamps] assistant: Hello! Hi there, this is Jane...
[timestamps] user: Hi Jane! Yes, I'm very interested...
...
================================================================================

📊 Generating AI call summary with o4-mini...
✅ Summary generated successfully!

--------------------------------------------------------------------------------
CALL SUMMARY
--------------------------------------------------------------------------------
## Call Summary
The customer expressed interest in the Bluetooth Hard Hat Add-On for construction
site communication. Successfully scheduled a Zoom demonstration for January 21st
at 2 PM EST. Contact information collected: kyle.a.lee24@gmail.com, 647-969-9379.

## Zoom Meeting Information
| Meeting Date | Meeting Time | Customer Name | Customer Email | Phone |
|--------------|--------------|---------------|----------------|-------|
| January 21, 2026 | 2:00 PM EST | Kyle | kyle.a.lee24@gmail.com | 647-969-9379 |
--------------------------------------------------------------------------------

📧 Formatting HTML email...
  ✓ HTML email formatted

💾 HTML email saved to: call_logs/test_email_test-20260113-143000.html
  (Open in browser to see how the email looks)

📮 Sending test email...
✅ Test email sent successfully to: kyle.a.lee24@gmail.com

================================================================================
✅ TEST COMPLETE
================================================================================

Check your email and the call_logs/ directory for results!
```

## Custom Conversation File Format

Create a text file with this format:

```
# Lines starting with # are comments (ignored)
# Format: speaker: message

user: Hello, I'd like information about your product.
assistant: I'd be happy to help! What would you like to know?
user: How much does it cost?
assistant: Our team can discuss pricing on a Zoom call. Would you like to schedule one?
user: Yes, next Tuesday at 3 PM.
assistant: Perfect! What's your email?
user: customer@example.com
```

**Speaker Names:**
- Use `user` or `assistant`
- Case insensitive
- One message per line

## Environment Variables Needed

The test script uses the same environment variables as the main app:

```bash
# Required for summary generation
AZURE_OPENAI_ENDPOINT=https://cog-xxxxx.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here

# Required for email sending (optional for testing)
ACS_EMAIL_CONNECTION_STRING=endpoint=https://acs-xxxx...
ACS_EMAIL_SENDER=DoNotReply@xxxx.azurecomm.net
TRANSCRIPT_EMAIL_RECIPIENTS=your-email@example.com
```

**Load from .env:**
```bash
source <(azd env get-values)
python test_transcript.py --scenario meeting_scheduled
```

**Or set manually:**
```bash
export AZURE_OPENAI_ENDPOINT="..."
export AZURE_OPENAI_API_KEY="..."
python test_transcript.py --scenario meeting_scheduled
```

## Testing Different Scenarios

### Scenario 1: Meeting Scheduled
**Tests:** Full meeting scheduling flow with contact info extraction

```bash
python test_transcript.py --scenario meeting_scheduled
```

**Expected:** Summary includes meeting table with all details

### Scenario 2: Inquiry Only
**Tests:** Customer asking questions but not scheduling

```bash
python test_transcript.py --scenario inquiry_only
```

**Expected:** Summary notes no meeting was scheduled

### Scenario 3: Technical Questions
**Tests:** Deep technical discussion

```bash
python test_transcript.py --scenario technical_questions
```

**Expected:** Summary highlights technical topics discussed

### Scenario 4: Short Call
**Tests:** Very brief call (wrong number)

```bash
python test_transcript.py --scenario short_call
```

**Expected:** Brief summary, no meeting info

### Scenario 5: Detailed Meeting
**Tests:** Extended conversation with qualifying questions

```bash
python test_transcript.py --scenario detailed_meeting
```

**Expected:** Comprehensive summary with meeting details and customer context

## Verifying Results

### Check Email
Look for email with:
- ✅ Call Information section
- ✅ AI-Generated Call Summary
- ✅ Zoom Meeting table (if applicable)
- ✅ Full conversation transcript

### Check call_logs/ Directory
```bash
ls -la call_logs/test_email_*.html
ls -la call_logs/transcript_test-*.json
```

**Open HTML file in browser:**
```bash
# Linux/WSL
xdg-open call_logs/test_email_test-20260113-143000.html

# Mac
open call_logs/test_email_test-20260113-143000.html

# Windows
start call_logs/test_email_test-20260113-143000.html
```

### Check Console Output
The script prints:
- Transcript text (formatted)
- AI-generated summary
- Zoom meeting table
- Status messages

## Advanced Usage

### Test Multiple Scenarios Quickly

```bash
# Loop through all scenarios
for scenario in meeting_scheduled inquiry_only technical_questions; do
    echo "Testing: $scenario"
    python test_transcript.py --scenario $scenario
    sleep 2
done
```

### Custom Test with Specific Phone

```bash
python test_transcript.py --scenario meeting_scheduled --phone +15551234567
```

### Create Your Own Test Scenarios

Add to `test_transcript.py` in the `SCENARIOS` dictionary:

```python
"my_scenario": [
    ("assistant", "Your opening message..."),
    ("user", "Customer response..."),
    # ... more messages
],
```

## Troubleshooting

### "AZURE_OPENAI_ENDPOINT not set"
**Fix:** Load environment variables first
```bash
source <(azd env get-values)
# or
source .venv/bin/activate && python -c "from dotenv import load_dotenv; load_dotenv()"
```

### "Email service not configured"
**Fix:** This is just a warning. The test will still run and save files, just won't send email.
To enable email, set:
```bash
export ACS_EMAIL_CONNECTION_STRING="..."
export ACS_EMAIL_SENDER="..."
export TRANSCRIPT_EMAIL_RECIPIENTS="..."
```

### "Error generating summary"
**Fix:** Check that:
- Azure OpenAI endpoint is correct
- API key is valid
- o4-mini deployment exists
- API version is 2024-12-01-preview

### "Module not found"
**Fix:** Make sure you're in the project root directory and have dependencies installed:
```bash
pip install -r src/app/requirements.txt
```

## Benefits of Testing This Way

### Speed
- ⚡ Test in seconds vs. minutes for real calls
- ⚡ No need to dial, wait, talk, hang up

### Control
- 🎯 Test specific scenarios easily
- 🎯 Reproduce exact conversations
- 🎯 Test edge cases

### Cost
- 💰 Only pays for summary generation (~$0.00015 per test)
- 💰 No ACS call charges
- 💰 No phone minutes used

### Iteration
- 🔄 Quickly test changes
- 🔄 Try different conversation types
- 🔄 Validate summary accuracy

### Documentation
- 📝 HTML files for visual inspection
- 📝 JSON files for debugging
- 📝 Console output for quick checks

## What This Tests

✅ **Tests:**
- Transcript storage and formatting
- AI summary generation (o4-mini)
- Zoom meeting information extraction
- Email HTML formatting
- Email sending (if configured)
- JSON file creation

❌ **Does NOT Test:**
- Actual audio transcription (Whisper)
- ACS call handling
- WebSocket communication
- Real-time transcript capture

For full end-to-end testing, you still need to make actual phone calls occasionally.

## Recommended Testing Workflow

### Development Cycle:
```
1. Make code changes
   ↓
2. Test with script: python test_transcript.py --scenario meeting_scheduled
   ↓
3. Verify email and HTML output
   ↓
4. If good, deploy: bash ./azd-hooks/deploy.sh app cs-agent
   ↓
5. Make 1-2 real test calls to verify end-to-end
```

This way you can iterate quickly on summary/email formatting without constant phone calls!

---

**Created:** Test script for rapid transcript testing
**Scenarios:** 5 predefined + custom file support
**Speed:** ~5-10 seconds per test
**Cost:** Minimal (only summary generation)
