# Call Transcript Recording and Email Feature

## Overview

This feature automatically records conversation transcripts from all calls, outputs them to application logs, and emails HTML-formatted transcripts to specified recipients after each call completes.

## What Was Implemented

### 1. New Components

#### **TranscriptManager** (`backend/transcript_manager.py`)
- Manages conversation transcripts for call sessions
- Captures user and assistant messages in real-time
- Formats transcripts as plain text and HTML
- Saves transcripts to JSON files in `call_logs/` directory
- Associates transcripts with call metadata (phone numbers, duration, timestamps)

#### **EmailService** (`backend/email_service.py`)
- Handles email delivery via Azure Communication Services Email
- Sends HTML-formatted emails with beautiful styling
- Supports configurable recipient lists
- Includes error handling and detailed logging

### 2. Modified Components

#### **RTMiddleTier** (`backend/rtmt.py`)
- Added transcript capture from OpenAI Realtime API messages
- Tracks conversation items (both user input and assistant responses)
- Associates WebSocket connections with session IDs
- Automatically cleans up sessions when connections close

#### **AcsCaller** (`backend/acs.py`)
- Integrated with TranscriptManager and EmailService
- Updates transcript metadata throughout call lifecycle
- Triggers email sending when calls disconnect
- Logs formatted transcripts to console

#### **app.py**
- Initializes TranscriptManager and EmailService on startup
- Wires up services to RTMiddleTier and AcsCaller
- Sets logging level to INFO to see transcript output
- Configures transcript sessions for ACS calls

### 3. Updated Files

- `src/app/requirements.txt` - Added `azure-communication-email==1.1.0`
- `README.md` - Added documentation for email configuration

## Configuration

### Required Environment Variables

Add these to your `.env` file or `.azure/xxx/.env` file:

```bash
# Email configuration for transcript delivery
ACS_EMAIL_CONNECTION_STRING=endpoint=https://acs-xxxx.communication.azure.com/;accesskey=xxxxx
ACS_EMAIL_SENDER=DoNotReply@xxxxxxxx.azurecomm.net
TRANSCRIPT_EMAIL_RECIPIENTS=kyle.a.lee24@gmail.com
```

### Setting Up Azure Communication Services Email

1. **Navigate to your ACS resource in Azure Portal**
2. **Go to Email > Domains**
   - Use the free Azure-managed domain, or
   - Connect your custom domain (requires DNS verification)
3. **Note the sender address**
   - Free domain: `DoNotReply@xxxxxxxx.azurecomm.net`
   - Custom domain: Your configured address
4. **Get your connection string**
   - Go to Keys in your ACS resource
   - Copy the connection string (same as `ACS_CONNECTION_STRING`)

### Multiple Recipients

To send transcripts to multiple email addresses:

```bash
TRANSCRIPT_EMAIL_RECIPIENTS=user1@example.com,user2@example.com,user3@example.com
```

## How It Works

### Transcript Flow

```
1. Call Initiated
   ↓
2. RTMiddleTier creates transcript session
   ↓
3. Conversation messages captured in real-time
   - User speech → "user" entries
   - AI responses → "assistant" entries
   ↓
4. Call Disconnects
   ↓
5. Transcript formatted as HTML and plain text
   ↓
6. Transcript logged to console
   ↓
7. Email sent via ACS
   ↓
8. Transcript saved to call_logs/transcript_*.json
```

### What Gets Captured

- **User Input**: Speech converted to text by OpenAI
- **Assistant Responses**: AI-generated text responses
- **Timestamps**: Each message includes ISO 8601 timestamp
- **Call Metadata**: Phone numbers, duration, connection times

### Email Format

The HTML email includes:

- **Header**: Professional branded header
- **Call Information Section**:
  - Phone number (target and source)
  - Call start time
  - Connection time
  - End time
  - Duration (minutes and seconds)
  - Total message count

- **Conversation Section**:
  - Each message with speaker icon (👤 Customer, 🤖 AI Assistant)
  - Color-coded (green for user, blue for assistant)
  - Timestamps for each message
  - Clean, readable formatting

- **Footer**: Timestamp of report generation

## Application Logs

Transcripts are logged to the console in real-time:

