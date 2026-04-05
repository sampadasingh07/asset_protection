import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import Organisation, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security import create_access_token, hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or f"org-{uuid4().hex[:8]}"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.strip().lower()
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    organisation_name = payload.organisation_name or f"{payload.full_name}'s Organisation"
    slug = _slugify(organisation_name)
    existing_slug = db.scalar(select(Organisation).where(Organisation.slug == slug))
    if existing_slug is not None:
        slug = f"{slug}-{uuid4().hex[:6]}"

    organisation = Organisation(name=organisation_name, slug=slug)
    db.add(organisation)
    db.flush()

    user = User(
        organisation_id=organisation.id,
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        subject=user.id,
        organisation_id=user.organisation_id,
    )
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/token", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        subject=user.id,
        organisation_id=user.organisation_id,
    )
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
