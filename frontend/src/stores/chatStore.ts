// frontend/src/stores/chatStore.ts

import { create } from "zustand";
import type { ChatMessage, ChatSession, ToolCall } from "../types/chat";
import type { TokenUsage } from "../types/ws";

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  messages: ChatMessage[];

  // Streaming state
  streamingText: string;
  streamingToolCalls: ToolCall[];
  isStreaming: boolean;

  totalUsage: TokenUsage;
  chatWsStatus: "connecting" | "connected" | "disconnected";

  setSessions: (sessions: ChatSession[]) => void;
  setActiveSession: (id: string) => void;
  addMessage: (msg: ChatMessage) => void;
  appendStreamingText: (text: string) => void;
  finalizeStreaming: () => void;
  startStreaming: () => void;
  addToolCall: (tc: ToolCall) => void;
  appendToolInput: (toolUseId: string, partialJson: string) => void;
  updateToolResult: (toolUseId: string, result: unknown, isError: boolean, durationMs?: number) => void;
  updateUsage: (usage: TokenUsage) => void;
  clearMessages: () => void;
  setChatWsStatus: (status: "connecting" | "connected" | "disconnected") => void;
}

export const useChatStore = create<ChatState>((set, _get) => ({
  sessions: [],
  activeSessionId: null,
  messages: [],
  streamingText: "",
  streamingToolCalls: [],
  isStreaming: false,
  totalUsage: { input_tokens: 0, output_tokens: 0 },
  chatWsStatus: "disconnected",

  setSessions: (sessions) => set({ sessions }),
  setActiveSession: (id) => set({ activeSessionId: id }),

  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),

  appendStreamingText: (text) =>
    set((s) => ({ streamingText: s.streamingText + text })),

  startStreaming: () => set({ streamingText: "", streamingToolCalls: [], isStreaming: true }),

  finalizeStreaming: () =>
    set((s) => {
      if (!s.streamingText && s.streamingToolCalls.length === 0) {
        return { isStreaming: false };
      }
      const msg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: s.streamingText,
        timestamp: Date.now(),
        toolCalls: s.streamingToolCalls.length > 0 ? s.streamingToolCalls : undefined,
      };
      return {
        messages: [...s.messages, msg],
        streamingText: "",
        streamingToolCalls: [],
        isStreaming: false,
      };
    }),

  addToolCall: (tc) =>
    set((s) => ({
      streamingToolCalls: [...s.streamingToolCalls, tc],
    })),

  appendToolInput: (toolUseId, partialJson) =>
    set((s) => ({
      streamingToolCalls: s.streamingToolCalls.map((tc) =>
        tc.id === toolUseId ? { ...tc, input: tc.input + partialJson } : tc,
      ),
    })),

  updateToolResult: (toolUseId, result, isError, durationMs) =>
    set((s) => {
      const inStreaming = s.streamingToolCalls.some((tc) => tc.id === toolUseId);
      if (inStreaming) {
        return {
          streamingToolCalls: s.streamingToolCalls.map((tc) =>
            tc.id === toolUseId
              ? { ...tc, result, isError, durationMs, isComplete: true }
              : tc,
          ),
        };
      }
      const messages = s.messages.map((msg) => {
        if (!msg.toolCalls) return msg;
        const toolCalls = msg.toolCalls.map((tc) =>
          tc.id === toolUseId
            ? { ...tc, result, isError, durationMs, isComplete: true }
            : tc,
        );
        return { ...msg, toolCalls };
      });
      return { messages };
    }),

  updateUsage: (usage) =>
    set((s) => ({
      totalUsage: {
        input_tokens: s.totalUsage.input_tokens + usage.input_tokens,
        output_tokens: s.totalUsage.output_tokens + usage.output_tokens,
        cache_read_input_tokens:
          (s.totalUsage.cache_read_input_tokens ?? 0) +
          (usage.cache_read_input_tokens ?? 0),
        cache_creation_input_tokens:
          (s.totalUsage.cache_creation_input_tokens ?? 0) +
          (usage.cache_creation_input_tokens ?? 0),
      },
    })),

  clearMessages: () =>
    set({ messages: [], streamingText: "", streamingToolCalls: [], isStreaming: false, totalUsage: { input_tokens: 0, output_tokens: 0 } }),

  setChatWsStatus: (status) => set({ chatWsStatus: status }),
}));
