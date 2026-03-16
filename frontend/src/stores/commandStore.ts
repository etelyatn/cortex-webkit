// frontend/src/stores/commandStore.ts

import { create } from "zustand";
import type { CommandHistoryEntry, CapabilityDomain } from "../types/commands";

const MAX_FAVORITES = 20;

interface CommandState {
  rawInput: string;
  parsedDomain: string;
  parsedCommand: string;
  parsedParams: Record<string, unknown>;
  inputMode: "raw" | "structured";
  history: CommandHistoryEntry[];
  favorites: CommandHistoryEntry[];
  capabilities: CapabilityDomain[];
  isExecuting: boolean;

  setRawInput: (input: string) => void;
  setParsed: (domain: string, command: string, params: Record<string, unknown>) => void;
  setInputMode: (mode: "raw" | "structured") => void;
  addResult: (entry: CommandHistoryEntry) => void;
  toggleFavorite: (id: string) => void;
  setCapabilities: (caps: CapabilityDomain[]) => void;
  setIsExecuting: (v: boolean) => void;
}

export const useCommandStore = create<CommandState>((set, get) => ({
  rawInput: "",
  parsedDomain: "",
  parsedCommand: "",
  parsedParams: {},
  inputMode: "raw",
  history: [],
  favorites: JSON.parse(localStorage.getItem("cortex_favorites") ?? "[]"),
  capabilities: [],
  isExecuting: false,

  setRawInput: (input) => set({ rawInput: input }),

  setParsed: (domain, command, params) =>
    set({ parsedDomain: domain, parsedCommand: command, parsedParams: params }),

  setInputMode: (mode) => set({ inputMode: mode }),

  addResult: (entry) =>
    set((s) => ({ history: [entry, ...s.history].slice(0, 100) })),

  toggleFavorite: (id) =>
    set((s) => {
      const entry = s.history.find((h) => h.id === id);
      if (!entry) return s;
      const isFav = s.favorites.some((f) => f.id === id);
      let favorites: CommandHistoryEntry[];
      if (isFav) {
        favorites = s.favorites.filter((f) => f.id !== id);
      } else {
        favorites = [{ ...entry, isFavorite: true }, ...s.favorites].slice(0, MAX_FAVORITES);
      }
      localStorage.setItem("cortex_favorites", JSON.stringify(favorites));
      const history = s.history.map((h) => (h.id === id ? { ...h, isFavorite: !isFav } : h));
      return { favorites, history };
    }),

  setCapabilities: (caps) => set({ capabilities: caps }),
  setIsExecuting: (v) => set({ isExecuting: v }),
}));
