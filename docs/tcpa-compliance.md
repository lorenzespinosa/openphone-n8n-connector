# SMS workflow review notes

This repository contains example n8n workflows, not a verified consent, opt-out, or regulatory compliance system. This page replaces earlier guidance that described fixed requirements, penalty figures, and implemented safeguards beyond what the example files establish.

## What the example files show

- `workflows/sms-auto-responder.json` checks inbound message substrings and branches to an opt-out update request and an approval form. The external opt-out store and approval behavior have not been independently verified here.
- `workflows/missed-call-recovery.json` drafts an outbound message and includes an approval form. The checked workflow JSON does not independently query an opt-out or consent source before its outbound request.
- Neither example proves that legal rules, hours, logging, or a blocking human decision will be enforced in your deployment.

## Before any real outbound message

Have a qualified reviewer assess the applicable requirements for the message and recipient. Implement and test consent and opt-out handling, approval, recipient validation, logging, and failure behavior in the actual configured workflow and connected services. These files are not legal advice or permission to send messages.
