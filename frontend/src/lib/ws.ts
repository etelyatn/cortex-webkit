// frontend/src/lib/ws.ts

export type MessageHandler = (data: any) => void;
export type StatusHandler = (status: "connecting" | "connected" | "disconnected") => void;

export interface ReconnectingSocketOptions {
  url: string;
  onMessage: MessageHandler;
  onStatus?: StatusHandler;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
}

/**
 * WebSocket with automatic reconnection and exponential backoff.
 */
export class ReconnectingSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private onMessage: MessageHandler;
  private onStatus: StatusHandler;
  private reconnectInterval: number;
  private maxReconnectInterval: number;
  private currentInterval: number;
  private reconnectTimer: number | null = null;
  private intentionallyClosed = false;
  private messageQueue: string[] = [];

  constructor(options: ReconnectingSocketOptions) {
    this.url = options.url;
    this.onMessage = options.onMessage;
    this.onStatus = options.onStatus ?? (() => {});
    this.reconnectInterval = options.reconnectInterval ?? 1000;
    this.maxReconnectInterval = options.maxReconnectInterval ?? 30000;
    this.currentInterval = this.reconnectInterval;
  }

  connect(): void {
    this.intentionallyClosed = false;
    this.onStatus("connecting");

    try {
      this.ws = new WebSocket(this.url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.onStatus("connected");
      this.currentInterval = this.reconnectInterval;

      // Drain queued messages
      while (this.messageQueue.length > 0) {
        const msg = this.messageQueue.shift()!;
        this.ws?.send(msg);
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onMessage(data);
      } catch {
        // Ignore unparseable messages
      }
    };

    this.ws.onclose = () => {
      if (!this.intentionallyClosed) {
        this.onStatus("disconnected");
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      // onclose will fire after onerror
    };
  }

  send(data: unknown): void {
    const msg = JSON.stringify(data);
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(msg);
    } else {
      // Cap queue to prevent unbounded growth during disconnection
      if (this.messageQueue.length >= 50) this.messageQueue.shift();
      this.messageQueue.push(msg);
    }
  }

  close(): void {
    this.intentionallyClosed = true;
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
    this.onStatus("disconnected");
  }

  get connected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private scheduleReconnect(): void {
    if (this.intentionallyClosed) return;

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, this.currentInterval);

    // Exponential backoff with cap
    this.currentInterval = Math.min(
      this.currentInterval * 1.5,
      this.maxReconnectInterval,
    );
  }
}

/**
 * Build a WebSocket URL with auth token as query param.
 */
export function wsUrl(path: string, params: Record<string, string> = {}): string {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const token = (window as any).__CORTEX_TOKEN__ ?? localStorage.getItem("cortex_token") ?? "";
  const searchParams = new URLSearchParams({ token, ...params });
  return `${proto}//${window.location.host}${path}?${searchParams}`;
}
