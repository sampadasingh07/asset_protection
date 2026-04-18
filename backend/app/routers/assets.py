import json
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import get_db
from app.deps import (
    get_ai_engine_service,
    get_current_user,
    get_graph_service,
    get_notifier,
    get_settings_dependency,
    get_source_service,
    get_vector_service,
)
from app.models.asset import Asset, AssetMatch
from app.models.user import User
from app.schemas.asset import AssetDetailResponse, AssetMatchResponse, AssetResponse
from app.services.milvus_service import MilvusService
from app.services.neo4j_service import Neo4jService
from app.services.notifier import ConnectionManager
from app.services.source_service import SourceConfidenceService
from app.services.ai_engine_service import AIEngineService
from app.tasks.analysis import dispatch_asset_analysis


router = APIRouter(prefix="/assets", tags=["assets"])


def _parse_vector(raw_value: str | None) -> list[float] | None:
    if raw_value is None or raw_value.strip() == "":
        return None
    try:
        data = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Vector must be a JSON array of numbers.",
        ) from exc

    if not isinstance(data, list) or not all(isinstance(item, (int, float)) for item in data):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Vector must be a JSON array of numbers.",
        )
    return [float(item) for item in data]


def _build_asset_response(asset: Asset, matches: list[AssetMatch]) -> AssetDetailResponse:
    return AssetDetailResponse(
        id=asset.id,
        organisation_id=asset.organisation_id,
        owner_user_id=asset.owner_user_id,
        title=asset.title,
        file_name=asset.file_name,
        file_path=asset.file_path,
        content_type=asset.content_type,
        source_url=asset.source_url,
        status=asset.status,
        fingerprint_vector=asset.fingerprint_vector,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        matches=[AssetMatchResponse.model_validate(match) for match in matches],
    )


@router.post("", response_model=AssetDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    request: Request,
    title: str = Form(...),
    source_url: str | None = Form(default=None),
    vector: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
    current_user: User = Depends(get_current_user),
    milvus_service: MilvusService = Depends(get_vector_service),
    graph_service: Neo4jService = Depends(get_graph_service),
    source_service: SourceConfidenceService = Depends(get_source_service),
    ai_engine_service: AIEngineService = Depends(get_ai_engine_service),
    notifier: ConnectionManager = Depends(get_notifier),
) -> AssetDetailResponse:
    vector_values = _parse_vector(vector)
    settings.upload_path.mkdir(parents=True, exist_ok=True)

    file_name = file.filename if file else f"{uuid4().hex}.bin"
    content_type = file.content_type if file and file.content_type else "application/octet-stream"
    destination = settings.upload_path / f"{uuid4().hex}_{file_name}"

    if file is not None:
        with Path(destination).open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    else:
        destination.write_bytes(b"")

    asset = Asset(
        organisation_id=current_user.organisation_id,
        owner_user_id=current_user.id,
        title=title.strip(),
        file_name=file_name,
        file_path=str(destination),
        content_type=content_type,
        source_url=source_url,
        status="queued",
        fingerprint_vector=vector_values,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    if vector_values:
        milvus_service.upsert(
            asset_id=asset.id,
            organisation_id=asset.organisation_id,
            vector=vector_values,
        )

    alerts = dispatch_asset_analysis(
        asset_id=asset.id,
        session_factory=request.app.state.session_factory,
        milvus_service=milvus_service,
        graph_service=graph_service,
        source_service=source_service,
        ai_engine_service=ai_engine_service,
    )
    for alert in alerts:
        await notifier.broadcast(alert, organisation_id=current_user.organisation_id)

    db.refresh(asset)
    matches = list(
        db.scalars(
            select(AssetMatch)
            .where(AssetMatch.asset_id == asset.id)
            .order_by(desc(AssetMatch.score))
        ).all()
    )
    return _build_asset_response(asset, matches)


@router.get("", response_model=list[AssetResponse])
def list_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AssetResponse]:
    assets = list(
        db.scalars(
            select(Asset)
            .where(Asset.organisation_id == current_user.organisation_id)
            .order_by(desc(Asset.created_at))
        ).all()
    )
    return [AssetResponse.model_validate(asset) for asset in assets]


@router.get("/{asset_id}", response_model=AssetDetailResponse)
def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssetDetailResponse:
    asset = db.scalar(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.organisation_id == current_user.organisation_id,
        )
    )
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")

    matches = list(
        db.scalars(
            select(AssetMatch)
            .where(AssetMatch.asset_id == asset.id)
            .order_by(desc(AssetMatch.score))
        ).all()
    )
    return _build_asset_response(asset, matches)

