# Security

- Credentials belong only in environment variables or a local `.env` file.
- `.env` is ignored by git.
- Job descriptions and external messages are untrusted source text.
- Human approval is mandatory before external write actions.
- Audit events are recorded for seed, job creation, sponsorship classification, scoring, and status transitions.
- Agent outputs cannot execute external write actions directly; requested external actions create `HumanApproval` records.
- Untrusted text passed to agents is scanned for instruction-injection markers and neutralized before adapter execution.
- `python -m scripts.tasks security-scan` checks repository text files for common secret patterns.
- `python -m scripts.tasks backup-db` copies the local SQLite database to `data/backups/`.
- Upload validation helpers enforce allowlisted file extensions and size limits.

## Current Limits

- The app is designed for local single-user operation. It does not yet implement hosted authentication, multi-user authorization, encryption-at-rest, or managed secret rotation.
- The security scanner is a practical local safeguard, not a replacement for dedicated secret-scanning or SAST tooling.
