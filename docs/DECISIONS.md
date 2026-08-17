# Decisions

## 2026-08-17

- Created a new `career-os` directory under `Downloads` because the workspace root contained unrelated personal/downloaded files and no git repository.
- Used Python 3.11.9 for local validation because Python 3.12 was not available in PATH. The project remains configured for Python 3.11+ locally and Docker uses Python 3.12.
- Implemented `python -m scripts.tasks` commands behind the Makefile because GNU `make` is not installed on this Windows machine.
- Used deterministic mock-friendly services first. OpenAI-backed agents remain deferred until the core workflow is stable and does not require credentials.
- Seeded uncertain profile wording with `requires_confirmation` or `user_reported_pending_evidence` states so it cannot silently become a finalized CV claim.
