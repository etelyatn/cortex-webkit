// frontend/src/components/shell/AppShell.tsx

import { TopBar } from "./TopBar";
import { ActivityBar } from "./ActivityBar";
import { Sidebar } from "./Sidebar";
import { PanelContainer } from "../../layouts/PanelContainer";
import { useLayoutStore } from "../../stores/layoutStore";

export function AppShell() {
  const sidebarOpen = useLayoutStore((s) => s.sidebarOpen);
  const toggleSidebar = useLayoutStore((s) => s.toggleSidebar);

  return (
    <div className="h-screen flex flex-col bg-bg-primary text-text-primary">
      <TopBar onMenuToggle={toggleSidebar} />
      <div className="flex flex-1 overflow-hidden">
        <ActivityBar />
        {sidebarOpen && <Sidebar />}
        <PanelContainer />
      </div>
    </div>
  );
}
