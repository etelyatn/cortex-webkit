// frontend/src/hooks/useWebSocket.ts

import { useEffect, useRef, useCallback } from "react";
import { ReconnectingSocket, wsUrl, type MessageHandler, type StatusHandler } from "../lib/ws";

export function useWebSocket(
  path: string,
  params: Record<string, string>,
  onMessage: MessageHandler,
  onStatus?: StatusHandler,
  enabled: boolean = true,
) {
  const socketRef = useRef<ReconnectingSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  const onStatusRef = useRef(onStatus);
  onMessageRef.current = onMessage;
  onStatusRef.current = onStatus;

  useEffect(() => {
    if (!enabled) return;

    const url = wsUrl(path, params);
    const socket = new ReconnectingSocket({
      url,
      onMessage: (data) => onMessageRef.current(data),
      onStatus: (status) => onStatusRef.current?.(status),
    });
    socketRef.current = socket;
    socket.connect();

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [path, JSON.stringify(params), enabled]);

  const send = useCallback((data: unknown) => {
    socketRef.current?.send(data);
  }, []);

  return { send };
}
