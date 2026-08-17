from sqlalchemy.orm import Session

from app.agents.adapters import MockAgentAdapter, OpenAIAgentsAdapter
from app.agents.contracts import (
    AGENT_DEFINITIONS,
    AgentAdapter,
    AgentInput,
    AgentResult,
    AgentStatus,
    parse_agent_output,
)
from app.agents.guardrails import requested_external_actions, sanitize_untrusted_payload
from app.core.config import get_settings
from app.core.enums import ApprovalStatus
from app.models.entities import AgentRun, HumanApproval, ValidationResult


def get_default_adapter() -> AgentAdapter:
    settings = get_settings()
    if settings.agent_provider == "openai":
        return OpenAIAgentsAdapter(settings.openai_model)
    return MockAgentAdapter()


def run_agent(
    session: Session,
    agent_input: AgentInput,
    adapter: AgentAdapter | None = None,
) -> AgentResult:
    definition = AGENT_DEFINITIONS[agent_input.agent_name]
    selected_adapter = adapter or get_default_adapter()
    sanitized_payload, guardrail_warnings = sanitize_untrusted_payload(agent_input.payload)
    sanitized_payload["guardrail_warnings"] = guardrail_warnings
    sanitized_input = agent_input.model_copy(update={"payload": sanitized_payload})

    try:
        raw = selected_adapter.run(definition, sanitized_input)
        output = parse_agent_output(raw)
    except Exception as exc:
        result = AgentResult(
            status=AgentStatus.FAILED,
            output=None,
            errors=[str(exc)],
            sanitized_input=sanitized_input.model_dump(),
        )
        _record_run(session, selected_adapter.provider, agent_input, result)
        return result

    external_actions = requested_external_actions(output.approval_required_actions)
    errors: list[str] = []
    status = AgentStatus.SUCCEEDED
    if external_actions:
        status = AgentStatus.NEEDS_REVIEW
        output.requires_human_review = True
        _request_approvals(session, agent_input, external_actions)
    if output.confidence < definition.confidence_threshold:
        status = AgentStatus.NEEDS_REVIEW
        output.requires_human_review = True
        errors.append("Low confidence output routed to manual review.")
    if guardrail_warnings:
        status = AgentStatus.NEEDS_REVIEW
        output.requires_human_review = True
        errors.append("Prompt-injection-like source text was neutralized.")

    result = AgentResult(
        status=status,
        output=output,
        errors=errors,
        sanitized_input=sanitized_input.model_dump(),
    )
    _record_run(session, selected_adapter.provider, agent_input, result)
    return result


def list_agent_definitions() -> list[dict[str, object]]:
    return [definition.model_dump() for definition in AGENT_DEFINITIONS.values()]


def _record_run(
    session: Session, provider: str, agent_input: AgentInput, result: AgentResult
) -> AgentRun:
    run = AgentRun(
        agent_name=agent_input.agent_name.value,
        input_summary=agent_input.model_dump(),
        output_summary=result.model_dump(),
        provider=provider,
        status=result.status.value,
    )
    session.add(run)
    session.flush()
    if result.status != AgentStatus.SUCCEEDED:
        session.add(
            ValidationResult(
                subject_type=agent_input.subject_type,
                subject_id=agent_input.subject_id or run.id,
                status=result.status.value,
                details=result.model_dump(),
            )
        )
    return run


def _request_approvals(session: Session, agent_input: AgentInput, actions: list[str]) -> None:
    for action in actions:
        session.add(
            HumanApproval(
                action_type=action,
                subject_type=agent_input.subject_type,
                subject_id=agent_input.subject_id or "",
                status=ApprovalStatus.REQUESTED,
                rationale=(
                    "Agent output requested an external write action; human approval required."
                ),
            )
        )
