from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AssetMatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    matched_asset_id: str
    score: float
    confidence_label: str
    source_url: str | None = None
    created_at: datetime
    updated_at: datetime


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organisation_id: str
    owner_user_id: str
    title: str
    file_name: str
    file_path: str
    content_type: str
    source_url: str | None = None
    status: str
    fingerprint_vector: list[float] | None = None
    created_at: datetime
    updated_at: datetime


class AssetDetailResponse(AssetResponse):
    matches: list[AssetMatchResponse] = Field(default_factory=list)


class SearchRequest(BaseModel):
    asset_id: str | None = None
    vector: list[float] | None = None
    limit: int = Field(default=5, ge=1, le=20)

    @model_validator(mode="after")
    def validate_input(self) -> "SearchRequest":
        if not self.asset_id and not self.vector:
            raise ValueError("Provide either asset_id or vector.")
        return self


class SearchHitResponse(BaseModel):
    asset_id: str
    title: str
    score: float
    confidence_label: str
    source_url: str | None = None

