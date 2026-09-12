from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AgentRunRequest(BaseModel):
    campaign: str = Field(pattern="^(healthcare|corporate|relocation|partners|social)$")
    max_queries: int = Field(default=5, ge=1, le=20)


class LeadOut(BaseModel):
    id: int
    name: str | None
    source: str
    campaign: str
    lead_type: str | None
    url: str | None
    occupation: str | None
    assignment_location: str | None
    move_in: str | None
    move_out: str | None
    stay_days: int | None
    budget: float | None
    reason_for_stay: str | None
    evidence: str | None
    score: int
    classification: str
    status: str
    ai_confidence: float | None
    approved_for_contact: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
