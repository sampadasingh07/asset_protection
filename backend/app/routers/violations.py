from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.violation import EnforcementRecord, Violation
from app.schemas.violation import (
    EnforcementRecordCreate,
    EnforcementRecordResponse,
    ViolationResponse,
    ViolationStatusUpdate,
)


router = APIRouter(prefix="/violations", tags=["violations"])


@router.get("", response_model=list[ViolationResponse])
def list_violations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ViolationResponse]:
    violations = list(
        db.scalars(
            select(Violation)
            .where(Violation.organisation_id == current_user.organisation_id)
            .order_by(desc(Violation.created_at))
        ).all()
    )
    return [ViolationResponse.model_validate(violation) for violation in violations]


@router.get("/{violation_id}", response_model=ViolationResponse)
def get_violation(
    violation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ViolationResponse:
    violation = db.scalar(
        select(Violation).where(
            Violation.id == violation_id,
            Violation.organisation_id == current_user.organisation_id,
        )
    )
    if violation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found.")
    return ViolationResponse.model_validate(violation)


@router.patch("/{violation_id}", response_model=ViolationResponse)
def update_violation_status(
    violation_id: str,
    payload: ViolationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ViolationResponse:
    violation = db.scalar(
        select(Violation).where(
            Violation.id == violation_id,
            Violation.organisation_id == current_user.organisation_id,
        )
    )
    if violation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found.")

    violation.status = payload.status.strip().lower()
    db.add(violation)
    db.commit()
    db.refresh(violation)
    return ViolationResponse.model_validate(violation)


@router.post(
    "/{violation_id}/enforcement",
    response_model=EnforcementRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_enforcement_record(
    violation_id: str,
    payload: EnforcementRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnforcementRecordResponse:
    violation = db.scalar(
        select(Violation).where(
            Violation.id == violation_id,
            Violation.organisation_id == current_user.organisation_id,
        )
    )
    if violation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found.")

    record = EnforcementRecord(
        violation_id=violation.id,
        action_type=payload.action_type.strip(),
        platform_name=payload.platform_name.strip(),
        status=payload.status.strip().lower(),
        external_reference=payload.external_reference,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return EnforcementRecordResponse.model_validate(record)