```
💬 [user]: Hello, I'd like to know more about the Bluetooth Hard Hat
💬 [assistant]: Hi! I'd be happy to tell you about our patented Bluetooth Hard Hat Add-On...
```

When a call ends, a full formatted transcript is printed:

```
================================================================================
📋 CALL TRANSCRIPT - +16479699379 (2m 34s)
================================================================================
[2026-01-12T13:45:21.123Z] user: Hello, I'd like to know more...
[2026-01-12T13:45:23.456Z] assistant: Hi! I'd be happy to tell you...
================================================================================
```

## Files Generated

### Call Logs Directory Structure

```
call_logs/
├── call_events.jsonl              # All call events (existing)
├── bulk_call_*.csv                # Bulk call logs (existing)
└── transcript_<callId>_*.json     # NEW: Individual transcripts
```

### Transcript JSON Format

```json
{
  "session_id": "call-connection-id",
  "metadata": {
    "target_number": "+16479699379",
    "source_number": "+18005551234",
    "initiated_at": "2026-01-12T13:45:00.000Z",
    "connected_at": "2026-01-12T13:45:10.000Z",
    "disconnected_at": "2026-01-12T13:47:44.000Z",
    "duration_seconds": 154,
    "status": "disconnected"
  },
  "entries": [
    {
      "speaker": "user",
      "text": "Hello, I'd like to know more about the Bluetooth Hard Hat",
      "timestamp": "2026-01-12T13:45:21.123Z"
    },
    {
      "speaker": "assistant",
      "text": "Hi! I'd be happy to tell you about our patented Bluetooth Hard Hat Add-On...",
      "timestamp": "2026-01-12T13:45:23.456Z"
    }
  ],
  "saved_at": "2026-01-12T13:47:45.000Z"
}
```

## Testing the Feature

### 1. Install Dependencies

```bash
pip install -r src/app/requirements.txt
```

### 2. Configure Environment Variables

```bash
# Add to .env file
export ACS_EMAIL_CONNECTION_STRING="<your-connection-string>"
export ACS_EMAIL_SENDER="DoNotReply@<your-domain>.azurecomm.net"
export TRANSCRIPT_EMAIL_RECIPIENTS="kyle.a.lee24@gmail.com"
```

### 3. Run the Application

```bash
python src/app/app.py
```

### 4. Make a Test Call

```bash
python bulk_call.py
```

### 5. Verify Results

- **Console**: Check for transcript logs
- **Email**: Check kyle.a.lee24@gmail.com inbox
- **Files**: Check `call_logs/` directory for transcript JSON files

## Troubleshooting

### Email Not Sending

**Check:**
1. `ACS_EMAIL_CONNECTION_STRING` is correct
2. `ACS_EMAIL_SENDER` is a verified sender in your ACS Email domain
3. Email domain is properly configured in Azure Portal
4. Recipient email address is valid

**Look for logs:**
```
⚠️ Email service not configured
❌ Failed to send email: <error message>
```

### Transcripts Not Captured

**Check:**
1. Application logs show transcript initialization:
   ```
   ✅ Transcript manager initialized
   ```
2. Calls are connecting successfully
3. WebSocket connections are established

**Look for logs:**
```
📝 Created transcript session: <call-id>
💬 [user]: <message>
💬 [assistant]: <message>
```

### Empty Transcripts

**Possible causes:**
1. Call disconnected before conversation started
2. Audio streaming issues
3. OpenAI API not returning transcripts

**Check logs for:**
```
✅ Closed transcript session: <call-id> (0 entries)
```

## Future Enhancements (Optional)

- [ ] Add transcript search functionality
- [ ] Create daily/weekly summary emails
- [ ] Add sentiment analysis to transcripts
- [ ] Export transcripts to external CRM systems
- [ ] Add transcript analytics dashboard
- [ ] Support for multiple languages
- [ ] Custom email templates
- [ ] Scheduled transcript reports

## Support

If you encounter issues:
1. Check application logs for error messages
2. Verify all environment variables are set correctly
3. Ensure Azure Communication Services Email is properly configured
4. Test email sending separately using Azure Portal

## Notes

- Transcripts are stored in memory during active calls
- HTML emails are mobile-responsive
- Plain text fallback included for email clients that don't support HTML
- All timestamps use ISO 8601 format
- Logging level changed from WARNING to INFO to show transcripts
