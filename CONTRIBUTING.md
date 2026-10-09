# Contributing to OpenPhone n8n Connector

Thanks for your interest in contributing. This repo contains n8n workflow templates, so contributing looks a bit different from a typical code project.

## How to Contribute

### Reporting Issues

- Open a GitHub Issue with a clear description of the problem
- Include which workflow is affected
- Include the n8n version you are running
- If possible, include the error output from n8n's execution log (with any sensitive data redacted)

### Suggesting New Workflows

1. Open an Issue with the `enhancement` label
2. Describe the use case: what triggers it, what it does, what systems are involved
3. Include a flow diagram if possible (Mermaid syntax preferred)

### Submitting Workflow Changes

1. **Fork** this repository
2. **Create a branch** from `main`: `git checkout -b feature/your-workflow-name`
3. **Make your changes** — see the workflow guidelines below
4. **Test** your workflow by importing it into n8n and running it with sample payloads
5. **Submit a Pull Request** with a description of what the workflow does and how you tested it

## Workflow Guidelines

### Structure

- All workflows go in the `workflows/` directory
- Sample payloads go in `payloads/`
- Use descriptive node names (not "Code1", "HTTP Request2")

### Required Elements

Every workflow must include:

1. **Trigger** — Webhook or Schedule
2. **Input validation** — Check required fields exist before processing
3. **Error handling** — At minimum, a catch path that logs failures
4. **Audit logging** — Write key events to Airtable or similar
5. **Sticky notes** — Add a sticky note to the workflow canvas explaining the flow at a high level

### n8n JSON Standards

- Export workflows using n8n's built-in export (Workflow menu > Export)
- Set `"active": false` — workflows should not auto-activate on import
- Remove all credential values — use placeholder strings like `YOUR_API_KEY`
- Use `555`-prefix phone numbers in any hardcoded examples
- Ensure the JSON is valid and importable (test by importing into a fresh n8n instance)

### SMS-related contributions

If you propose an SMS workflow, document the intended consent and opt-out checks, the approval step, and the tests for both allowed and blocked messages. See `docs/tcpa-compliance.md` for this repository's example limitations. Determine applicable legal requirements with a qualified reviewer; these files are not compliance guidance.

### Commit Messages

Use clear, descriptive commit messages:
- `add: voicemail transcription workflow`
- `fix: business hours check not accounting for DST`
- `update: missed call recovery SMS template`
- `docs: add webhook retry behavior notes`

## Code of Conduct

Be respectful, constructive, and professional. We are all here to build useful automations.

## Questions?

Open an Issue with the `question` label or reach out to the maintainer.
