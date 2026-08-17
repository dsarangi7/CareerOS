from pydantic import BaseModel, ConfigDict


class TailoredCVRequest(BaseModel):
    profile_id: str
    base_version: str = "battery-analytics-v1"


class TailoredCVRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    base_cv_id: str | None
    status: str
    source_text: str
    rendered_pdf_path: str | None
    validation_summary: dict[str, object]


class ClaimValidationReport(BaseModel):
    tailored_cv_id: str
    unsupported_claims: list[str]
    supported_claims: list[dict[str, object]]
    required_user_confirmation: list[str]
