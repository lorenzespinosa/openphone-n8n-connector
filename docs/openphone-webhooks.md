# OpenPhone Webhooks Reference

## Available Webhook Events

| Event | Description | Used In |
|---|---|---|
| `call.completed` | Fired when a call ends (includes missed calls where `status=missed`) | missed-call-recovery, call-log-sync |
| `call.ringing` | Fired when an inbound call starts ringing | — |
| `message.received` | Fired when an inbound SMS/MMS is received | sms-auto-responder |
| `message.delivered` | Fired when an outbound message is confirmed delivered | — |
| `contact.created` | Fired when a new contact is created in OpenPhone | contact-sync |
| `contact.updated` | Fired when a contact is modified | contact-sync |
| `voicemail.created` | Fired when a new voicemail is left | — |
| `recording.completed` | Fired when a call recording finishes processing | — |

---

## Payload Structure

All webhook payloads follow this structure:

```json
{
  "id": "evt_<unique_id>",
  "object": "event",
  "apiVersion": "v1",
  "createdAt": "2025-10-15T14:32:18.000Z",
  "type": "<event.type>",
  "data": {
    "object": "<object_type>",
    "id": "<object_id>",
    ...
  }
}
```

### Key Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique event ID — use for deduplication |
| `type` | string | Event type (e.g., `call.completed`, `message.received`) |
| `createdAt` | ISO 8601 | When the event was created |
| `data` | object | The full object that triggered the event |
| `data.id` | string | ID of the call, message, or contact |
| `data.from` | string | Phone number (E.164 format) of the sender/caller |
| `data.to` | string | Phone number (E.164 format) of the recipient |
| `data.direction` | string | `inbound` or `outbound` |
| `data.status` | string | Object-specific status (e.g., `completed`, `missed`, `received`) |

---

## Webhook Setup Instructions

### 1. Get Your n8n Webhook URLs

For each workflow you want to activate, get the webhook URL from the Webhook trigger node in n8n:

- **Missed Call Recovery:** `https://your-n8n-instance.com/webhook/openphone-missed-call`
- **SMS Auto-Responder:** `https://your-n8n-instance.com/webhook/openphone-incoming-sms`

### 2. Configure in OpenPhone

1. Log in to [OpenPhone](https://my.openphone.com)
2. Go to **Settings** > **Integrations** > **Webhooks**
3. Click **Add Webhook**
4. Enter your n8n webhook URL
5. Select the events you want to subscribe to:
   - For missed call recovery: `call.completed`
   - For SMS auto-responder: `message.received`
6. Save

### 3. Alternatively, Use the API

```bash
curl -X POST https://api.openphone.com/v1/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-n8n-instance.com/webhook/openphone-missed-call",
    "events": ["call.completed"]
  }'
```

### 4. Verify the Webhook

OpenPhone may send a verification request when you first register a webhook. The n8n Webhook node handles this automatically by responding with a 200 status.

### 5. Test with Sample Payloads

Use the files in `/payloads/` to test your workflows:
- Send a POST request to your webhook URL with the sample payload
- Use n8n's built-in "Test Workflow" feature
- Or use curl:

```bash
curl -X POST https://your-n8n-instance.com/webhook-test/openphone-missed-call \
  -H "Content-Type: application/json" \
  -d @payloads/missed-call-event.json
```

---

## Rate Limits

| Limit | Value |
|---|---|
| API rate limit | 10 requests per second per API key |
| Webhook delivery | OpenPhone retries failed deliveries 3 times with exponential backoff |
| Webhook timeout | Your endpoint must respond within 10 seconds |
| Max concurrent webhooks | No documented limit, but keep URLs minimal |

### Handling Rate Limits in n8n

- The call-log-sync workflow uses a 15-minute polling interval to stay well within rate limits
- For webhook-triggered workflows, n8n processes events serially by default
- If you hit 429 errors on outbound API calls, add retry logic with backoff in the HTTP Request node settings

---

## Idempotency

Webhook events may be delivered more than once. Use the `id` field from the event payload to deduplicate:

1. Before processing, check if `event.id` exists in your Airtable audit log
2. If it exists, skip processing
3. If it does not exist, process and log the event ID

This is especially important for the SMS auto-responder to avoid sending duplicate messages.

---

## Security

- **Webhook URL:** Use HTTPS only. Do not expose webhook URLs publicly without authentication.
- **n8n Authentication:** Consider adding Basic Auth or Header Auth to your n8n webhook nodes for an extra layer of security.
- **IP Allowlisting:** If your n8n instance supports it, restrict incoming webhook traffic to OpenPhone's IP ranges (check their docs for current ranges).
