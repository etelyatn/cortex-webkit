// frontend/src/types/ws.ts

export type EditorLifecycle =
  | 'disconnected'
  | 'starting'
  | 'connected'
  | 'stopping'
  | 'restarting'
  | 'timed_out'
  | 'error';

/** Client → Server */
export type ClientMessage =
  | { type: "user_message"; session_id: string; content: string }
  | { type: "cancel"; session_id: string };

/** Server → Client */
export type ServerEvent =
  | { type: "session_info"; backend: "cli" | "sdk"; session_id: string; model: string; capabilities?: Record<string, unknown> }
  | { type: "turn_started" }
  | { type: "text_delta"; text: string }
  | { type: "tool_call_start"; tool_use_id: string; name: string }
  | { type: "tool_input_delta"; tool_use_id: string; partial_json: string }
  | { type: "tool_result"; tool_use_id: string; result: unknown; is_error: boolean; duration_ms?: number }
  | { type: "turn_complete"; usage: TokenUsage }
  | { type: "error"; code: string; message: string; retryable: boolean }
  | { type: "replay_start"; event_count: number }
  | { type: "replay_end" }
  | { type: "ue_status"; connected: boolean; port?: number; pid?: number; project?: string }
  | { type: "editor.lifecycle"; state: EditorLifecycle; started_at?: number; port?: number; pid?: number; project?: string; error?: string };

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  cache_read_input_tokens?: number;
  cache_creation_input_tokens?: number;
}
