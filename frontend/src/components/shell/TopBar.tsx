// frontend/src/components/shell/TopBar.tsx

import { useConnectionStore } from "../../stores/connectionStore";

interface TopBarProps {
  onMenuToggle?: () => void;
}

export function TopBar({ onMenuToggle }: TopBarProps) {
  const ueConnected = useConnectionStore((s) => s.ueConnected);
  const ueProject = useConnectionStore((s) => s.ueProject);

  return (
    <div className="h-10 flex items-center px-4 bg-bg-secondary border-b border-border shrink-0">
      <button
        onClick={onMenuToggle}
        className="md:hidden mr-3 text-text-secondary hover:text-text-primary text-lg"
      >
        ≡
      </button>
      <span className="font-semibold text-sm tracking-wide mr-2">CORTEX</span>
      <span className="text-text-secondary text-xs hidden sm:inline">
        {ueProject ?? "No Project"}
      </span>
      <div className="ml-auto flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${ueConnected ? "bg-success" : "bg-error"}`}
        />
        <span className="text-xs text-text-secondary hidden sm:inline">
          {ueConnected ? "UE Connected" : "UE Disconnected"}
        </span>
      </div>
    </div>
  );
}
