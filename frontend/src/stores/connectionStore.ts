// frontend/src/stores/connectionStore.ts

import { create } from "zustand";
import type { EditorLifecycle } from "../types/ws";

const VALID_TRANSITIONS: Record<EditorLifecycle, EditorLifecycle[]> = {
  disconnected: ['starting'],
  starting:     ['connected', 'timed_out', 'error', 'disconnected'],
  connected:    ['stopping', 'restarting', 'error', 'disconnected'],
  stopping:     ['disconnected', 'error'],
  restarting:   ['connected', 'timed_out', 'error', 'disconnected'],
  timed_out:    ['starting', 'disconnected'],
  error:        ['starting', 'disconnected'],
};

// States where editorStartedAt is cleared on transition
const CLEAR_STARTED_AT_ON: EditorLifecycle[] = ['disconnected', 'error', 'timed_out'];

interface ConnectionState {
  editorLifecycle: EditorLifecycle;
  editorStartedAt: number | null;
  editorError: string | null;

  uePort: number | null;
  uePid: number | null;
  ueProject: string | null;

  eventWsStatus: "connecting" | "connected" | "disconnected";

  transitionLifecycle: (to: EditorLifecycle, meta?: {
    error?: string;
    startedAt?: number;
    port?: number;
    pid?: number;
    project?: string;
  }) => void;
  setEventWsStatus: (status: "connecting" | "connected" | "disconnected") => void;
}

export const useConnectionStore = create<ConnectionState>((set, get) => ({
  editorLifecycle: 'disconnected',
  editorStartedAt: null,
  editorError: null,

  uePort: null,
  uePid: null,
  ueProject: null,

  eventWsStatus: "disconnected",

  transitionLifecycle: (to, meta) => {
    const current = get().editorLifecycle;
    const allowed = VALID_TRANSITIONS[current];

    if (!allowed.includes(to)) {
      if ((import.meta as any).env?.DEV) {
        console.warn(`[connectionStore] Invalid lifecycle transition: ${current} → ${to}`);
      }
      return;
    }

    set((state) => {
      // Clear editorError when transitioning out of error/timed_out
      const clearError = state.editorLifecycle === 'error' || state.editorLifecycle === 'timed_out';

      // Clear editorStartedAt on transition to connected (new start) or disconnected/error/timed_out
      const clearStartedAt = CLEAR_STARTED_AT_ON.includes(to);

      return {
        editorLifecycle: to,
        editorError: clearError ? (meta?.error ?? null) : (meta?.error ?? state.editorError),
        editorStartedAt: clearStartedAt ? null : (meta?.startedAt ?? state.editorStartedAt),
        uePort: meta?.port !== undefined ? meta.port : state.uePort,
        uePid: meta?.pid !== undefined ? meta.pid : state.uePid,
        ueProject: meta?.project !== undefined ? meta.project : state.ueProject,
      };
    });
  },

  setEventWsStatus: (status) => set({ eventWsStatus: status }),
}));

export const selectUeConnected = (s: ConnectionState) => s.editorLifecycle === 'connected';
export const selectEditorBusy = (s: ConnectionState) =>
  ['starting', 'stopping', 'restarting'].includes(s.editorLifecycle);
