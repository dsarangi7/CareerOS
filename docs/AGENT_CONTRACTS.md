# Agent Contracts

# Agent Contracts

Phase 5 adds typed contracts and deterministic local adapters for all requested agents.

- Default provider: `mock`
- Optional provider: `openai`
- Config: `CAREEROS_AGENT_PROVIDER` and `CAREEROS_OPENAI_MODEL`
- Local startup, tests, profile seed, CRM, and CV generation do not require an API key.
- Agent outputs must validate against `AgentOutput`.
- Malformed outputs are rejected and stored as failed `AgentRun` records.
- Low-confidence outputs enter manual review.
- Prompt-injection-like text in untrusted payload fields is neutralized before adapter execution.
- External-write actions create `HumanApproval` requests instead of executing.

The optional OpenAI adapter follows the official OpenAI documentation direction of keeping API credentials in environment variables and placing Agents SDK orchestration behind backend code. CareerOS keeps this optional so deterministic tests remain credential-free.
