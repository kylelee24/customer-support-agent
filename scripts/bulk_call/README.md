# Bulk Calling Documentation

**Location:** `scripts/bulk_call/`

## Overview

This system allows you to automatically call a list of phone numbers sequentially using the Azure Communication Services integration. It provides comprehensive logging of both call initiation and call events.

## Quick Start

```bash
# From project root
python scripts/bulk_call/bulk_call.py
```

## Components

### 1. Bulk Calling Script (`bulk_call.py`)

A standalone Python script that calls multiple phone numbers from a list with configurable delays between calls.

**Features:**
- ✅ Reads phone numbers from a file
- ✅ Configurable delay between calls
- ✅ CSV logging with timestamps
- ✅ Real-time console output with status emojis
- ✅ Comprehensive error handling
- ✅ Summary statistics at the end

### 2. Enhanced Backend Logging (`src/app/backend/acs.py`)

The ACS backend has been enhanced to log all call events to a structured JSONL file.

**Events Logged:**
- CallInitiated - When a call is first initiated
- CallConnected - When the call is answered
- CallDisconnected - When the call ends (includes duration)
- IncomingCall - When receiving an inbound call
- Other ACS events (transfers, recognition, etc.)

## Setup

### Prerequisites

1. Make sure your app is running:
```bash
cd src/app
python app.py
```

2. Ensure Azure Communication Services is configured with these environment variables:
   - `ACS_SOURCE_NUMBER`
   - `ACS_CONNECTION_STRING`
   - `ACS_CALLBACK_PATH`
   - `ACS_MEDIA_STREAMING_WEBSOCKET_PATH`

### Installation

Install the required Python package for the bulk calling script:

```bash
pip install aiohttp
```

