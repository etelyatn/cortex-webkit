// frontend/src/hooks/useChatSession.ts

import { useCallback } from "react";
import { useChatStore } from "../stores/chatStore";
import { useWebSocket } from "./useWebSocket";
import type { ServerEvent } from "../types/ws";

export function useChatSession(sessionId: string | null) {
  const store = useChatStore;

  const handleMessage = useCallback((event: ServerEvent) => {
    switch (event.type) {
      case "turn_started":
        store.getState().startStreaming();
        break;
      case "text_delta":
        store.getState().appendStreamingText(event.text);
        break;
      case "tool_call_start":
        store.getState().addToolCall({
          id: event.tool_use_id,
          name: event.name,
          input: "",
          isComplete: false,
        });
        break;
      case "tool_input_delta":
        store.getState().appendToolInput(event.tool_use_id, event.partial_json);
        break;
      case "tool_result":
        store.getState().updateToolResult(
          event.tool_use_id,
          event.result,
          event.is_error,
          event.duration_ms,
        );
        break;
      case "turn_complete":
        store.getState().finalizeStreaming();
        if (event.usage) {
          store.getState().updateUsage(event.usage);
        }
        break;
      case "error":
        store.getState().finalizeStreaming();
        break;
      case "session_info":
        break;
    }
  }, []);

  const { send } = useWebSocket(
    "/ws/chat",
    sessionId ? { session_id: sessionId } : {},
    handleMessage,
    (status) => store.getState().setChatWsStatus(status),
    sessionId !== null,
  );

  const sendMessage = useCallback(
    (content: string) => {
      if (!sessionId) return;
      store.getState().addMessage({
        id: crypto.randomUUID(),
        role: "user",
        content,
        timestamp: Date.now(),
      });
      send({ type: "user_message", session_id: sessionId, content });
    },
    [sessionId, send],
  );

  const cancelTurn = useCallback(() => {
    if (!sessionId) return;
    send({ type: "cancel", session_id: sessionId });
  }, [sessionId, send]);

  return { sendMessage, cancelTurn };
}
