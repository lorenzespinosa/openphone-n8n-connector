# OpenPhone + n8n Connector

A collection of production-ready n8n workflows for integrating [OpenPhone](https://www.openphone.com/) with CRM, Airtable, Slack, and AI services. Built for law firms and professional services teams that need reliable phone automation with TCPA compliance baked in.

## Architecture Overview

```mermaid
graph LR
    OP[OpenPhone] -->|Webhooks| N8N[n8n]
    N8N -->|API| CRM[CRM / Lawmatics]
    N8N -->|API| AT[Airtable]
    N8N -->|API| SL[Slack]
    N8N -->|API| AI[OpenAI]
    N8N -->|API| OP

    style OP fill:#4A90D9,color:#fff
    style N8N fill:#FF6D5A,color:#fff
    style CRM fill:#34C759,color:#fff
    style AT fill:#FCBF49,color:#000
    style SL fill:#611F69,color:#fff
    style AI fill:#10A37F,color:#fff
```

## Workflows

### 1. Missed Call Recovery

Automatically detects missed calls, checks business hours, identifies if the caller is a known contact, and sends a recovery SMS — with human approval before any message goes out.

```mermaid
flowchart TD
    A[OpenPhone Webhook: call.completed, status=missed] --> B[Extract Caller Info]
    B --> C{Business Hours? Mon-Sat 8AM-7PM ET}
    C -->|Yes| D[Check CRM for Existing Contact]
    C -->|No| E[Queue for Next Business Day]
    D --> F{New or Existing?}
    F -->|New| G[Draft SMS: New Caller Template]
    F -->|Existing| H[Draft SMS: Existing Client Template]
    G --> I[Human Approval Gate]
    H --> I
    I -->|Approved| J[Send SMS via OpenPhone API]
    I -->|Rejected| K[Log: Skipped]
    J --> L[Audit Log to Airtable]
    K --> L
    E --> L
```

**File:** [`workflows/missed-call-recovery.json`](workflows/missed-call-recovery.json)

---

### 2. SMS Auto-Responder

Handles inbound SMS with TCPA-compliant opt-out detection, AI-powered intent classification, and templated responses routed by intent.

```mermaid
flowchart TD
    A[OpenPhone Webhook: message.received] --> B{STOP / UNSUBSCRIBE?}
    B -->|Yes| C[Update Opt-Out List]
    C --> D[Do NOT Respond]
    B -->|No| E{Business Hours?}
    E -->|No| F[After-Hours Auto-Reply]
    E -->|Yes| G[AI Classify Intent via OpenAI]
    G --> H{Intent Type}
    H -->|Appointment Request| I[Appointment Template]
    H -->|Case Status| J[Case Status Template]
    H -->|General Inquiry| K[General Template]
    I --> L[Human Approval Gate]
    J --> L
    K --> L
    F --> L
    L -->|Approved| M[Send SMS via OpenPhone API]
    L -->|Rejected| N[Log: Skipped]
    M --> O[Audit Log to Airtable]
    N --> O
    D --> O
```

**File:** [`workflows/sms-auto-responder.json`](workflows/sms-auto-responder.json)

---

### 3. Call Log Sync

Polls OpenPhone every 15 minutes, formats call records, writes them to Airtable, and alerts Slack when the same number has 2+ missed calls within 24 hours.

```mermaid
flowchart TD
    A[Schedule: Every 15 Minutes] --> B[GET Recent Calls from OpenPhone API]
    B --> C[Format Call Records]
    C --> D[Write to Airtable]
    D --> E[Flag Repeat Missed Calls]
    E --> F{Same Number 2+ Missed in 24hrs?}
    F -->|Yes| G[Slack Alert: Urgent Follow-Up]
    F -->|No| H[Done]
```

**File:** [`workflows/call-log-sync.json`](workflows/call-log-sync.json)

---

### 4. Contact Sync

Daily bidirectional sync between OpenPhone and CRM. CRM is the source of truth for conflict resolution.

```mermaid
flowchart TD
    A[Schedule: Daily at 2AM ET] --> B[GET Contacts from OpenPhone]
    B --> C[GET Contacts from CRM]
    C --> D[Compare & Find Mismatches]
    D --> E{Mismatch Type}
    E -->|New in OpenPhone| F[Create in CRM]
    E -->|Updated in CRM| G[Update in OpenPhone]
    E -->|Conflict| H[CRM Wins — Source of Truth]
    F --> I[Audit Log to Airtable]
    G --> I
    H --> I
```

**File:** [`workflows/contact-sync.json`](workflows/contact-sync.json)

---

## TCPA Compliance

All SMS workflows include mandatory TCPA safeguards:

- **STOP/UNSUBSCRIBE handling** — Immediate opt-out, no further messages sent
- **Business hours only** — Mon-Sat 8AM-7PM ET (no Sundays)
- **Human approval gates** — No automated outbound SMS without review
- **Consent tracking** — Logged in Airtable audit trail
- **Penalties** — Up to $1,500 per non-compliant message

See [`docs/tcpa-compliance.md`](docs/tcpa-compliance.md) for the full guide.

---

## Quick Start

1. **Import workflows** — In n8n, go to Workflows > Import and select any `.json` file from `workflows/`
2. **Configure credentials** — Set up OpenPhone API key, CRM API credentials, Airtable token, Slack webhook, and OpenAI key in n8n Credentials
3. **Update placeholders** — Replace placeholder URLs and IDs in HTTP Request nodes with your actual endpoints
4. **Set up OpenPhone webhooks** — Point webhooks to your n8n webhook URLs (see [`docs/openphone-webhooks.md`](docs/openphone-webhooks.md))
5. **Test with sample payloads** — Use files in `payloads/` to test each workflow
6. **Activate** — All workflows ship as `active: false` — enable when ready

## Project Structure

```
openphone-n8n-connector/
├── workflows/
│   ├── missed-call-recovery.json
│   ├── sms-auto-responder.json
│   ├── call-log-sync.json
│   └── contact-sync.json
├── payloads/
│   ├── missed-call-event.json
│   ├── incoming-sms-event.json
│   ├── call-log-response.json
│   └── contact-sync-result.json
├── docs/
│   ├── tcpa-compliance.md
│   └── openphone-webhooks.md
├── .gitignore
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
└── README.md
```

## License

MIT License. See [LICENSE](LICENSE).
