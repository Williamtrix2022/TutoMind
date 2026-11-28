import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from app.api import analytics, auth, documents, health, tutor
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.db.session import get_session_factory
from app.services.ingestion import STARTUP_GRACE, fail_stale_documents

logger = logging.getLogger(__name__)


def _recover_abandoned_documents() -> None:
    with get_session_factory()() as session:
        count = fail_stale_documents(session, datetime.now(UTC), STARTUP_GRACE)
        session.commit()
    if count:
        logger.warning("Marked %d document(s) interrupted by a restart as failed", count)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await run_in_threadpool(_recover_abandoned_documents)
    except Exception:
        # The server must come up even if the database is not reachable yet.
        logger.exception("Could not check for documents interrupted by a restart")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(documents.router)
    app.include_router(tutor.router)
    app.include_router(analytics.router)
    return app


app = create_app()
