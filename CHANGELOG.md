# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2025-11-15

### Added
- Contact sync workflow (OpenPhone <-> CRM bidirectional)
- Conflict resolution logic: CRM wins as source of truth
- Contact sync result sample payload
- CONTRIBUTING.md with workflow submission guidelines

### Changed
- Upgraded all HTTP Request nodes to typeVersion 4.1
- Improved phone number normalization to handle international formats
- Updated TCPA compliance guide with reassigned number guidance

### Fixed
- Business hours check now correctly handles Eastern Daylight Time (EDT) transitions
- SMS auto-responder switch node routes now match case-insensitively

---

## [0.2.0] - 2025-08-20

### Added
- SMS auto-responder workflow with AI intent classification
- Call log sync workflow (15-minute polling to Airtable)
- Repeat missed call detection with Slack alerting
- TCPA compliance documentation
- OpenPhone webhooks reference documentation
- Sample payloads for all webhook events

### Changed
- Missed call recovery now includes human approval gate before sending SMS
- Added opt-out list checking to all SMS-sending workflows

### Fixed
- Webhook node response mode set to `onReceived` to prevent OpenPhone timeouts

---

## [0.1.0] - 2025-05-10

### Added
- Initial release
- Missed call recovery workflow
  - OpenPhone webhook trigger
  - Business hours check (Mon-Sat 8AM-7PM ET)
  - CRM contact lookup
  - SMS response via OpenPhone API
  - Audit logging to Airtable
- Sample missed call event payload
- README with Mermaid flow diagrams
- MIT License
- .gitignore for n8n projects
