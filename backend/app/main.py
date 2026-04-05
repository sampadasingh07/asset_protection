from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import get_session_factory, init_db
from app.routers import assets, auth, propagation, search, stats, violations, ws
from app.services.milvus_service import MilvusService
from app.services.neo4j_service import Neo4jService
from app.services.notifier import ConnectionManager
from app.services.source_service import SourceConfidenceService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.state.settings = settings
    application.state.session_factory = get_session_factory()
    application.state.milvus_service = MilvusService()
    application.state.graph_service = Neo4jService()
    application.state.source_service = SourceConfidenceService()
    application.state.notifier = ConnectionManager()

    application.include_router(auth.router)
    application.include_router(assets.router)
    application.include_router(search.router)
    application.include_router(violations.router)
    application.include_router(propagation.router)
    application.include_router(stats.router)
    application.include_router(ws.router)

    @application.get("/health")
    def health_check() -> dict[str, object]:
        return {
            "status": "ok",
            "app": settings.app_name,
            "environment": settings.environment,
            "task_mode": settings.task_mode,
        }

    return application


app = create_app()
