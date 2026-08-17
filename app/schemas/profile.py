from pydantic import BaseModel, ConfigDict


class CandidateProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    current_location: str | None
    origin: str | None
    current_role: str | None
    positioning: str
    review_notes: str
