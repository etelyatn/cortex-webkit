// frontend/src/types/chat.ts

import type { TokenUsage } from "./ws";

export interface ChatSession {
  id: string;
  backend: "cli" | "sdk";
  model: string;
  state: "idle" | "processing" | "disconnected";
  message_count: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  toolCalls?: ToolCall[];
  usage?: TokenUsage;
}

export interface ToolCall {
  id: string;
  name: string;
  input: string;
  result?: unknown;
  isError?: boolean;
  durationMs?: number;
  isComplete: boolean;
}
