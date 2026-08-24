import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.internal.routes import whatsapp as internal_whatsapp
from app.api.v1.routes import (
    admin,
    auth,
    consent,
    contacts,
    exports,
    groups,
    keywords,
    polls,
    scoring,
    session,
)
from app.core.bridge_process import get_bridge_manager
from app.core.config import get_settings
from app.core.logging_setup import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    settings = get_settings()
    bridge = get_bridge_manager()
    if settings.whatsapp_bridge_enabled:
        try:
            bridge.start()
        except Exception:
            logger.exception("Failed to start WhatsApp bridge on startup")
    yield
    bridge.stop()


def create_app() -> FastAPI:
    settings = get_settings()

    insecure = settings.insecure_defaults_still_in_use()
    if insecure:
        raise RuntimeError(
            "Refusing to start: these secrets are still at their .env.example placeholder value "
            f"(anyone can read the placeholder from the public repo): {insecure}. "
            "Set real random values for them in .env before running."
        )

    app = FastAPI(title="wp-bot", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition", "X-Above-Threshold-Count", "X-Row-Count"],
    )

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")
    app.include_router(session.router, prefix="/api/v1")
    app.include_router(groups.router, prefix="/api/v1")
    app.include_router(consent.router, prefix="/api/v1")
    app.include_router(contacts.router, prefix="/api/v1")
    app.include_router(polls.router, prefix="/api/v1")
    app.include_router(scoring.router, prefix="/api/v1")
    app.include_router(keywords.router, prefix="/api/v1")
    app.include_router(exports.router, prefix="/api/v1")
    app.include_router(internal_whatsapp.router)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
