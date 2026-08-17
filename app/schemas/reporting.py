from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CommunicationCreate(BaseModel):
    contact_id: str | None = None
    channel: str
    direction: str
    body: str = ""


class CommunicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str | None
    contact_id: str | None
    channel: str
    direction: str
    body: str
    created_at: datetime


class FollowUpCreate(BaseModel):
    due_at: datetime
    notes: str = ""


class FollowUpRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str | None
    due_at: datetime
    status: str
    notes: str


class InterviewCreate(BaseModel):
    stage: str
    scheduled_at: datetime | None = None
    notes: str = ""


class InterviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    stage: str
    scheduled_at: datetime | None
    notes: str


class InterviewPreparationPackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    interview_id: str
    content: dict[str, Any]
    source_notes: list[str]


class OutcomeCreate(BaseModel):
    result: str
    reason: str | None = None
    notes: str = ""


class OutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    result: str
    reason: str | None
    notes: str
    created_at: datetime


class WeeklyReportRequest(BaseModel):
    week_start: str


class WeeklyReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    week_start: str
    facts: dict[str, Any]
    recommendations: dict[str, Any]
