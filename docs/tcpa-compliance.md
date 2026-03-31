# TCPA Compliance Guide for SMS Automation

The Telephone Consumer Protection Act (TCPA) governs automated text messaging. Non-compliance carries severe penalties. This guide covers the requirements enforced by the workflows in this repo.

## Mandatory: STOP/UNSUBSCRIBE Handling

Any inbound message containing an opt-out keyword **must** immediately stop all future automated messages to that number.

**Required opt-out keywords to detect:**
- STOP
- UNSUBSCRIBE
- CANCEL
- END
- QUIT
- OPT OUT / OPTOUT

**What the workflow does:**
1. Checks every incoming SMS for opt-out keywords (case-insensitive)
2. Adds the number to the opt-out list in Airtable
3. Does NOT send any response (responding to a STOP message can itself be a violation)
4. Logs the opt-out event with timestamp

**Before sending any automated SMS, workflows must:**
- Check the opt-out list
- Skip any number that has opted out
- There is no expiration on opt-outs — they are permanent unless the person explicitly re-opts in

---

## Business Hours Restrictions

Automated messages should only be sent during reasonable hours.

**This repo enforces:**
- Monday through Saturday: 8:00 AM - 7:00 PM Eastern Time
- No messages on Sundays
- Messages triggered outside business hours are queued for the next business day

**State-specific rules:**
Some states have stricter windows (e.g., Florida restricts to 8AM-8PM local time, Washington restricts to 8AM-9PM). Adjust the time check in the Code node if your firm operates in states with tighter restrictions.

---

## Consent Tracking

The TCPA requires **prior express consent** before sending automated texts.

**Types of consent:**
| Consent Level | What It Covers | How to Get It |
|---|---|---|
| Express consent | Informational texts (appointment reminders, case updates) | Written or verbal agreement to receive texts |
| Express written consent | Marketing or promotional texts | Signed written agreement (paper or electronic) |

**What to track in Airtable:**
- Phone number
- Consent type (express / express written)
- Date consent obtained
- Method (web form, signed retainer, verbal + call recording ID)
- Consent scope (what types of messages were agreed to)

**Important:** The burden of proof is on the sender. If you cannot produce consent records, you lose.

---

## Penalties

| Violation Type | Penalty Per Message |
|---|---|
| Negligent violation (no intent) | $500 |
| Willful or knowing violation | $1,500 |
| Class action multiplier | Per-message penalty x every affected recipient |

A single workflow sending unauthorized texts to 100 numbers = $150,000 in potential liability at the willful rate.

---

## Best Practices

### 1. Human Approval Gates
All workflows in this repo include a human approval step before sending any outbound SMS. Do not remove these gates without legal review.

### 2. Double Opt-In
For marketing messages, implement double opt-in:
1. User provides phone number
2. Send a single confirmation text: "Reply YES to confirm you'd like to receive messages from [Firm Name]"
3. Only add to messaging list after receiving YES

### 3. Message Content
- Always identify your firm in the message
- Include opt-out instructions at least once per conversation thread
- Keep messages professional and relevant to the stated consent scope
- Do not send messages unrelated to the original consent purpose

### 4. Record Retention
- Keep consent records for at least **5 years** (statute of limitations is 4 years, plus buffer)
- Keep opt-out records **indefinitely**
- Log all outbound automated messages with timestamp, recipient, content, and consent reference

### 5. Regular Audits
- Monthly: Review opt-out list is being honored
- Quarterly: Audit consent records for completeness
- Annually: Review all active workflows against current TCPA regulations

### 6. Reassigned Numbers
Phone numbers get reassigned. A number that gave consent 2 years ago may belong to someone else now. Consider:
- Re-confirming consent periodically
- Checking for "wrong number" replies
- Using number validation APIs to detect reassigned numbers

---

## Workflow-Specific Implementation

### Missed Call Recovery (`missed-call-recovery.json`)
- Only sends one SMS per missed call (not a sequence)
- Human approval required before send
- Business hours check prevents late-night messages
- Audit log captures every action

### SMS Auto-Responder (`sms-auto-responder.json`)
- STOP keyword check is the **first** thing that happens — before any other logic
- Opted-out numbers are blocked at the top of the flow
- Human approval on every outbound message
- Intent classification does not trigger any automatic sends

---

## Disclaimer

This guide is for informational purposes to support automation design. It is not legal advice. Consult with your firm's compliance team or a TCPA attorney before deploying any automated messaging system.

## State-Specific Rules

Florida has additional requirements beyond federal TCPA:
- Florida Telephone Solicitation Act (FTSA) — stricter than federal
- Prior express written consent required for automated texts
- $500 per violation (Florida), $1,500 per violation (federal TCPA)
