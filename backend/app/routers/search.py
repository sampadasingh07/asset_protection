from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import get_db
from app.deps import (
    get_current_user,
    get_settings_dependency,
    get_source_service,
    get_vector_service,
)
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset import SearchHitResponse, SearchRequest
from app.services.milvus_service import MilvusService
from app.services.source_service import SourceConfidenceService


router = APIRouter(prefix="/search", tags=["search"])


def _fallback_db_search(
    *,
    db: Session,
    vector: list[float],
    organisation_id: str,
    limit: int,
    exclude_asset_id: str | None,
    source_service: SourceConfidenceService,
    milvus_service: MilvusService,
) -> list[SearchHitResponse]:
    assets = list(
        db.scalars(
            select(Asset).where(
                Asset.organisation_id == organisation_id,
                Asset.id != exclude_asset_id if exclude_asset_id else True,
            )
        ).all()
    )
    scored_assets: list[tuple[Asset, float]] = []
    for asset in assets:
        if not asset.fingerprint_vector:
            continue
        score = milvus_service.cosine_similarity(vector, asset.fingerprint_vector)
        if score <= 0:
            continue
        scored_assets.append((asset, score))

    scored_assets.sort(key=lambda item: item[1], reverse=True)
    return [
        SearchHitResponse(
            asset_id=asset.id,
            title=asset.title,
            score=round(score, 6),
            confidence_label=source_service.label_for_score(score),
            source_url=asset.source_url,
        )
        for asset, score in scored_assets[:limit]
    ]


@router.post("", response_model=list[SearchHitResponse])
def search_assets(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
    current_user: User = Depends(get_current_user),
    milvus_service: MilvusService = Depends(get_vector_service),
    source_service: SourceConfidenceService = Depends(get_source_service),
) -> list[SearchHitResponse]:
    vector = payload.vector
    if vector is None and payload.asset_id is not None:
        vector = milvus_service.get_vector(payload.asset_id)
        if vector is None:
            asset = db.get(Asset, payload.asset_id)
            if asset is not None:
                vector = asset.fingerprint_vector

    if vector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vector available for this search.",
        )

    results = milvus_service.search(
        vector=vector,
        limit=min(payload.limit, settings.max_search_results),
        organisation_id=current_user.organisation_id,
        exclude_asset_id=payload.asset_id,
    )
    if not results:
        return _fallback_db_search(
            db=db,
            vector=vector,
            organisation_id=current_user.organisation_id,
            limit=min(payload.limit, settings.max_search_results),
            exclude_asset_id=payload.asset_id,
            source_service=source_service,
            milvus_service=milvus_service,
        )

    asset_ids = [str(item["asset_id"]) for item in results]
    assets = list(db.scalars(select(Asset).where(Asset.id.in_(asset_ids))).all())
    asset_map = {asset.id: asset for asset in assets}

    response: list[SearchHitResponse] = []
    for result in results:
        asset = asset_map.get(str(result["asset_id"]))
        if asset is None:
            continue
        score = float(result["score"])
        response.append(
            SearchHitResponse(
                asset_id=asset.id,
                title=asset.title,
                score=score,
                confidence_label=source_service.label_for_score(score),
                source_url=asset.source_url,
            )
        )
    return response
