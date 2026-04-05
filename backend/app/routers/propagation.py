from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_graph_service
from app.models.asset import Asset
from app.models.user import User
from app.schemas.stats import PropagationResponse
from app.services.neo4j_service import Neo4jService


router = APIRouter(prefix="/propagation", tags=["propagation"])


@router.get("/{asset_id}", response_model=PropagationResponse)
def get_asset_propagation(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    graph_service: Neo4jService = Depends(get_graph_service),
) -> PropagationResponse:
    asset = db.scalar(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.organisation_id == current_user.organisation_id,
        )
    )
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")

    graph_service.upsert_asset_node(
        asset_id=asset.id,
        title=asset.title,
        organisation_id=asset.organisation_id,
    )
    return PropagationResponse.model_validate(graph_service.get_propagation(asset.id))

