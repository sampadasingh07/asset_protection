from sqlalchemy import func, select

from app.database import get_session_factory
from app.models.asset import Asset
from app.models.violation import Violation
from app.tasks.celery_app import celery_app


def build_monitoring_snapshot() -> dict[str, int]:
    session_factory = get_session_factory()
    with session_factory() as db:
        return {
            "assets": int(db.scalar(select(func.count(Asset.id))) or 0),
            "violations": int(db.scalar(select(func.count(Violation.id))) or 0),
        }


@celery_app.task(name="app.tasks.monitoring.snapshot", queue="monitoring")
def monitoring_snapshot_task() -> dict[str, int]:
    return build_monitoring_snapshot()

