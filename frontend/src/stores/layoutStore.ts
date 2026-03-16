// frontend/src/stores/layoutStore.ts

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type PanelId = "chat" | "commands";

interface LayoutState {
  activePanel: PanelId;
  sidebarOpen: boolean;
  sidebarSections: Record<string, boolean>; // section id -> collapsed

  setActivePanel: (panel: PanelId) => void;
  toggleSidebar: () => void;
  toggleSection: (id: string) => void;
}

export const useLayoutStore = create<LayoutState>()(
  persist(
    (set) => ({
      activePanel: "chat",
      sidebarOpen: true,
      sidebarSections: {},

      setActivePanel: (panel) => set({ activePanel: panel }),
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      toggleSection: (id) =>
        set((s) => ({
          sidebarSections: {
            ...s.sidebarSections,
            [id]: !s.sidebarSections[id],
          },
        })),
    }),
    {
      name: "cortex-layout",
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        sidebarSections: state.sidebarSections,
      }),
    },
  ),
);
