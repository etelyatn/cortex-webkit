class ChatSession:
    def __init__(self, session_id, model=None, directive=None, buffer_size=500):
        self.id = session_id
        self.model = model or ""
        self.directive = directive or ""
        self.backend = None
        self.websocket = None

    @property
    def state(self):
        return "idle"

    def info(self):
        from cortex_webkit.models.chat import SessionInfo
        return SessionInfo(id=self.id, model=self.model, state=self.state)

    def buffer_event(self, event):
        pass

    def get_buffered_events(self):
        return []

    def increment_messages(self):
        pass


class SessionManager:
    def __init__(self, config):
        self._config = config
        self._sessions = {}

    async def create_session(self, model=None, directive=None):
        import uuid
        session_id = str(uuid.uuid4())
        session = ChatSession(session_id=session_id, model=model, directive=directive)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id):
        return self._sessions.get(session_id)

    def list_sessions(self):
        return [s.info() for s in self._sessions.values()]

    async def delete_session(self, session_id):
        session = self._sessions.pop(session_id, None)
        return session is not None

    async def shutdown_all(self):
        self._sessions.clear()
