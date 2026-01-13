# Project Organization

This document describes the organized structure of the Customer Support Agent project.

## Directory Structure

```
customer-support-agent/
├── src/app/                    # Main application code
│   ├── backend/               # Backend services
│   │   ├── acs.py            # Azure Communication Services
│   │   ├── rtmt.py           # Realtime middleware
│   │   ├── transcript_manager.py   # Transcript capture
│   │   ├── email_service.py        # Email delivery
│   │   └── call_summarizer.py      # AI summarization
│   ├── static/               # Frontend assets
│   ├── app.py               # Main app entry point
│   └── requirements.txt     # Python dependencies
│
├── scripts/                   # Automation scripts
│   ├── README.md
│   ├── bulk_call/            # Bulk calling automation
│   │   ├── QUICK_START.md
│   │   ├── README.md
│   │   ├── bulk_call.py     # ⭐ Main script
│   │   └── phone_numbers.txt # Phone number list
│   └── upload_data.sh       # Data upload script
│
├── tests/                     # Testing suite
│   ├── README.md
│   └── test_transcripts/     # Transcript testing
│       ├── QUICK_START.md
│       ├── README.md
│       ├── test_transcript.py    # ⭐ Test script
│       ├── scenarios/
│       │   └── sample_conversation.txt
│       └── docs/             # Testing documentation
│           ├── TESTING_TRANSCRIPTS.md
│           ├── CALL_SUMMARY_FEATURE.md
│           ├── TRANSCRIPT_FEATURE_SUMMARY.md
│           ├── TRANSCRIPT_BEHAVIOR_NOTES.md
│           ├── QUICK_START_TRANSCRIPTS.md
│           └── DEPLOYMENT_FIXES_SUMMARY.md
│
├── call_logs/                 # Output directory (shared)
│   ├── bulk_call_*.csv       # Bulk call logs
│   ├── call_events.jsonl     # Detailed call events
│   ├── transcript_*.json     # Call transcripts
│   └── test_email_*.html     # Test email previews
│
├── azd-hooks/                 # Deployment hooks
├── data/                      # Knowledge base
├── infra/                     # Infrastructure as code
├── .azure/                    # Azure configuration
└── README.md                  # Main project README
```

## Quick Reference

### Running the Application

```bash
# Local development
python src/app/app.py

# Deploy to Azure
bash ./azd-hooks/deploy.sh app cs-agent
```

### Making Bulk Calls

```bash
# Edit phone numbers
vim scripts/bulk_call/phone_numbers.txt

# Run bulk calling
python scripts/bulk_call/bulk_call.py
```

**See:** [scripts/bulk_call/QUICK_START.md](scripts/bulk_call/QUICK_START.md)

### Testing Transcripts

```bash
# List test scenarios
python tests/test_transcripts/test_transcript.py --list

# Run a test
source .venv/bin/activate && source <(azd env get-values)
python tests/test_transcripts/test_transcript.py --scenario meeting_scheduled
```

**See:** [tests/test_transcripts/QUICK_START.md](tests/test_transcripts/QUICK_START.md)

## Documentation Structure

### Main Documentation
- **[README.md](README.md)** - Project overview and setup
- **PROJECT_ORGANIZATION.md** - This file

### Script Documentation
- **[scripts/README.md](scripts/README.md)** - Scripts overview
- **[scripts/bulk_call/README.md](scripts/bulk_call/README.md)** - Bulk calling guide
- **[scripts/bulk_call/QUICK_START.md](scripts/bulk_call/QUICK_START.md)** - Quick reference

### Testing Documentation
- **[tests/README.md](tests/README.md)** - Testing overview
- **[tests/test_transcripts/README.md](tests/test_transcripts/README.md)** - Transcript testing guide
- **[tests/test_transcripts/QUICK_START.md](tests/test_transcripts/QUICK_START.md)** - Quick reference
- **[tests/test_transcripts/docs/](tests/test_transcripts/docs/)** - Detailed feature docs

## Output Directories

### call_logs/
**Purpose:** All call-related outputs (shared by scripts and tests)

**Contents:**
- CSV logs from bulk calling
- JSONL event logs from backend
- JSON transcript files
- HTML email previews from tests

**Location:** Project root (not moved to maintain consistency)

### .azure/
**Purpose:** Azure deployment configuration

**Contents:**
- Environment-specific configurations
- Environment variables

## File Organization Principles

### Scripts (`scripts/`)
- **Purpose:** Automation and utility scripts
- **Run from:** Project root
- **Output to:** `call_logs/` in project root
- **Self-contained:** Each script has its own subdirectory with docs

### Tests (`tests/`)
- **Purpose:** Testing and validation tools
- **Run from:** Project root
- **Output to:** `call_logs/` in project root (shared with production)
- **Isolated:** Test scenarios and docs in subdirectories

### Application (`src/app/`)
- **Purpose:** Main application code
- **Run from:** Project root or `src/app/` directory
- **Production:** Deployed to Azure Container Apps

## Common Commands

### Development
```bash
# Install dependencies
pip install -r src/app/requirements.txt

# Run locally
python src/app/app.py
```

### Scripts
```bash
# Bulk calling
python scripts/bulk_call/bulk_call.py

# Custom phone list
PHONE_LIST_FILE=my_list.txt python scripts/bulk_call/bulk_call.py
```

### Testing
```bash
# Setup
source .venv/bin/activate && source <(azd env get-values)

# Test transcripts
python tests/test_transcripts/test_transcript.py --scenario meeting_scheduled
```

### Deployment
```bash
# Deploy to Azure
bash ./azd-hooks/deploy.sh app cs-agent

# Check status
az containerapp show --name callcenterapp --resource-group rg-cs-agent
```

## Benefits of Organization

### Clear Separation
- ✅ Scripts vs Tests vs Application code clearly separated
- ✅ Each has its own README and documentation
- ✅ Easy to find what you need

### Consistent Structure
- ✅ All subdirectories follow similar patterns
- ✅ QUICK_START.md for quick reference
- ✅ README.md for complete guides
- ✅ docs/ for detailed documentation

### Maintainability
- ✅ Easy to add new scripts or tests
- ✅ Documentation lives with the code
- ✅ Clear ownership of files

### Shared Resources
- ✅ `call_logs/` shared by all components
- ✅ Virtual environment shared
- ✅ Environment variables consistent

## Navigation

**Need to:**
- **Make bulk calls?** → `scripts/bulk_call/`
- **Test transcripts?** → `tests/test_transcripts/`
- **Modify backend?** → `src/app/backend/`
- **Deploy?** → `azd-hooks/deploy.sh`
- **Check logs?** → `call_logs/`

---

**Last Updated:** 2026-01-13  
**Organization:** Complete  
**Status:** Production Ready
