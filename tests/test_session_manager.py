# tests/test_session_manager.py
import pytest
from cortex_webkit.session import SessionManager, ChatSession
from cortex_webkit.config import CortexWebConfig


@pytest.fixture
def config():
    return CortexWebConfig(auth_token="test", max_sessions=3)


@pytest.fixture
def manager(config):
    return SessionManager(config=config)


@pytest.mark.asyncio
async def test_create_session(manager):
    session = await manager.create_session()
    assert session is not None
    assert session.id is not None
    assert session.state == "idle"


@pytest.mark.asyncio
async def test_list_sessions(manager):
    await manager.create_session()
    await manager.create_session()
    sessions = manager.list_sessions()
    assert len(sessions) == 2


@pytest.mark.asyncio
async def test_get_session(manager):
    session = await manager.create_session()
    found = manager.get_session(session.id)
    assert found is not None
    assert found.id == session.id


@pytest.mark.asyncio
async def test_delete_session(manager):
    session = await manager.create_session()
    deleted = await manager.delete_session(session.id)
    assert deleted is True
    assert manager.get_session(session.id) is None


@pytest.mark.asyncio
async def test_max_sessions_enforced(manager):
    for _ in range(3):
        await manager.create_session()
    with pytest.raises(RuntimeError, match="max sessions"):
        await manager.create_session()


def test_event_buffer_ring_behavior():
    session = ChatSession(session_id="test")
    # Fill beyond capacity (500 default)
    for i in range(600):
        session.buffer_event({"type": "text_delta", "text": str(i)})
    events = session.get_buffered_events()
    assert len(events) == 500
    assert events[0]["text"] == "100"  # oldest 100 dropped