(Note: This is likely already installed if you're running the main app)

## Usage

### Step 1: Create Your Phone Number List

Edit `scripts/bulk_call/phone_numbers.txt` and add your phone numbers (one per line):

```txt
+1234567890
+1987654321
+1555123456
```

**Note:** The script looks for `phone_numbers.txt` in `scripts/bulk_call/` first, then the project root.

**Important:** 
- Include the country code (e.g., +1 for US/Canada)
- One number per line
- Lines starting with `#` are comments and ignored
- Empty lines are ignored

### Step 2: Run the Bulk Calling Script

```bash
python bulk_call.py
```

**With Custom Configuration:**

```bash
# Use a different phone list file
PHONE_LIST_FILE=my_numbers.txt python bulk_call.py

# Change delay between calls (in seconds)
CALL_DELAY_SECONDS=60 python bulk_call.py

# Use a different API endpoint
CALL_API_URL=http://myserver:8080/call python bulk_call.py

# Combine multiple options
PHONE_LIST_FILE=vip_customers.txt CALL_DELAY_SECONDS=45 python bulk_call.py
```

### Step 3: Monitor Progress

The script will show real-time progress in the console:

```
🚀 Starting bulk calling...
📞 Total numbers to call: 3
⏱️  Delay between calls: 30 seconds
============================================================

[1/3] ✅ +1234567890
  Status: success
  Response: Created outbound call

⏳ Waiting 30 seconds before next call...

[2/3] ✅ +1987654321
  Status: success
  Response: Created outbound call

...

============================================================
📊 Summary:
  Total calls: 3
  Successful: 3
  Failed: 0
  Success rate: 100.0%

📋 Full log saved to: call_logs/bulk_call_20260103_143022.csv
```

## Log Files

The system creates two types of log files in the `call_logs/` directory:

### 1. CSV Call Initiation Logs

**File:** `call_logs/bulk_call_YYYYMMDD_HHMMSS.csv`

Created by the bulk calling script, tracks each call attempt:

| Timestamp | Phone Number | Status | Response | Error |
|-----------|-------------|--------|----------|-------|
| 2026-01-03T14:30:22 | +1234567890 | success | Created outbound call | |
| 2026-01-03T14:31:02 | +1987654321 | failed | | HTTP 500 |

**Status Values:**
- `success` - Call was initiated successfully
- `failed` - HTTP error from server
- `timeout` - Request timed out
- `connection_error` - Cannot connect to server
- `error` - Other error occurred

### 2. JSONL Call Events Log

**File:** `call_logs/call_events.jsonl`

Created by the backend, tracks detailed call events (one JSON object per line):

```json
{"timestamp": "2026-01-03T14:30:22.123", "event_type": "CallInitiated", "call_connection_id": "abc123", "data": {"target_number": "+1234567890", "source_number": "+1999888777"}}
{"timestamp": "2026-01-03T14:30:25.456", "event_type": "CallConnected", "call_connection_id": "abc123", "data": {"call_info": {"connected_at": "2026-01-03T14:30:25.456", "status": "connected"}}}
{"timestamp": "2026-01-03T14:32:10.789", "event_type": "CallDisconnected", "call_connection_id": "abc123", "data": {"call_info": {"duration_seconds": 105.333}}}
```

**Key Event Types:**
- `CallInitiated` - Call creation started
- `CallConnected` - Recipient answered the call
- `CallDisconnected` - Call ended (check `duration_seconds` field)
- `IncomingCall` - Received an inbound call
- Others: Transfer events, recognition events, etc.

## Analyzing Call Data

### View Recent Calls

```bash
# View the latest CSV log
cat call_logs/bulk_call_*.csv | tail -n 20

# View all call events
cat call_logs/call_events.jsonl | tail -n 50
```

### Extract Call Durations

```bash
# Find all calls with their durations
grep "CallDisconnected" call_logs/call_events.jsonl | grep -o "duration_seconds[^,}]*"
```

### Count Success Rate

```bash
# Count successful initiations
grep "success" call_logs/bulk_call_*.csv | wc -l

# Count failed initiations
grep "failed\|timeout\|error" call_logs/bulk_call_*.csv | wc -l
```

### Python Analysis Script

```python
import json
import csv
from datetime import datetime

# Analyze call events
with open('call_logs/call_events.jsonl', 'r') as f:
    events = [json.loads(line) for line in f]

# Find calls that connected
connected_calls = [e for e in events if e['event_type'] == 'CallConnected']
print(f"Total connected calls: {len(connected_calls)}")

# Find calls with durations
disconnected_calls = [e for e in events if e['event_type'] == 'CallDisconnected']
durations = [e['data']['call_info'].get('duration_seconds', 0) 
             for e in disconnected_calls 
             if 'duration_seconds' in e['data']['call_info']]

if durations:
    avg_duration = sum(durations) / len(durations)
    print(f"Average call duration: {avg_duration:.1f} seconds")
    print(f"Total talk time: {sum(durations):.1f} seconds")
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CALL_API_URL` | `http://localhost:8765/call` | API endpoint URL |
| `CALL_DELAY_SECONDS` | `30` | Seconds between calls |
| `PHONE_LIST_FILE` | `phone_numbers.txt` | Phone number list file |

### Recommended Delays

- **Testing:** 10-15 seconds
- **Production:** 30-60 seconds
- **Compliance:** Check local laws for auto-dialing regulations

## Troubleshooting

### Common Issues

**1. "Cannot connect to server"**
- Ensure the app is running (`python src/app/app.py`)
- Check if you're using the correct host/port

**2. "Outbound calling is not configured"**
- Verify all ACS environment variables are set
- Check your `.env` file

**3. "File not found: phone_numbers.txt"**
- Create the file in the project root
- Or specify a different file with `PHONE_LIST_FILE`

**4. No call events in `call_events.jsonl`**
- Ensure your ACS callback URL is publicly accessible
- Check Azure Event Grid subscription is configured
- Verify webhook endpoints are registered

### Viewing Real-Time Logs

Monitor the app logs while calling:

```bash
# Terminal 1: Run the app
python src/app/app.py

# Terminal 2: Run bulk calling
python bulk_call.py

# Terminal 3: Watch call events
tail -f call_logs/call_events.jsonl
```

## Best Practices

1. **Test First:** Start with 2-3 test numbers before bulk calling
2. **Monitor Logs:** Keep the app console visible during calling
3. **Respect Delays:** Don't reduce delays too much (spam prevention)
4. **Backup Data:** Archive old log files periodically
5. **Error Handling:** Review failed calls and retry if needed
6. **Compliance:** Ensure you have consent to call all numbers

## Limitations

### What's Logged:
- ✅ Call initiation (success/failure)
- ✅ Call connection status
- ✅ Call duration
- ✅ Timestamps for all events

### What's NOT Logged (Currently):
- ❌ Conversation transcripts
- ❌ Audio recordings
- ❌ Detailed error messages from ACS
- ❌ Real-time call quality metrics

**Note:** Transcript capture requires additional implementation (see Option C in the original discussion).

## Future Enhancements

Potential additions:
- Transcript logging
- Database storage instead of files
- Web dashboard for monitoring
- Retry logic for failed calls
- Scheduling support
- Analytics and reporting

## Support

For issues or questions:
1. Check the log files for error details
2. Verify Azure Communication Services configuration
3. Review the console output from both the app and script

