# src/cortex_webkit/backends/base.py
"""ChatBackend abstract base class."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from cortex_webkit.events import StreamEvent


class ChatBackend(ABC):
    @abstractmethod
    async def send_message(self, message: str) -> AsyncGenerator[StreamEvent, None]:
        """Stream events for a user message."""
        ...

    @abstractmethod
    async def cancel(self) -> None:
        """Cancel the current turn."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Terminate the backend process."""
        ...

    @abstractmethod
    def get_state(self) -> str:
        """Return 'idle', 'processing', or 'disconnected'."""
        ...
