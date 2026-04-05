from celery import Celery

from app.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()
    celery = Celery(
        "verilens",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        task_always_eager=settings.task_mode.lower() == "eager",
        timezone="UTC",
    )
    return celery


celery_app = create_celery_app()

