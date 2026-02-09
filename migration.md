# Migration: Set Up ACS with a Phone Number and Point to Your Existing Web App

This guide walks through the exact steps to configure **Azure Communication Services (ACS)** with a phone number and route inbound calls to your existing call center app at:

**https://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io**

---

## Prerequisites

- An Azure subscription.
- Your call center app already deployed and reachable at the URL above.
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed (optional; useful for connection strings and verification).

---

## Part 1: Create or Locate Your Azure Communication Services Resource

### Option A: You already have an ACS resource (e.g. from `azd up`)

1. In the [Azure Portal](https://portal.azure.com), go to **All resources** or search for **Communication Services**.
2. Open your existing **Communication Services** resource (name often like `acs-<project>-<env>`).
3. Note the **Resource group** and **Name** — you will need them for the Event Grid step.
4. Skip to [Part 2: Get a phone number](#part-2-get-a-phone-number).

### Option B: Create a new ACS resource

1. In the [Azure Portal](https://portal.azure.com), click **Create a resource**.
2. Search for **Communication Services** and select **Microsoft Communication Services**.
3. Click **Create**.
4. Fill in:
   - **Subscription**: your subscription
   - **Resource group**: create new or use existing (e.g. same as your Container App)
   - **Name**: e.g. `acs-callcenter`
   - **Data location**: choose a region (e.g. **United States** or **Europe**)
5. Click **Review + create**, then **Create**.
6. After deployment, open the resource and note the **Resource group** and **Name**.

---

## Part 2: Get a phone number

1. In your **Communication Services** resource, in the left menu select **Phone numbers**.
2. Click **Get** (or **Get phone numbers**).
3. Choose:
   - **Country or region**: e.g. United States
   - **Number type**: e.g. **Toll free** or **Geographic** (geographic may require more compliance).
4. Click **Search** and pick an available number.
5. Complete the purchase flow (cost is typically around a few dollars per month).
6. Copy the number in **E.164** format (e.g. `+18001234567`) — use the portal’s copy button so the format is correct.
7. Save this value; you will use it as **ACS_SOURCE_NUMBER** and when configuring the app.

---

## Part 3: Configure your existing web app (Container App)

Your app must have these environment variables set so it can receive calls and stream media. Use either the Portal or Azure CLI.

### Required environment variables

| Variable | Value for your app |
|----------|---------------------|
| `ACS_SOURCE_NUMBER` | The E.164 phone number you acquired (e.g. `+18001234567`) |
| `ACS_CONNECTION_STRING` | Primary connection string from your ACS resource (see below) |
| `ACS_CALLBACK_PATH` | `https://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io/acs` |
| `ACS_MEDIA_STREAMING_WEBSOCKET_PATH` | `wss://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io/realtime-acs` |

### Get the ACS connection string

- **Portal**: Open your Communication Services resource → **Keys** (under Settings) → copy **Primary connection string**.
- **CLI** (replace `<resource-group>` and `<acs-name>`):

  ```bash
  az communication list-key --name <acs-name> --resource-group <resource-group> --query primaryConnectionString -o tsv
  ```

### Set the variables on the Container App

**Using Azure Portal**

1. Go to [Azure Portal](https://portal.azure.com) → **Container Apps**.
2. Open the app that serves **callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io** (e.g. `callcenterapp` in the relevant resource group).
3. In the left menu, select **Containers** (or **Revision management** → your revision) → **Edit and deploy** (or **Revision management** → **Create new revision**).
4. Under **Containers**, open your container and go to **Environment variables**.
5. Add or update:
   - `ACS_SOURCE_NUMBER` = your E.164 number
   - `ACS_CONNECTION_STRING` = primary connection string from ACS
   - `ACS_CALLBACK_PATH` = `https://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io/acs`
   - `ACS_MEDIA_STREAMING_WEBSOCKET_PATH` = `wss://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io/realtime-acs`
6. Save and deploy the new revision so the app restarts with the new settings.

**Using Azure CLI**

Replace `<resource-group>`, `<container-app-name>`, and `<acs-name>` with your values. Use the same URL values as in the table above.

```bash
# Get connection string
ACS_CONN=$(az communication list-key --name <acs-name> --resource-group <resource-group> --query primaryConnectionString -o tsv)

# Set env vars on the Container App (merge with existing)
az containerapp update --name <container-app-name> --resource-group <resource-group> \
  --set-env-vars \
    "ACS_SOURCE_NUMBER=+1XXXXXXXXXX" \
    "ACS_CONNECTION_STRING=$ACS_CONN" \
    "ACS_CALLBACK_PATH=https://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io/acs" \
    "ACS_MEDIA_STREAMING_WEBSOCKET_PATH=wss://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io/realtime-acs"
```

---

## Part 4: Event Grid — route inbound calls to your app

Inbound calls are delivered as **Incoming Call** events from ACS via **Event Grid**. You need a **System Topic** for your ACS resource and an **Event Subscription** whose webhook is your app’s `/acs/incoming` endpoint.

### Step 1: Ensure an Event Grid System Topic exists for your ACS resource

1. In the [Azure Portal](https://portal.azure.com), search for **Event Grid System Topics** (or **System topics**).
2. Check if there is a system topic whose **Source** is your **Communication Services** resource (e.g. `acs-callcenter` or `acs-<project>-<env>`).
3. **If it exists**: note its name and resource group; go to [Step 2: Create the Event Subscription](#step-2-create-the-event-subscription).
4. **If it does not exist** (e.g. you created ACS manually):
   - In your **Communication Services** resource, open **Events** (or **Event Grid**) in the left menu, or
   - Create a system topic manually:
     - **Create a resource** → search **Event Grid System Topic** → **Create**.
     - **Topic type**: **Microsoft.Communication.CommunicationServices**.
     - **Source resource**: select your Communication Services resource.
     - Create the resource.

### Step 2: Create the Event Subscription

1. Open the **Event Grid System Topic** that is linked to your ACS resource.
2. In the left menu, select **Event subscriptions**.
3. Click **+ Event subscription**.
4. **Basics**:
   - **Name**: e.g. `receive-call` or `incoming-call-to-callcenterapp`.
   - **Event Schema**: **Event Grid Schema**.
5. **Filters**:
   - **Filter to Event Types**: enable **Incoming Call** (event type `Microsoft.Communication.IncomingCall`). You can leave other event types unchecked if you only need inbound calls.
6. **Endpoint**:
   - **Endpoint type**: **Web Hook**.
   - **Endpoint**:  
     `https://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io/acs/incoming`
7. Click **Create**.
8. Event Grid will send a validation request to that URL. Your app’s `/acs/incoming` handler must respond with the validation code (the existing code in this repo does this). Once validation succeeds, the subscription becomes active.

---

## Part 5: Verify end-to-end

1. **App and env vars**
   - Open https://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io and confirm the app loads.
   - In Azure Portal, confirm the Container App revision has the four ACS-related environment variables set correctly.

2. **Inbound call**
   - From a phone, call the ACS number you purchased.
   - The call should be answered and handled by your AI agent (browser and phone flows both use the same backend and `/acs/incoming` + realtime WebSocket).

3. **Optional: outbound “call me” from the web app**
   - On the same site, use “Receive a call from us” or “Call us directly” and ensure the number used is the same **ACS_SOURCE_NUMBER** and that outbound calls work.

---

## Summary checklist

- [ ] ACS resource created or located.
- [ ] Phone number acquired in ACS and copied in E.164 format.
- [ ] Container App env vars set: `ACS_SOURCE_NUMBER`, `ACS_CONNECTION_STRING`, `ACS_CALLBACK_PATH`, `ACS_MEDIA_STREAMING_WEBSOCKET_PATH` (using your app URL and `wss://` for the WebSocket).
- [ ] Event Grid System Topic exists for the ACS resource.
- [ ] Event Subscription created with endpoint `https://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io/acs/incoming` and **Incoming Call** event type.
- [ ] Tested an inbound call to the ACS number.

---

## Troubleshooting

- **Calls not received**: Confirm the Event Subscription endpoint URL is exactly `https://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io/acs/incoming` (no trailing slash unless your app expects it) and that the subscription shows as **Enabled** after validation.
- **Validation failed**: Ensure the Container App is running and the `/acs/incoming` route is publicly reachable; the handler must respond to `aeg-event-type: SubscriptionValidation` with `validationResponse` set to the received `validationCode`.
- **One-way or no audio**: Check `ACS_MEDIA_STREAMING_WEBSOCKET_PATH` is `wss://callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io/realtime-acs` (HTTPS for the site, WSS for the WebSocket path).
- **Wrong number or “not configured”**: Verify `ACS_SOURCE_NUMBER` is in E.164 and matches the number shown in the ACS **Phone numbers** blade.

If your app runs in a different region or behind a custom domain, replace `callcenterapp.purplebay-fcdfd637.eastus2.azurecontainerapps.io` in both the HTTPS and WSS URLs with your actual hostname.
