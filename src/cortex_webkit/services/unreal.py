# src/cortex_webkit/services/unreal.py
"""Async wrapper around cortex-mcp's UEConnection."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AsyncUEConnection:
    """Thread-safe async wrapper over cortex-mcp's synchronous UEConnection."""

    def __init__(self, project_dir: str | None = None):
        self._project_dir = project_dir
        self._conn = None  # Lazy — created on first use to avoid blocking startup

    async def _ensure_connection(self):
        if self._conn is None:
            self._conn = await asyncio.to_thread(self._create_connection)

    def _create_connection(self):
        try:
            import os
            if self._project_dir:
                os.environ["CORTEX_PROJECT_DIR"] = self._project_dir
            from cortex_mcp.tcp_client import UEConnection
            return UEConnection()
        except Exception:
            logger.warning("cortex-mcp not available — UE commands disabled")
            return None

    @property
    def connected(self) -> bool:
        return self._conn is not None and self._conn.connected

    async def send_command(
        self, command: str, params: dict[str, Any] | None = None, timeout: float | None = None
    ) -> dict[str, Any]:
        await self._ensure_connection()
        if self._conn is None:
            return {"success": False, "error": "UE connection not available"}
        return await asyncio.to_thread(
            self._conn.send_command, command, params, timeout=timeout
        )

    async def get_status(self) -> dict[str, Any]:
        await self._ensure_connection()
        if self._conn is None:
            return {"connected": False}
        try:
            result = await asyncio.to_thread(self._conn.send_command, "get_status")
            data = result.get("data", {})
            return {
                "connected": True,
                "port": getattr(self._conn, "_port", None),
                "pid": data.get("pid"),
                "project": data.get("project"),
                "domains": data.get("domains"),
            }
        except Exception:
            return {"connected": False}

    async def reset(self) -> None:
        """Drop cached connection so next call creates a fresh one."""
        self._conn = None

    async def get_capabilities(self) -> dict[str, Any]:
        await self._ensure_connection()
        if self._conn is None:
            return {"domains": []}
        try:
            result = await asyncio.to_thread(self._conn.send_command, "get_capabilities")
            return result.get("data", {"domains": []})
        except Exception:
            return {"domains": []}
