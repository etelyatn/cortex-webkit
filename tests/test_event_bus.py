# tests/test_event_bus.py
import asyncio
import pytest
from cortex_webkit.services.event_bus import EventBus


def test_subscribe_returns_queue():
    bus = EventBus()
    q = bus.subscribe()
    assert isinstance(q, asyncio.Queue)


async def test_emit_puts_event_on_subscriber_queue():
    bus = EventBus()
    q = bus.subscribe()
    event = {"type": "editor_started", "pid": 42}
    await bus.emit(event)
    assert not q.empty()
    assert q.get_nowait() == event


async def test_unsubscribe_removes_subscriber():
    bus = EventBus()
    q = bus.subscribe()
    bus.unsubscribe(q)
    await bus.emit({"type": "editor_started"})
    assert q.empty()


async def test_multiple_subscribers_each_receive_event():
    bus = EventBus()
    q1 = bus.subscribe()
    q2 = bus.subscribe()
    event = {"type": "editor_stopped"}
    await bus.emit(event)
    assert q1.get_nowait() == event
    assert q2.get_nowait() == event
