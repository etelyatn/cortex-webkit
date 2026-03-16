// frontend/src/components/shell/ActivityBar.tsx

import { useLayoutStore, type PanelId } from "../../stores/layoutStore";

const panels: { id: PanelId; label: string; icon: string }[] = [
  { id: "chat", label: "Chat", icon: "Ch" },
  { id: "commands", label: "Commands", icon: "Cm" },
];

export function ActivityBar() {
  const activePanel = useLayoutStore((s) => s.activePanel);
  const setActivePanel = useLayoutStore((s) => s.setActivePanel);
  const toggleSidebar = useLayoutStore((s) => s.toggleSidebar);

  return (
    <div className="w-12 hidden md:flex flex-col items-center py-2 gap-1 bg-bg-secondary border-r border-border shrink-0">
      <button
        onClick={toggleSidebar}
        className="w-10 h-10 md:hidden flex items-center justify-center text-xs font-mono text-text-secondary hover:text-text-primary"
      >
        ≡
      </button>
      {panels.map((p) => (
        <button
          key={p.id}
          onClick={() => setActivePanel(p.id)}
          title={p.label}
          className={`w-10 h-10 flex items-center justify-center text-xs font-mono font-semibold rounded
            ${activePanel === p.id ? "bg-bg-tertiary text-text-primary" : "text-text-secondary hover:text-text-primary"}`}
        >
          {p.icon}
        </button>
      ))}
    </div>
  );
}
