# src/cortex_webkit/app.py
"""FastAPI application factory."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pathlib

from cortex_webkit.config import CortexWebConfig


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — init services, cleanup sessions."""
    config: CortexWebConfig = app.state.config

    # Import here to avoid circular imports
    from cortex_webkit.session import SessionManager
    from cortex_webkit.services.unreal import AsyncUEConnection

    ue_conn = AsyncUEConnection(project_dir=config.ue_project_dir)
    session_mgr = SessionManager(config=config)

    app.state.ue_connection = ue_conn
    app.state.session_manager = session_mgr
    app.state.settings = {
        "model": "claude-sonnet-4-6",
        "effort": "medium",
        "workflow": "direct",
        "access_mode": "full",
        "directive": "",
    }

    yield

    await session_mgr.shutdown_all()


def create_app(config: CortexWebConfig | None = None) -> FastAPI:
    if config is None:
        config = CortexWebConfig()

    app = FastAPI(
        title="Cortex Web Kit",
        version="0.1.0",
        lifespan=_lifespan,
    )
    app.state.config = config

    # CORS for dev (Vite on :5173)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    from cortex_webkit.api.status import router as status_router
    from cortex_webkit.api.commands import router as commands_router
    from cortex_webkit.api.sessions import router as sessions_router
    from cortex_webkit.api.settings import router as settings_router

    app.include_router(status_router, prefix="/api")
    app.include_router(commands_router, prefix="/api")
    app.include_router(sessions_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")

    # Register WebSocket routes
    from cortex_webkit.ws.chat import router as chat_ws_router
    from cortex_webkit.ws.events import router as events_ws_router

    app.include_router(chat_ws_router)
    app.include_router(events_ws_router)

    # Serve built frontend (if dist exists)
    frontend_dist = pathlib.Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True))

    return app
