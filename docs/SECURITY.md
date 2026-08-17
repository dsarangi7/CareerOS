# Security

- Credentials belong only in environment variables or a local `.env` file.
- `.env` is ignored by git.
- Job descriptions and external messages are untrusted source text.
- Human approval is mandatory before external write actions.
- Audit events are recorded for seed, job creation, sponsorship classification, scoring, and status transitions.
