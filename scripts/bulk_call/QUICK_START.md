# Quick Start - Bulk Calling

## TL;DR

Make automated calls to a list of phone numbers:

```bash
# Edit phone numbers
vim scripts/bulk_call/phone_numbers.txt

# Run bulk calling
python scripts/bulk_call/bulk_call.py
```

## Setup Phone Numbers

Edit `scripts/bulk_call/phone_numbers.txt`:

```
+16479699379
+15551234567
+14165551234
```

## Run

```bash
# From project root
python scripts/bulk_call/bulk_call.py
```

## Configure

```bash
# Custom phone list
PHONE_LIST_FILE=my_list.txt python scripts/bulk_call/bulk_call.py

# Faster calls (60 second delay)
CALL_DELAY_SECONDS=60 python scripts/bulk_call/bulk_call.py

# Different API endpoint
CALL_API_URL=https://myapp.azurecontainerapps.io/call python scripts/bulk_call/bulk_call.py
```

## Output

**Console:**
```
[1/3] ✅ +16479699379
  Status: success
  Response: Created outbound call
```

**Log File:**
```
call_logs/bulk_call_20260113_102649.csv
```

## Full Documentation

See [README.md](README.md) for complete details.
