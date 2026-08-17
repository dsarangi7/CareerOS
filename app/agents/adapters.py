from typing import Any

from app.agents.contracts import AgentDefinition, AgentInput


class MockAgentAdapter:
    provider = "mock"

    def run(self, definition: AgentDefinition, agent_input: AgentInput) -> dict[str, Any]:
        findings = [f"Processed {agent_input.subject_type} locally with deterministic mock agent."]
        if agent_input.payload.get("guardrail_warnings"):
            findings.append("Untrusted instruction-like text was neutralized.")
        return {
            "summary": f"{definition.name.value} completed locally.",
            "findings": findings,
            "recommendations": ["Review outputs before using them in application materials."],
            "evidence_refs": [agent_input.subject_id] if agent_input.subject_id else [],
            "confidence": float(agent_input.payload.get("mock_confidence", 0.86)),
            "requires_human_review": False,
            "approval_required_actions": [],
        }


class MalformedMockAgentAdapter:
    provider = "mock_malformed"

    def run(self, definition: AgentDefinition, agent_input: AgentInput) -> dict[str, Any]:
        return {"summary": "missing confidence"}


class LowConfidenceMockAgentAdapter:
    provider = "mock_low_confidence"

    def run(self, definition: AgentDefinition, agent_input: AgentInput) -> dict[str, Any]:
        return {
            "summary": "Low confidence mock output.",
            "findings": ["Not enough evidence."],
            "recommendations": ["Route to manual review."],
            "evidence_refs": [],
            "confidence": 0.25,
            "requires_human_review": False,
            "approval_required_actions": [],
        }


class UnsafeActionMockAgentAdapter:
    provider = "mock_unsafe_action"

    def run(self, definition: AgentDefinition, agent_input: AgentInput) -> dict[str, Any]:
        return {
            "summary": "Unsafe action requested.",
            "findings": ["The draft asks to submit an application."],
            "recommendations": ["Request human approval."],
            "evidence_refs": [],
            "confidence": 0.9,
            "requires_human_review": False,
            "approval_required_actions": ["submit_application"],
        }


class OpenAIAgentsAdapter:
    provider = "openai"

    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, definition: AgentDefinition, agent_input: AgentInput) -> dict[str, Any]:
        try:
            from agents import Agent, Runner  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError("OpenAI Agents SDK is not installed or unavailable") from exc

        agent = Agent(
            name=definition.name.value,
            instructions=(
                f"{definition.purpose}\n"
                "Return JSON matching the CareerOS AgentOutput schema. "
                "Do not perform external write actions."
            ),
            model=self.model,
        )
        result = Runner.run_sync(agent, str(agent_input.model_dump()))  # pragma: no cover
        final_output = getattr(result, "final_output", None)  # pragma: no cover
        if not isinstance(final_output, dict):  # pragma: no cover
            raise RuntimeError("OpenAI agent did not return structured output")
        return final_output  # pragma: no cover
