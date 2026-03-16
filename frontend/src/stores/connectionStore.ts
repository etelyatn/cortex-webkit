// frontend/src/stores/connectionStore.ts

import { create } from "zustand";

interface ConnectionState {
  ueConnected: boolean;
  uePort: number | null;
  uePid: number | null;
  ueProject: string | null;
  eventWsStatus: "connecting" | "connected" | "disconnected";

  setUeStatus: (status: { connected: boolean; port?: number; pid?: number; project?: string }) => void;
  setEventWsStatus: (status: "connecting" | "connected" | "disconnected") => void;
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  ueConnected: false,
  uePort: null,
  uePid: null,
  ueProject: null,
  eventWsStatus: "disconnected",

  setUeStatus: (status) =>
    set({
      ueConnected: status.connected,
      uePort: status.port ?? null,
      uePid: status.pid ?? null,
      ueProject: status.project ?? null,
    }),
  setEventWsStatus: (status) => set({ eventWsStatus: status }),
}));
