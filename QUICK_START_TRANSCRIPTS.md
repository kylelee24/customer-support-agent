# Quick Start: Call Transcripts & Email

## Step 1: Set Up Azure Communication Services Email

### Option A: Use Azure-Managed Domain (Fastest)

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your ACS resource: `acs-b7yjv3h22fjci`
3. Click **Email** → **Domains** in left menu
4. Click **Connect domain** → **Azure Managed Domain**
5. Copy the sender address shown (e.g., `DoNotReply@xxxxxxxx.azurecomm.net`)

### Option B: Use Custom Domain

1. Follow steps 1-3 above
2. Click **Connect domain** → **Custom Domain**
3. Add your domain and verify DNS records
4. Configure sender address

## Step 2: Configure Environment Variables

Add to your `.env` file or Azure configuration:

```bash
# Your existing ACS connection string
ACS_EMAIL_CONNECTION_STRING=<paste-your-ACS-connection-string>

# Sender email from Step 1
ACS_EMAIL_SENDER=DoNotReply@xxxxxxxx.azurecomm.net

# Your email address
TRANSCRIPT_EMAIL_RECIPIENTS=kyle.a.lee24@gmail.com
```

**To get your connection string:**
- In Azure Portal, go to your ACS resource
- Click **Keys** in left menu
- Copy **Connection string**

## Step 3: Install Dependencies

```bash
# Activate your virtual environment if needed
source .venv/bin/activate

# Install new dependency
pip install azure-communication-email==1.1.0

# Or reinstall all
pip install -r src/app/requirements.txt
```

## Step 4: Test Locally (Optional)

```bash
# Set environment variables
export ACS_EMAIL_CONNECTION_STRING="<your-connection-string>"
export ACS_EMAIL_SENDER="DoNotReply@<your-domain>.azurecomm.net"
export TRANSCRIPT_EMAIL_RECIPIENTS="kyle.a.lee24@gmail.com"

# Run the app
python src/app/app.py
```

## Step 5: Deploy to Azure

```bash
# Get environment name
source <(azd env get-values | grep AZURE_ENV_NAME)

# Add environment variables to Azure
azd env set ACS_EMAIL_CONNECTION_STRING "<your-connection-string>"
azd env set ACS_EMAIL_SENDER "DoNotReply@<your-domain>.azurecomm.net"
azd env set TRANSCRIPT_EMAIL_RECIPIENTS "kyle.a.lee24@gmail.com"

# Deploy
bash ./azd-hooks/deploy.sh app $AZURE_ENV_NAME
```

## Step 6: Make a Test Call

```bash
# Ensure API_URL points to your deployed app
export API_URL=https://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io/call

# Make a test call
python bulk_call.py
```

## Step 7: Check Results

### Console Output
You should see:
```
📝 Created transcript session: <call-id>
💬 [user]: Hello...
💬 [assistant]: Hi! I'd be happy to help...
✅ Email sent successfully!
```

### Email
Check `kyle.a.lee24@gmail.com` for:
- Subject: "Call Transcript - +16479699379 (Xm Ys)"
- HTML-formatted transcript with call details
- Professional styling

### Files
Check `call_logs/` directory for:
- `transcript_<callId>_<timestamp>.json`

## Troubleshooting

### "Email service not configured"
**Fix:** Verify environment variables are set correctly
```bash
echo $ACS_EMAIL_CONNECTION_STRING
echo $ACS_EMAIL_SENDER
echo $TRANSCRIPT_EMAIL_RECIPIENTS
```

### "Failed to send email: 401 Unauthorized"
**Fix:** Connection string is incorrect or expired
- Get fresh connection string from Azure Portal
- Ensure you're using the PRIMARY connection string

### "Failed to send email: 403 Forbidden"
**Fix:** Sender address not verified
- Go to ACS → Email → Domains
- Verify sender address is properly configured
- If using custom domain, check DNS records

### Email not received
**Check:**
1. Spam/junk folder
2. Email address spelling in `TRANSCRIPT_EMAIL_RECIPIENTS`
3. Email service status in Azure Portal
4. Application logs for error messages

### Empty transcript
**This is normal if:**
- Call disconnected before conversation started
- Testing with very short calls

**To get better results:**
- Let calls run for at least 10-15 seconds
- Speak clearly during test calls
- Ensure phone answers the call

## Verification Checklist

- [ ] Azure ACS Email domain configured
- [ ] Environment variables set correctly
- [ ] Dependencies installed (`azure-communication-email`)
- [ ] Application deploys without errors
- [ ] Test call completes successfully
- [ ] Console shows transcript messages
- [ ] Email received at specified address
- [ ] Transcript JSON file created in `call_logs/`

## Next Steps

Once working:
1. Add more email recipients if needed (comma-separated)
2. Review transcript formatting in emails
3. Check saved transcript files in `call_logs/`
4. Monitor application logs for transcript capture
5. Customize email styling if desired (edit `transcript_manager.py`)

## Quick Reference

**Files Created:**
- `src/app/backend/transcript_manager.py` - Transcript recording
- `src/app/backend/email_service.py` - Email sending

**Files Modified:**
- `src/app/backend/rtmt.py` - Transcript capture
- `src/app/backend/acs.py` - Email triggering
- `src/app/app.py` - Service initialization
- `src/app/requirements.txt` - Added email dependency
- `README.md` - Added documentation

**Key Environment Variables:**
```
ACS_EMAIL_CONNECTION_STRING
ACS_EMAIL_SENDER
TRANSCRIPT_EMAIL_RECIPIENTS
```

**Support Files:**
- `TRANSCRIPT_FEATURE_SUMMARY.md` - Full documentation
- `QUICK_START_TRANSCRIPTS.md` - This file
