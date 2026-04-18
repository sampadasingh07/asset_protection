from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models.user import User
from app.security import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_settings_dependency() -> Settings:
    return get_settings()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    return user


def get_vector_service(request: Request):
    return request.app.state.milvus_service


def get_graph_service(request: Request):
    return request.app.state.graph_service


def get_source_service(request: Request):
    return request.app.state.source_service


def get_ai_engine_service(request: Request):
    return request.app.state.ai_engine_service


def get_notifier(request: Request):
    return request.app.state.notifier

