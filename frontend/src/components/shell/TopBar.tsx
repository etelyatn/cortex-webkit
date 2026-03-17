// frontend/src/components/shell/TopBar.tsx

import { useConnectionStore } from "../../stores/connectionStore";
import type { EditorLifecycle } from "../../types/ws";

const dotClass: Record<EditorLifecycle, string> = {
  connected:    'bg-success',
  disconnected: 'bg-error',
  starting:     'bg-warning animate-pulse',
  restarting:   'bg-warning animate-pulse',
  stopping:     'bg-warning animate-pulse',
  timed_out:    'bg-error',
  error:        'bg-error',
};

interface TopBarProps {
  onMenuToggle?: () => void;
}

export function TopBar({ onMenuToggle }: TopBarProps) {
  const editorLifecycle = useConnectionStore((s) => s.editorLifecycle);
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
        <span className={`w-2 h-2 rounded-full ${dotClass[editorLifecycle]}`} />
      </div>
    </div>
  );
}
