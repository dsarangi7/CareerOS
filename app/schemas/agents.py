from typing import Any

from pydantic import BaseModel, Field

from app.agents.contracts import AgentName, AgentResult


class AgentRunRequest(BaseModel):
    agent_name: AgentName
    subject_type: str
    subject_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(AgentResult):
    pass
