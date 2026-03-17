# tests/test_editor_lifecycle_manager.py
"""Unit tests for EditorLifecycleManager — TDD, Red-Green-Refactor."""

import asyncio
import threading
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cortex_webkit.services.editor import EditorLifecycleManager
from cortex_webkit.services.event_bus import EventBus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_manager(project_dir: str | None = None) -> EditorLifecycleManager:
    bus = EventBus()
    return EditorLifecycleManager(event_bus=bus, project_dir=project_dir)


# ---------------------------------------------------------------------------
# 1. Initial state
# ---------------------------------------------------------------------------

def test_initial_state_is_disconnected():
    mgr = make_manager()
    assert mgr.state == "disconnected"
    assert mgr.started_at is None
    assert mgr.error is None
    assert mgr.port is None
    assert mgr.pid is None
    assert mgr.project is None


# ---------------------------------------------------------------------------
# 2. start() transitions to 'starting'
# ---------------------------------------------------------------------------

async def test_start_transitions_to_starting():
    mgr = make_manager()

    # Patch _run_start so it doesn't actually launch anything
    with patch.object(mgr, "_run_start", new_callable=AsyncMock):
        result = await mgr.start()

    assert result["state"] == "starting"
    assert isinstance(result["started_at"], int)
    assert mgr.state == "starting"
    assert mgr.started_at == result["started_at"]


# ---------------------------------------------------------------------------
# 3. start() raises ValueError when not in valid state
# ---------------------------------------------------------------------------

async def test_start_raises_when_not_disconnected():
    mgr = make_manager()
    # Force into 'connected' state via internal transition
    mgr._state = "connected"

    with pytest.raises(ValueError, match="connected"):
        await mgr.start()


# ---------------------------------------------------------------------------
# 4. stop() raises ValueError when not connected/starting/restarting
# ---------------------------------------------------------------------------

async def test_stop_raises_when_not_connected():
    mgr = make_manager()
    # state is 'disconnected'
    with pytest.raises(ValueError):
        await mgr.stop()


# ---------------------------------------------------------------------------
# 5. restart() raises ValueError when not connected
# ---------------------------------------------------------------------------

async def test_restart_raises_when_not_connected():
    mgr = make_manager()
    with pytest.raises(ValueError):
        await mgr.restart()


# ---------------------------------------------------------------------------
# 6. _transition clears error when leaving error state
# ---------------------------------------------------------------------------

async def test_transition_clears_error_on_exit():
    mgr = make_manager()
    mgr._state = "error"
    mgr._error = "something went wrong"

    # Transition from error -> starting is valid
    mgr._transition("starting", {"started_at": int(time.time())})

    assert mgr.error is None
    assert mgr.state == "starting"


# ---------------------------------------------------------------------------
# 7. Invalid transition is silently ignored
# ---------------------------------------------------------------------------

async def test_invalid_transition_is_ignored():
    mgr = make_manager()
    # disconnected -> connected is not in VALID_TRANSITIONS
    mgr._transition("connected")
    # State should remain disconnected; no exception
    assert mgr.state == "disconnected"


# ---------------------------------------------------------------------------
# 8. get_status returns current snapshot
# ---------------------------------------------------------------------------

async def test_get_status_returns_snapshot():
    mgr = make_manager()
    status = mgr.get_status()

    assert status["state"] == "disconnected"
    assert status["started_at"] is None
    assert status["error"] is None
    assert status["port"] is None
    assert status["pid"] is None
    assert status["project"] is None


# ---------------------------------------------------------------------------
# 9. start() emits editor.lifecycle event to EventBus
# ---------------------------------------------------------------------------

async def test_start_emits_lifecycle_event():
    bus = EventBus()
    q = bus.subscribe()
    mgr = EditorLifecycleManager(event_bus=bus)

    with patch.object(mgr, "_run_start", new_callable=AsyncMock):
        await mgr.start()

    # Yield to let the scheduled emit coroutine run
    await asyncio.sleep(0)

    assert not q.empty()
    event = q.get_nowait()
    assert event["type"] == "editor.lifecycle"
    assert event["state"] == "starting"
    assert "started_at" in event


