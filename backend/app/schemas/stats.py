from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    asset_count: int
    queued_assets: int
    ready_assets: int
    violation_count: int
    open_violations: int
    high_severity_violations: int
    high_severity: int
    enforcement_actions_today: int


class SystemStatsResponse(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    process_uptime_seconds: float
    request_latency_p95_ms: float
    requests_last_minute: int
    queue_depth: int
    queued_assets: int
    processing_assets: int
    ready_assets: int
    open_violations: int
    high_severity_violations: int
    task_mode: str
    ai_mode: str


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

