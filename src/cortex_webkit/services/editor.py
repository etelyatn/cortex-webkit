# src/cortex_webkit/services/editor.py
"""EditorLifecycleManager: state machine for Unreal Editor process lifecycle."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import subprocess
import threading
import time
from typing import Literal

from cortex_webkit.services.event_bus import EventBus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State machine definition
# ---------------------------------------------------------------------------

EditorLifecycle = Literal[
    "disconnected",
    "starting",
    "connected",
    "stopping",
    "restarting",
    "timed_out",
    "error",
]

VALID_TRANSITIONS: dict[str, list[str]] = {
    "disconnected": ["starting"],
    "starting":     ["connected", "timed_out", "error", "disconnected"],
    "connected":    ["stopping", "restarting", "error", "disconnected"],
    "stopping":     ["disconnected", "error"],
    "restarting":   ["connected", "timed_out", "error", "disconnected"],
    "timed_out":    ["starting", "disconnected"],
    "error":        ["starting", "disconnected"],
}

# States from which start() / restart() set _started_at
_STARTED_AT_CLEARED_ON = {"connected", "disconnected", "error", "timed_out"}

# States that clear _error when transitioning away
_ERROR_STATES = {"error", "timed_out"}


class EditorLifecycleManager:
    """Manages the Unreal Editor process lifecycle via a state machine."""

    def __init__(self, event_bus: EventBus, project_dir: str | None = None):
        self._event_bus = event_bus
        self._project_dir = project_dir or os.environ.get("CORTEX_PROJECT_DIR", "")

        # State
        self._state: str = "disconnected"
        self._started_at: int | None = None
        self._error: str | None = None
        self._port: int | None = None
        self._pid: int | None = None
        self._project: str | None = None

        # Background task management
        self._bg_task: asyncio.Task | None = None
        self._cancel_event: threading.Event = threading.Event()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> str:
        return self._state

    @property
    def started_at(self) -> int | None:
        return self._started_at

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def port(self) -> int | None:
        return self._port

    @property
    def pid(self) -> int | None:
        return self._pid

    @property
    def project(self) -> str | None:
        return self._project

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def _transition(self, to: str, meta: dict | None = None) -> None:
        """Validate and apply a state transition, then emit an event."""
        allowed = VALID_TRANSITIONS.get(self._state, [])
        if to not in allowed:
            logger.debug(
                "EditorLifecycleManager: ignoring invalid transition %s -> %s",
                self._state,
                to,
            )
            return

        meta = meta or {}

        # Clear error when leaving an error/timed_out state
        if self._state in _ERROR_STATES:
            self._error = None

        # Clear started_at when landing in certain states
        if to in _STARTED_AT_CLEARED_ON:
            self._started_at = None

        # Apply transition
        self._state = to

        # Update metadata fields from meta dict
        if to == "connected":
            self._port = meta.get("port")
            self._pid = meta.get("pid")
            self._project = meta.get("project")
        elif to in {"disconnected", "stopping"}:
            # Keep port/pid/project until explicitly cleared (they may be useful for reconnect)
            pass
        elif to in {"error", "timed_out"}:
            self._error = meta.get("error")

        # Build and emit event
        event = self._build_event(to, meta)
        # Fire-and-forget: schedule on the running event loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._event_bus.emit(event))
        except RuntimeError:
            # No running loop (e.g. called from sync context during init)
            pass

    def _build_event(self, state: str, meta: dict) -> dict:
        """Construct the editor.lifecycle event payload."""
        event: dict = {"type": "editor.lifecycle", "state": state}
        if state in {"starting", "restarting"} and self._started_at is not None:
            event["started_at"] = self._started_at
        elif state == "connected":
            if self._port is not None:
                event["port"] = self._port
            if self._pid is not None:
                event["pid"] = self._pid
            if self._project is not None:
                event["project"] = self._project
        elif state in {"error", "timed_out"} and self._error is not None:
            event["error"] = self._error
        return event

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def start(self) -> dict:
        """Start editor. Raises ValueError if current state is invalid."""
        valid_from = {"disconnected", "timed_out", "error"}
        if self._state not in valid_from:
            raise ValueError(
                f"Cannot start from state '{self._state}'. "
                f"Valid states: {sorted(valid_from)}"
            )

        self._started_at = int(time.time())
        self._cancel_event = threading.Event()
        self._transition("starting")

        self._bg_task = asyncio.create_task(self._run_start())
        return {"state": "starting", "started_at": self._started_at}

    async def stop(self) -> dict:
        """Stop editor. Raises ValueError if current state is invalid."""
        valid_from = {"connected", "starting", "restarting"}
        if self._state not in valid_from:
            raise ValueError(
                f"Cannot stop from state '{self._state}'. "
                f"Valid states: {sorted(valid_from)}"
            )

        self._cancel_event.set()
        self._transition("stopping")

        self._bg_task = asyncio.create_task(self._run_stop())
        return {"state": "stopping"}

    async def restart(self) -> dict:
        """Restart editor. Raises ValueError if current state is invalid."""
        valid_from = {"connected"}
        if self._state not in valid_from:
            raise ValueError(
                f"Cannot restart from state '{self._state}'. "
                f"Valid states: {sorted(valid_from)}"
            )

        self._started_at = int(time.time())
        self._cancel_event = threading.Event()
        self._transition("restarting")

        self._bg_task = asyncio.create_task(self._run_restart())
        return {"state": "restarting", "started_at": self._started_at}

    def get_status(self) -> dict:
        """Return current state snapshot."""
        return {
            "state": self._state,
            "started_at": self._started_at,
            "error": self._error,
            "port": self._port,
            "pid": self._pid,
            "project": self._project,
        }

    async def initialize(self) -> None:
        """Startup probe: check for existing CortexPort-*.txt, verify TCP."""
        if not self._project_dir:
            logger.debug("EditorLifecycleManager.initialize: no project_dir, skipping probe")
            return

        saved_dir = pathlib.Path(self._project_dir) / "Saved"
        port_files = list(saved_dir.glob("CortexPort-*.txt"))
        if not port_files:
            return

        # Try to find a responsive editor
        for port_file in port_files:
            try:
                content = port_file.read_text().strip()
                if not content.startswith("{"):
                    continue
                data = json.loads(content)
                port = int(data["port"])
                pid = data.get("pid")
                project_path = data.get("project_path", "")
                project_name = pathlib.Path(project_path).stem if project_path else None

                # Verify via TCP
                verified = await asyncio.to_thread(
                    self._verify_tcp_connection, port
                )
                if verified:
                    self._port = port
                    self._pid = pid
                    self._project = project_name
                    self._state = "connected"
                    await self._event_bus.emit(self._build_event("connected", {}))
                    logger.info(
                        "EditorLifecycleManager: found running editor on port %d (pid=%s)",
                        port,
                        pid,
                    )
                    return
            except (json.JSONDecodeError, ValueError, OSError, KeyError):
                continue

        logger.debug("EditorLifecycleManager.initialize: found stale port file(s), staying disconnected")

    async def shutdown(self) -> None:
        """Cleanup: cancel background task."""
        self._cancel_event.set()
        if self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()
            try:
                await self._bg_task
            except (asyncio.CancelledError, Exception):
                pass

    # ------------------------------------------------------------------
    # Background tasks
    # ------------------------------------------------------------------

    async def _run_start(self) -> None:
        """Background: launch editor, wait for port file, verify TCP."""
        try:
            result = await asyncio.to_thread(
                self._launch_editor_sync,
                120,
                self._cancel_event,
                None,  # no current pid — fresh start
            )
            self._apply_launch_result(result)
        except asyncio.CancelledError:
            self._transition("disconnected")
        except Exception as exc:
            self._transition("error", {"error": str(exc)})

    async def _run_restart(self) -> None:
        """Background: shutdown existing editor, relaunch, verify TCP."""
        try:
            result = await asyncio.to_thread(
                self._launch_editor_sync,
                120,
                self._cancel_event,
                self._pid,  # current pid for shutdown
            )
            self._apply_launch_result(result)
        except asyncio.CancelledError:
            self._transition("disconnected")
        except Exception as exc:
            self._transition("error", {"error": str(exc)})

    async def _run_stop(self) -> None:
        """Background: send shutdown command, transition to disconnected."""
        try:
            await asyncio.to_thread(self._shutdown_editor_sync)
            self._transition("disconnected")
        except asyncio.CancelledError:
            self._transition("disconnected")
        except Exception as exc:
            self._transition("error", {"error": str(exc)})

    def _apply_launch_result(self, result: dict) -> None:
        """Apply the result from _launch_editor_sync to the state machine."""
        if result.get("cancelled"):
            self._transition("disconnected")
        elif result.get("error") == "timed_out":
            self._transition("timed_out", {"error": result.get("message", "Editor did not start in time")})
        elif result.get("error"):
            self._transition("error", {"error": result["error"]})
        else:
            self._transition("connected", {
                "port": result.get("port"),
                "pid": result.get("pid"),
                "project": result.get("project"),
            })

    # ------------------------------------------------------------------
    # Synchronous helpers (run in thread via asyncio.to_thread)
    # ------------------------------------------------------------------

    def _launch_editor_sync(
        self,
        timeout: int = 120,
        cancel: threading.Event | None = None,
        current_pid: int | None = None,
    ) -> dict:
        """Launch the Unreal Editor and wait for it to come online.

        Mirrors the logic of do_restart_editor from composites.py, but
        inlined so cortex-webkit doesn't depend on the MCP tools directory.
        """
        start_time = time.monotonic()

        project_dir = self._project_dir
        if not project_dir:
            return {"error": "CORTEX_PROJECT_DIR not set"}

        saved_dir = pathlib.Path(project_dir) / "Saved"

        # Discover project path from existing port file
        project_path: str | None = None
        for pf in saved_dir.glob("CortexPort-*.txt"):
            try:
                content = pf.read_text().strip()
                if content.startswith("{"):
                    data = json.loads(content)
                    found_path = data.get("project_path")
                    if found_path:
                        project_path = found_path
                        if not current_pid:
                            current_pid = data.get("pid")
                        break
            except (json.JSONDecodeError, OSError):
                continue

        # Fall back: look for .uproject in project_dir
        if not project_path:
            candidates = list(pathlib.Path(project_dir).glob("*.uproject"))
            if candidates:
                project_path = str(candidates[0])

        if not project_path:
            return {
                "error": (
                    "Cannot determine .uproject path. "
                    "Ensure CORTEX_PROJECT_DIR points to an Unreal project."
                )
            }

        port_file_pattern = f"CortexPort-{current_pid}.txt" if current_pid else None

        # Phase 1: shutdown existing editor (restart scenario)
        if current_pid is not None:
            try:
                import psutil
                if psutil.pid_exists(current_pid):
                    # Send shutdown via TCP (best-effort)
                    try:
                        self._send_tcp_command(self._port or 8742, "core.shutdown", {"force": True})
                    except Exception:
                        pass

                    remaining = timeout - (time.monotonic() - start_time)
                    shutdown_deadline = time.monotonic() + min(30.0, max(0.0, remaining))
                    while time.monotonic() < shutdown_deadline:
                        if not psutil.pid_exists(current_pid):
                            break
                        time.sleep(2)
                    else:
                        if psutil.pid_exists(current_pid):
                            return {
                                "error": "Shutdown timeout",
                                "pid": current_pid,
                                "message": "Editor did not exit within 30s",
                            }
            except ImportError:
                # psutil not available — skip process check
                pass

        if cancel and cancel.is_set():
            return {"cancelled": True}

        # Remove old port file
        if current_pid:
            old_port_file = saved_dir / f"CortexPort-{current_pid}.txt"
            try:
                old_port_file.unlink(missing_ok=True)
            except OSError:
                pass

        # Phase 2: launch editor
        engine_path = os.environ.get("UE_56_PATH", "")
        if not engine_path:
            return {"error": "UE_56_PATH not set - cannot launch editor"}

        editor_exe = (
            pathlib.Path(engine_path)
            / "Engine"
            / "Binaries"
            / "Win64"
            / "UnrealEditor.exe"
        )

        subprocess.Popen(
            [
                str(editor_exe),
                project_path,
                "-nosplash",
                "-nopause",
                "-AutoDeclinePackageRecovery",
                '-ExecCmds=Mainframe.ShowRestoreAssetsPromptOnStartup 0',
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if cancel and cancel.is_set():
            return {"cancelled": True}

        # Phase 3: wait for new port file
        remaining = timeout - (time.monotonic() - start_time)
        launch_deadline = time.monotonic() + max(0.0, remaining)
        new_port: int | None = None
        new_pid: int | None = None

        while time.monotonic() < launch_deadline:
            time.sleep(3)
            if cancel and cancel.is_set():
                return {"cancelled": True}
            for port_file in saved_dir.glob("CortexPort-*.txt"):
                if port_file_pattern and port_file.name == port_file_pattern:
                    continue
                try:
                    content = port_file.read_text().strip()
                    if content.startswith("{"):
                        data = json.loads(content)
                        found_pid = data.get("pid")
                        if found_pid and found_pid != current_pid:
                            new_pid = found_pid
                            new_port = int(data["port"])
                            break
                except (json.JSONDecodeError, ValueError, OSError, KeyError):
                    continue
            if new_port is not None:
                break

        if new_port is None:
            return {
                "error": "timed_out",
                "message": f"Editor did not start within {timeout}s",
            }

        if cancel and cancel.is_set():
            return {"cancelled": True}

        # Phase 4: verify via TCP
        try:
            status = self._send_tcp_command(new_port, "get_status")
            project_name = pathlib.Path(project_path).stem
            return {
                "port": new_port,
                "pid": new_pid,
                "project": project_name,
                "domains": status.get("data", {}).get("subsystems", {}),
            }
        except Exception as exc:
            return {
                "error": f"Verification failed: {exc}",
                "port": new_port,
                "pid": new_pid,
            }

    def _shutdown_editor_sync(self) -> dict:
        """Send core.shutdown to the editor; handle graceful socket close."""
        port = self._port
        if port is None:
            return {"message": "No port known — nothing to shut down"}
        try:
            return self._send_tcp_command(port, "core.shutdown", {"force": True})
        except (ConnectionError, RuntimeError, OSError):
            return {"message": "Shutdown initiated", "note": "Connection closed as expected"}

    @staticmethod
    def _send_tcp_command(port: int, command: str, params: dict | None = None) -> dict:
        """Send a single JSON command over TCP and return the parsed response."""
        import socket

        payload = json.dumps({"command": command, "params": params or {}}) + "\n"
        with socket.create_connection(("127.0.0.1", port), timeout=10) as sock:
            sock.sendall(payload.encode())
            # Read until newline
            buf = b""
            while b"\n" not in buf:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
        return json.loads(buf.split(b"\n")[0])

    @staticmethod
    def _verify_tcp_connection(port: int) -> bool:
        """Return True if the editor responds to get_status on the given port."""
        try:
            EditorLifecycleManager._send_tcp_command(port, "get_status")
            return True
        except Exception:
            return False