# ---------------------------------------------------------------------------
# 10. stop() from connected transitions to stopping and emits event
# ---------------------------------------------------------------------------

async def test_stop_from_connected_transitions_to_stopping():
    bus = EventBus()
    q = bus.subscribe()
    mgr = EditorLifecycleManager(event_bus=bus)
    mgr._state = "connected"

    with patch.object(mgr, "_run_stop", new_callable=AsyncMock):
        result = await mgr.stop()

    await asyncio.sleep(0)

    assert result["state"] == "stopping"
    assert mgr.state == "stopping"
    event = q.get_nowait()
    assert event["type"] == "editor.lifecycle"
    assert event["state"] == "stopping"


# ---------------------------------------------------------------------------
# 11. restart() from connected transitions to restarting
# ---------------------------------------------------------------------------

async def test_restart_from_connected_transitions_to_restarting():
    bus = EventBus()
    q = bus.subscribe()
    mgr = EditorLifecycleManager(event_bus=bus)
    mgr._state = "connected"

    with patch.object(mgr, "_run_restart", new_callable=AsyncMock):
        result = await mgr.restart()

    await asyncio.sleep(0)

    assert result["state"] == "restarting"
    assert isinstance(result["started_at"], int)
    assert mgr.state == "restarting"
    event = q.get_nowait()
    assert event["type"] == "editor.lifecycle"
    assert event["state"] == "restarting"


# ---------------------------------------------------------------------------
# 12. _transition sets port/pid/project when transitioning to connected
# ---------------------------------------------------------------------------

async def test_transition_to_connected_sets_meta():
    mgr = make_manager()
    mgr._state = "starting"

    mgr._transition("connected", {"port": 8742, "pid": 999, "project": "TestProj"})

    assert mgr.state == "connected"
    assert mgr.port == 8742
    assert mgr.pid == 999
    assert mgr.project == "TestProj"


# ---------------------------------------------------------------------------
# 13. _run_start background task transitions to connected on success
# ---------------------------------------------------------------------------

async def test_run_start_transitions_to_connected_on_success():
    mgr = make_manager(project_dir="/fake/project")
    mgr._state = "starting"
    mgr._started_at = int(time.time())

    fake_result = {
        "port": 8742,
        "pid": 1234,
        "project": "MyProject",
    }

    with patch.object(mgr, "_launch_editor_sync", return_value=fake_result):
        await mgr._run_start()

    assert mgr.state == "connected"
    assert mgr.port == 8742
    assert mgr.pid == 1234
    assert mgr.project == "MyProject"


# ---------------------------------------------------------------------------
# 14. _run_start transitions to error when launch returns error
# ---------------------------------------------------------------------------

async def test_run_start_transitions_to_error_on_failure():
    mgr = make_manager(project_dir="/fake/project")
    mgr._state = "starting"
    mgr._started_at = int(time.time())

    error_result = {"error": "UE_56_PATH not set"}

    with patch.object(mgr, "_launch_editor_sync", return_value=error_result):
        await mgr._run_start()

    assert mgr.state == "error"
    assert mgr.error == "UE_56_PATH not set"


# ---------------------------------------------------------------------------
# 15. _run_start transitions to disconnected when cancelled
# ---------------------------------------------------------------------------

async def test_run_start_transitions_to_disconnected_when_cancelled():
    mgr = make_manager(project_dir="/fake/project")
    mgr._state = "starting"
    mgr._started_at = int(time.time())
    mgr._cancel_event.set()  # Signal cancel before launch

    cancelled_result = {"cancelled": True}

    with patch.object(mgr, "_launch_editor_sync", return_value=cancelled_result):
        await mgr._run_start()

    assert mgr.state == "disconnected"


# ---------------------------------------------------------------------------
# 16. _run_stop transitions to disconnected
# ---------------------------------------------------------------------------

async def test_run_stop_transitions_to_disconnected():
    mgr = make_manager()
    mgr._state = "stopping"

    with patch.object(mgr, "_shutdown_editor_sync", return_value={"message": "done"}):
        await mgr._run_stop()

    assert mgr.state == "disconnected"


# ---------------------------------------------------------------------------
# 17. start() from timed_out is valid
# ---------------------------------------------------------------------------

