// frontend/src/App.tsx

import { AppShell } from "./components/shell/AppShell";
import { useConnectionStore } from "./stores/connectionStore";
import { useWebSocket } from "./hooks/useWebSocket";
import type { ServerEvent, EditorLifecycle } from "./types/ws";

export default function App() {
  const transitionLifecycle = useConnectionStore((s) => s.transitionLifecycle);
  const setEventWsStatus = useConnectionStore((s) => s.setEventWsStatus);

  // Connect to /ws/events for UE connection status
  useWebSocket(
    "/ws/events",
    {},
    (event: ServerEvent) => {
      if (event.type === "editor.lifecycle") {
        transitionLifecycle(event.state as EditorLifecycle, {
          error: event.error,
          startedAt: event.started_at,
          port: event.port,
          pid: event.pid,
          project: event.project,
        });
      }
      // ue_status events are kept for non-lifecycle status data but no longer
      // drive connection state — lifecycle is driven by editor.lifecycle events only
    },
    setEventWsStatus,
  );

  return <AppShell />;
}
