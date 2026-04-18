from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.asset import Asset
from app.models.user import User
from app.models.violation import EnforcementRecord, Violation
from app.schemas.stats import DashboardStatsResponse, SystemStatsResponse


router = APIRouter(prefix="/stats", tags=["stats"])


def _count(db: Session, query) -> int:
    return int(db.scalar(query) or 0)


@router.get("/dashboard", response_model=DashboardStatsResponse)
def read_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardStatsResponse:
    org_id = current_user.organisation_id
    asset_count = _count(
        db,
        select(func.count(Asset.id)).where(Asset.organisation_id == org_id),
    )
    queued_assets = _count(
        db,
        select(func.count(Asset.id)).where(
            Asset.organisation_id == org_id,
            Asset.status == "queued",
        ),
    )
    ready_assets = _count(
        db,
        select(func.count(Asset.id)).where(
            Asset.organisation_id == org_id,
            Asset.status == "ready",
        ),
    )
    violation_count = _count(
        db,
        select(func.count(Violation.id)).where(Violation.organisation_id == org_id),
    )
    open_violations = _count(
        db,
        select(func.count(Violation.id)).where(
            Violation.organisation_id == org_id,
            Violation.status == "open",
        ),
    )
    high_severity_violations = _count(
        db,
        select(func.count(Violation.id)).where(
            Violation.organisation_id == org_id,
            Violation.severity.in_(["high", "critical"]),
        ),
    )
    day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    enforcement_actions_today = _count(
        db,
        select(func.count(EnforcementRecord.id))
        .join(Violation, Violation.id == EnforcementRecord.violation_id)
        .where(
            Violation.organisation_id == org_id,
            EnforcementRecord.created_at >= day_start,
        ),
    )
    return DashboardStatsResponse(
        asset_count=asset_count,
        queued_assets=queued_assets,
        ready_assets=ready_assets,
        violation_count=violation_count,
        open_violations=open_violations,
        high_severity_violations=high_severity_violations,
        high_severity=high_severity_violations,
        enforcement_actions_today=enforcement_actions_today,
    )


@router.get("/system", response_model=SystemStatsResponse)
def read_system_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SystemStatsResponse:
    org_id = current_user.organisation_id
    runtime_snapshot = request.app.state.runtime_metrics.snapshot()

    queued_assets = _count(
        db,
        select(func.count(Asset.id)).where(
            Asset.organisation_id == org_id,
            Asset.status == "queued",
        ),
    )
    processing_assets = _count(
        db,
        select(func.count(Asset.id)).where(
            Asset.organisation_id == org_id,
            Asset.status == "processing",
        ),
    )
    ready_assets = _count(
        db,
        select(func.count(Asset.id)).where(
            Asset.organisation_id == org_id,
            Asset.status == "ready",
        ),
    )
    open_violations = _count(
        db,
        select(func.count(Violation.id)).where(
            Violation.organisation_id == org_id,
            Violation.status == "open",
        ),
    )
    high_severity_violations = _count(
        db,
        select(func.count(Violation.id)).where(
            Violation.organisation_id == org_id,
            Violation.severity.in_(["high", "critical"]),
        ),
    )

    queue_depth = queued_assets + processing_assets
    task_mode = str(request.app.state.settings.task_mode)
    ai_mode = "fallback"
    ai_service = getattr(request.app.state, "ai_engine_service", None)
    if ai_service is not None:
        try:
            ai_mode = "full" if ai_service.is_ai_available() else "fallback"
        except Exception:
            ai_mode = "fallback"

    return SystemStatsResponse(
        cpu_percent=runtime_snapshot.cpu_percent,
        memory_percent=runtime_snapshot.memory_percent,
        disk_percent=runtime_snapshot.disk_percent,
        process_uptime_seconds=runtime_snapshot.process_uptime_seconds,
        request_latency_p95_ms=runtime_snapshot.request_latency_p95_ms,
        requests_last_minute=runtime_snapshot.requests_last_minute,
        queue_depth=queue_depth,
        queued_assets=queued_assets,
        processing_assets=processing_assets,
        ready_assets=ready_assets,
        open_violations=open_violations,
        high_severity_violations=high_severity_violations,
        task_mode=task_mode,
        ai_mode=ai_mode,
    )

