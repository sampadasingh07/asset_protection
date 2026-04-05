from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ViolationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organisation_id: str
    asset_id: str
    match_id: str | None = None
    severity: str
    status: str
    confidence: float
    summary: str
    source_url: str | None = None
    created_at: datetime
    updated_at: datetime


class ViolationStatusUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=40)


class EnforcementRecordCreate(BaseModel):
    action_type: str = Field(min_length=2, max_length=80)
    platform_name: str = Field(min_length=2, max_length=80)
    status: str = "draft"
    external_reference: str | None = None
    notes: str | None = None


class EnforcementRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    violation_id: str
    action_type: str
    platform_name: str
    status: str
    external_reference: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

