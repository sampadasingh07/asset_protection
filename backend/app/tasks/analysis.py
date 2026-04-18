from app.config import get_settings
from app.database import get_session_factory
from app.models.asset import Asset, AssetMatch
from app.models.violation import Violation
from app.services.milvus_service import MilvusService
from app.services.neo4j_service import Neo4jService
from app.services.source_service import SourceConfidenceService
from app.services.ai_engine_service import AIEngineService
from app.tasks.celery_app import celery_app


def _fallback_matches_from_db(
    *,
    db,
    asset: Asset,
    vector: list[float],
    milvus_service: MilvusService,
) -> list[dict[str, object]]:
    candidates = []
    for candidate in db.query(Asset).filter(Asset.organisation_id == asset.organisation_id).all():
        if candidate.id == asset.id or not candidate.fingerprint_vector:
            continue
        score = milvus_service.cosine_similarity(vector, candidate.fingerprint_vector)
        if score <= 0:
            continue
        candidates.append({"asset_id": candidate.id, "score": round(score, 6)})
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates


def run_asset_analysis(
    *,
    asset_id: str,
    session_factory,
    milvus_service: MilvusService,
    graph_service: Neo4jService,
    source_service: SourceConfidenceService,
    ai_engine_service: AIEngineService,
) -> list[dict[str, object]]:
    settings = get_settings()
    alerts: list[dict[str, object]] = []

    with session_factory() as db:
        asset = db.get(Asset, asset_id)
        if asset is None:
            return []

        asset.status = "extracting_keyframes"
        db.add(asset)
        db.commit()
        db.refresh(asset)

        graph_service.upsert_asset_node(
            asset_id=asset.id,
            title=asset.title,
            organisation_id=asset.organisation_id,
        )

        vector = asset.fingerprint_vector or milvus_service.get_vector(asset.id)
        morph_scores = {
            "morph_score": 0.0,
            "gan_score": 0.0,
            "freq_score": 0.0,
            "temporal_score": 0.0,
            "verdict": "clean",
        }

        if not vector and asset.file_path:
            asset.status = "fingerprinting"
            db.add(asset)
            db.commit()
            db.refresh(asset)

            vector = ai_engine_service.generate_fingerprint(asset.file_path)
            morph_scores = ai_engine_service.score_morph(asset.file_path)

            if vector:
                asset.fingerprint_vector = vector
                db.add(asset)
                db.commit()
                db.refresh(asset)

        if not vector:
            asset.status = "failed"
            db.add(asset)
            db.commit()
            return []

        asset.status = "indexing_milvus"
        db.add(asset)
        db.commit()
        db.refresh(asset)

        milvus_service.upsert(
            asset_id=asset.id,
            organisation_id=asset.organisation_id,
            vector=vector,
        )

        matches = milvus_service.search(
            vector=vector,
            limit=settings.max_search_results,
            organisation_id=asset.organisation_id,
            exclude_asset_id=asset.id,
        )
        if not matches:
            matches = _fallback_matches_from_db(
                db=db,
                asset=asset,
                vector=vector,
                milvus_service=milvus_service,
            )[: settings.max_search_results]

        for result in matches:
            matched_asset = db.get(Asset, str(result["asset_id"]))
            if matched_asset is None:
                continue

            score = float(result["score"])
            match = AssetMatch(
                asset_id=asset.id,
                matched_asset_id=matched_asset.id,
                score=score,
                confidence_label=source_service.label_for_score(score),
                source_url=matched_asset.source_url,
            )
            db.add(match)
            db.flush()

            graph_service.upsert_asset_node(
                asset_id=matched_asset.id,
                title=matched_asset.title,
                organisation_id=matched_asset.organisation_id,
            )
            graph_service.link_assets(
                source_asset_id=matched_asset.id,
                target_asset_id=asset.id,
                relation="similarity",
                score=score,
            )

            if score >= settings.alert_similarity_threshold:
                violation = Violation(
                    organisation_id=asset.organisation_id,
                    asset_id=asset.id,
                    match_id=match.id,
                    severity=source_service.severity_for_score(score),
                    status="open",
                    confidence=score,
                    summary=source_service.summary_for_match(
                        asset_title=asset.title,
                        matched_asset_title=matched_asset.title,
                        score=score,
                    ),
                    source_url=matched_asset.source_url,
                )
                db.add(violation)
                db.flush()

                alerts.append(
                    {
                        "event": "violation.detected",
                        "organisation_id": asset.organisation_id,
                        "asset_id": asset.id,
                        "matched_asset_id": matched_asset.id,
                        "violation_id": violation.id,
                        "score": score,
                        "morph_score": morph_scores.get("morph_score", 0.0),
                        "severity": violation.severity,
                        "summary": violation.summary,
                        "source_url": matched_asset.source_url,
                    }
                )

        asset.status = "ready"
        db.add(asset)
        db.commit()
        return alerts


def dispatch_asset_analysis(
    *,
    asset_id: str,
    session_factory,
    milvus_service: MilvusService,
    graph_service: Neo4jService,
    source_service: SourceConfidenceService,
    ai_engine_service: AIEngineService,
) -> list[dict[str, object]]:
    settings = get_settings()
    if settings.task_mode.lower() == "celery":
        analyze_asset_task.delay(asset_id)
        return []

    return run_asset_analysis(
        asset_id=asset_id,
        session_factory=session_factory,
        milvus_service=milvus_service,
        graph_service=graph_service,
        source_service=source_service,
        ai_engine_service=ai_engine_service,
    )


@celery_app.task(name="app.tasks.analysis.analyze_asset", queue="analysis")
def analyze_asset_task(asset_id: str) -> dict[str, object]:
    local_milvus = MilvusService()
    local_graph = Neo4jService()
    local_source = SourceConfidenceService()
    local_ai_engine = AIEngineService()
    alerts = run_asset_analysis(
        asset_id=asset_id,
        session_factory=get_session_factory(),
        milvus_service=local_milvus,
        graph_service=local_graph,
        source_service=local_source,
        ai_engine_service=local_ai_engine,
    )
    return {"asset_id": asset_id, "alerts_sent": len(alerts)}
