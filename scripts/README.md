# Scripts

This directory contains automation scripts for the Customer Support Agent.

## Directory Structure

```
scripts/
└── bulk_call/                    # Bulk calling automation
    ├── QUICK_START.md           # Quick reference
    ├── README.md                # Complete guide
    ├── bulk_call.py             # ⭐ Main script
    └── phone_numbers.txt        # Phone number list
```

## Available Scripts

### Bulk Calling

**Location:** `bulk_call/`

**Purpose:** Automatically call a list of phone numbers with configurable delays

**Usage:**
```bash
# From project root
python scripts/bulk_call/bulk_call.py
```

**Features:**
- ✅ Sequential calling with delays
- ✅ CSV logging
- ✅ Real-time status updates
- ✅ Error handling
- ✅ Summary statistics

**See:** [bulk_call/README.md](bulk_call/README.md) for complete guide

## Quick Reference

### Bulk Calling
```bash
# Edit phone numbers
vim scripts/bulk_call/phone_numbers.txt

# Run with defaults (120s delay)
python scripts/bulk_call/bulk_call.py

# Run with faster delay
CALL_DELAY_SECONDS=60 python scripts/bulk_call/bulk_call.py
```

### Output Locations

All script outputs go to `call_logs/` in the project root:
- `call_logs/bulk_call_*.csv` - Bulk call logs
- `call_logs/call_events.jsonl` - Detailed call events
- `call_logs/transcript_*.json` - Call transcripts
- `call_logs/test_email_*.html` - Test email previews

## Future Scripts

Potential additions:
- Database migration scripts
- Deployment automation
- Backup/restore utilities
- Performance monitoring tools

---

**Last Updated:** 2026-01-13  
**Scripts:** 1 (Bulk Calling)  
**Location:** All scripts run from project root
