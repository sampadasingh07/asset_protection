from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def generate_uuid() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

