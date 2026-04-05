from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    asset_count: int
    queued_assets: int
    ready_assets: int
    violation_count: int
    open_violations: int
    high_severity_violations: int


class GraphNode(BaseModel):
    id: str
    label: str
    kind: str = "asset"


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    score: float | None = None


class PropagationResponse(BaseModel):
    asset_id: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)

