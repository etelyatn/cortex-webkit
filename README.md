# Cortex Web Kit

Browser-based control panel for AI-powered Unreal Engine development. Provides a web UI for chatting with Claude (backed by the Claude CLI) and executing UnrealCortex MCP commands directly against a running Unreal Editor.

## Features

- **Chat panel** — Streaming chat with Claude CLI, full markdown rendering, tool call visualization
- **Command panel** — Execute UnrealCortex MCP commands with autocomplete, structured param forms, and tree/table/raw result views
- **Live UE status** — WebSocket polling of Unreal Editor connection state
- **Auth** — Bearer token auth, auto-generated on first run and injected into the served HTML

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js 18+ and npm (for frontend development/build)
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude` on PATH)
- [UnrealCortex](https://github.com/etelyatn/UnrealCortex) MCP plugin running in Unreal Editor (optional — app runs without it)

## Installation

```bash
# Clone the repo
git clone https://github.com/etelyatn/cortex-webkit
cd cortex-webkit

# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend && npm install && cd ..
```

## Usage

### Development (with mock backend)

Runs a mock backend that simulates both the Claude CLI and Unreal Editor — no real editor or API key required:

```bash
./scripts/dev.sh --mock
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173

Use `mock-token` as the auth token when prompted.

### Development (real backend)

Requires a running Unreal Editor with UnrealCortex loaded and `claude` on PATH:

```bash
./scripts/dev.sh
```

The auth token is printed to the backend console on first start. It is also injected into the served HTML at `/` so the browser picks it up automatically.

### Production

Build the frontend and serve everything from the Python backend:

```bash
# Build frontend
./scripts/build.sh

# Start server
uv run cortex-web
```

The server defaults to `127.0.0.1:8000`. Configure via environment variables:

| Variable | Default | Description |
|---|---|---|
| `CORTEX_WEB_PORT` | `8000` | Server port |
| `CORTEX_WEB_HOST` | `127.0.0.1` | Server host |
| `CORTEX_AUTH_TOKEN` | *(auto-generated)* | Bearer token for API auth |

## Development

### Backend tests

```bash
uv run pytest tests/ -v
```

### Frontend type check

```bash
cd frontend && npx tsc --noEmit
```

### Project structure

```
src/cortex_webkit/       # FastAPI backend
  app.py                 # App factory + lifespan
  config.py              # pydantic-settings config
  auth.py                # Bearer token auth
  api/                   # REST endpoints (status, commands, sessions, settings)
  ws/                    # WebSocket handlers (chat, events)
  backends/              # Chat backends (CliBackend — Claude subprocess)
  services/              # AsyncUEConnection wrapper

frontend/src/            # React 18 + TypeScript frontend
  components/chat/       # Chat panel, streaming text, tool call cards
  components/commands/   # Command panel, autocomplete, param forms, result cards
  components/shell/      # App shell, layout, sidebar
  stores/                # Zustand state (layout, connection, chat, commands)
  hooks/                 # WebSocket hooks, chat session, hotkeys
  lib/                   # REST client, WebSocket, command parser

scripts/
  dev.sh                 # Start dev environment (--mock for mock backend)
  build.sh               # Build frontend
  mock_server.py         # FastAPI mock backend for frontend development
```

## License

MIT
