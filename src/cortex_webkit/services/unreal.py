class AsyncUEConnection:
    def __init__(self, project_dir=None):
        self._project_dir = project_dir
        self._conn = None

    @property
    def connected(self):
        return False

    async def send_command(self, command, params=None, timeout=None):
        return {"success": False, "error": "Not implemented"}

    async def get_status(self):
        return {"connected": False}

    async def get_capabilities(self):
        return {"domains": []}
