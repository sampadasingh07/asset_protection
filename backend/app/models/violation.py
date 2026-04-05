from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Violation(TimestampMixin, Base):
    __tablename__ = "violations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organisation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("asset_matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    severity: Mapped[str] = mapped_column(String(40), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="open")
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=True)


class EnforcementRecord(TimestampMixin, Base):
    __tablename__ = "enforcement_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    violation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("violations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    platform_name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    external_reference: Mapped[str] = mapped_column(String(255), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
