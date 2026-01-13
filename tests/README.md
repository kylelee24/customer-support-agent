# Testing Suite

This directory contains all testing tools and documentation for the Customer Support Agent.

## Structure

```
tests/
└── test_transcripts/          # Call transcript testing suite
    ├── README.md              # Testing guide
    ├── test_transcript.py     # Main test script
    ├── scenarios/             # Test conversation scenarios
    │   └── sample_conversation.txt
    └── docs/                  # Testing documentation
        ├── TESTING_TRANSCRIPTS.md
        ├── CALL_SUMMARY_FEATURE.md
        ├── TRANSCRIPT_FEATURE_SUMMARY.md
        ├── TRANSCRIPT_BEHAVIOR_NOTES.md
        ├── QUICK_START_TRANSCRIPTS.md
        └── DEPLOYMENT_FIXES_SUMMARY.md
```

## Test Suites

### Call Transcript Testing

**Location:** `test_transcripts/`

**Purpose:** Test transcript capture, AI summarization, and email delivery without making actual phone calls

**Usage:**
```bash
python tests/test_transcripts/test_transcript.py --scenario meeting_scheduled
```

**See:** [test_transcripts/README.md](test_transcripts/README.md) for complete guide

## Running Tests

### Prerequisites

```bash
# Activate virtual environment
source .venv/bin/activate

# Load environment variables
source <(azd env get-values)
```

### Quick Test

```bash
# List available tests
python tests/test_transcripts/test_transcript.py --list

# Run a scenario
python tests/test_transcripts/test_transcript.py --scenario meeting_scheduled
```

### Results

Test outputs are saved to:
- `call_logs/test_email_*.html` - Email previews
- `call_logs/transcript_test-*.json` - Transcript data

## Documentation

All testing documentation is organized under `test_transcripts/docs/`:

- **Setup & Usage**: Start with [TESTING_TRANSCRIPTS.md](test_transcripts/docs/TESTING_TRANSCRIPTS.md)
- **Feature Details**: See [CALL_SUMMARY_FEATURE.md](test_transcripts/docs/CALL_SUMMARY_FEATURE.md)
- **Technical Overview**: See [TRANSCRIPT_FEATURE_SUMMARY.md](test_transcripts/docs/TRANSCRIPT_FEATURE_SUMMARY.md)

## Future Test Suites

Potential additions:
- Integration tests for ACS calling
- End-to-end WebSocket tests
- Performance/load tests
- API endpoint tests

---

**Last Updated:** 2026-01-13  
**Test Framework:** Custom Python scripts  
**Coverage:** Transcript pipeline (capture → summary → email)
