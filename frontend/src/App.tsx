// frontend/src/App.tsx

import { AppShell } from "./components/shell/AppShell";
import { useConnectionStore } from "./stores/connectionStore";
import { useWebSocket } from "./hooks/useWebSocket";
import type { ServerEvent } from "./types/ws";

export default function App() {
  const setUeStatus = useConnectionStore((s) => s.setUeStatus);
  const setEventWsStatus = useConnectionStore((s) => s.setEventWsStatus);

  // Connect to /ws/events for UE connection status
  useWebSocket(
    "/ws/events",
    {},
    (event: ServerEvent) => {
      if (event.type === "ue_status") {
        setUeStatus(event);
      }
    },
    setEventWsStatus,
  );

  return <AppShell />;
}
