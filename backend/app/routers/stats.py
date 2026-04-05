from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.asset import Asset
from app.models.user import User
from app.models.violation import Violation
from app.schemas.stats import DashboardStatsResponse


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
    return DashboardStatsResponse(
        asset_count=asset_count,
        queued_assets=queued_assets,
        ready_assets=ready_assets,
        violation_count=violation_count,
        open_violations=open_violations,
        high_severity_violations=high_severity_violations,
    )