async def test_start_from_timed_out_is_valid():
    mgr = make_manager()
    mgr._state = "timed_out"

    with patch.object(mgr, "_run_start", new_callable=AsyncMock):
        result = await mgr.start()

    assert result["state"] == "starting"


# ---------------------------------------------------------------------------
# 18. start() from error is valid
# ---------------------------------------------------------------------------

async def test_start_from_error_is_valid():
    mgr = make_manager()
    mgr._state = "error"
    mgr._error = "previous error"

    with patch.object(mgr, "_run_start", new_callable=AsyncMock):
        result = await mgr.start()

    assert result["state"] == "starting"
    # Error should be cleared by _transition
    assert mgr.error is None


# ---------------------------------------------------------------------------
# 19. get_status includes all fields
# ---------------------------------------------------------------------------

async def test_get_status_includes_all_fields_when_connected():
    mgr = make_manager()
    mgr._state = "connected"
    mgr._port = 8742
    mgr._pid = 999
    mgr._project = "SandboxProj"

    status = mgr.get_status()

    assert status["state"] == "connected"
    assert status["port"] == 8742
    assert status["pid"] == 999
    assert status["project"] == "SandboxProj"


# ---------------------------------------------------------------------------
# 20. shutdown() cancels background task
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 21. _run_start transitions to timed_out on timeout sentinel
# ---------------------------------------------------------------------------

async def test_start_transitions_to_timed_out_on_timeout():
    mgr = make_manager(project_dir="/fake/project")
    mgr._state = "starting"
    mgr._started_at = int(time.time())

    timeout_result = {
        "error": "timed_out",
        "message": "Editor did not start within 120s",
    }

    with patch.object(mgr, "_launch_editor_sync", return_value=timeout_result):
        await mgr._run_start()

    assert mgr.state == "timed_out"
    assert mgr.error == "Editor did not start within 120s"


async def test_shutdown_cancels_background_task():
    mgr = make_manager()

    async def fake_long_task():
        await asyncio.sleep(100)

    mgr._bg_task = asyncio.create_task(fake_long_task())
    await mgr.shutdown()

    assert mgr._bg_task.cancelled()


# ---------------------------------------------------------------------------
# 22. initialize() — no port files stays disconnected
# ---------------------------------------------------------------------------

async def test_initialize_stays_disconnected_when_no_port_files(tmp_path):
    """If no CortexPort-*.txt files exist, state remains disconnected."""
    mgr = make_manager(project_dir=str(tmp_path))
    # tmp_path/Saved/ does not exist, so glob returns nothing
    await mgr.initialize()
    assert mgr.state == "disconnected"


# ---------------------------------------------------------------------------
# 23. initialize() — port file present but TCP fails stays disconnected
# ---------------------------------------------------------------------------

async def test_initialize_stays_disconnected_on_tcp_failure(tmp_path):
    """Port file found but TCP verification fails; state stays disconnected."""
    saved_dir = tmp_path / "Saved"
    saved_dir.mkdir()
    port_file = saved_dir / "CortexPort-12345.txt"
    port_file.write_text('{"port": 8742, "pid": 12345, "project": "CortexSandbox"}')

    mgr = make_manager(project_dir=str(tmp_path))

    with patch.object(mgr, "_verify_tcp_connection", return_value=False):
        await mgr.initialize()

    assert mgr.state == "disconnected"


# ---------------------------------------------------------------------------
# 24. initialize() — port file present and TCP succeeds transitions to connected
# ---------------------------------------------------------------------------

async def test_initialize_transitions_to_connected_on_tcp_success(tmp_path):
    """Port file found and TCP verification succeeds; state becomes connected."""
    saved_dir = tmp_path / "Saved"
    saved_dir.mkdir()
    port_file = saved_dir / "CortexPort-12345.txt"
    port_file.write_text(
        '{"port": 8742, "pid": 12345, "project_path": "/fake/CortexSandbox.uproject"}'
    )

    mgr = make_manager(project_dir=str(tmp_path))

    with patch.object(mgr, "_verify_tcp_connection", return_value=True):
        await mgr.initialize()

    assert mgr.state == "connected"
    assert mgr.port == 8742
    assert mgr.pid == 12345
    assert mgr.project == "CortexSandbox"
