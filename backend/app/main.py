from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import get_session_factory, init_db
from app.routers import assets, auth, propagation, search, stats, violations, ws
from app.services.milvus_service import MilvusService
from app.services.neo4j_service import Neo4jService
from app.services.ai_engine_service import AIEngineService
from app.services.notifier import ConnectionManager
from app.services.source_service import SourceConfidenceService
from app.services.runtime_metrics import RuntimeMetrics


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
    application.state.ai_engine_service = AIEngineService()
    application.state.source_service = SourceConfidenceService()
    application.state.notifier = ConnectionManager()
    application.state.runtime_metrics = RuntimeMetrics()

    @application.middleware("http")
    async def collect_runtime_metrics(request, call_next):
        start = perf_counter()
        response = await call_next(request)
        elapsed_ms = (perf_counter() - start) * 1000
        application.state.runtime_metrics.record_request(elapsed_ms)
        return response

    application.include_router(auth.router)
    application.include_router(assets.router)
    application.include_router(search.router)
    application.include_router(violations.router)
    application.include_router(propagation.router)
    application.include_router(stats.router)
    application.include_router(ws.router)

    @application.get("/health")
    def health_check() -> dict[str, object]:
        ai_available = False
        ai_mode = "fallback"
        ai_service = getattr(application.state, "ai_engine_service", None)
        if ai_service is not None:
            try:
                ai_available = bool(ai_service.is_ai_available())
                ai_mode = "full" if ai_available else "fallback"
            except Exception:
                ai_available = False
                ai_mode = "fallback"

        return {
            "status": "ok",
            "app": settings.app_name,
            "environment": settings.environment,
            "task_mode": settings.task_mode,
            "ai_available": ai_available,
            "ai_mode": ai_mode,
        }

    return application


app = create_app()
