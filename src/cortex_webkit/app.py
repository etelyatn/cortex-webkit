# src/cortex_webkit/app.py
"""FastAPI application factory."""

import re
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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
    from cortex_webkit.services.event_bus import EventBus
    from cortex_webkit.services.editor import EditorLifecycleManager

    ue_conn = AsyncUEConnection(project_dir=config.ue_project_dir)
    session_mgr = SessionManager(config=config)
    event_bus = EventBus()
    editor_lifecycle = EditorLifecycleManager(
        event_bus=event_bus,
        project_dir=config.ue_project_dir,
        async_ue_conn=ue_conn,
    )
    await editor_lifecycle.initialize()  # Startup probe

    app.state.ue_connection = ue_conn
    app.state.session_manager = session_mgr
    app.state.event_bus = event_bus
    app.state.editor_lifecycle = editor_lifecycle
    app.state.settings = {
        "model": "claude-sonnet-4-6",
        "effort": "medium",
        "workflow": "direct",
        "access_mode": "full",
        "directive": "",
    }

    yield

    await editor_lifecycle.shutdown()
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
    from cortex_webkit.api.editor import router as editor_router

    app.include_router(status_router, prefix="/api")
    app.include_router(commands_router, prefix="/api")
    app.include_router(sessions_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(editor_router, prefix="/api")

    # Register WebSocket routes
    from cortex_webkit.ws.chat import router as chat_ws_router
    from cortex_webkit.ws.events import router as events_ws_router

    app.include_router(chat_ws_router)
    app.include_router(events_ws_router)

    # Serve built frontend (if dist exists)
    frontend_dist = pathlib.Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.is_dir():
        # Serve index.html with injected auth token — must be registered before StaticFiles
        @app.get("/", include_in_schema=False)
        async def serve_index(request: Request):
            dist_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
            index_path = dist_dir / "index.html"
            if not index_path.exists():
                return HTMLResponse("<h1>Frontend not built. Run scripts/build.sh</h1>", status_code=404)
            html = index_path.read_text(encoding="utf-8")
            token = request.app.state.config.auth_token
            script = f'<script>window.__CORTEX_TOKEN__ = "{token}";</script>'
            html = re.sub(r"</head>", f"{script}</head>", html, count=1)
            return HTMLResponse(html)

        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True))

    return app
