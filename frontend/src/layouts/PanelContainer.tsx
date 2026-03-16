// frontend/src/layouts/PanelContainer.tsx

import { useLayoutStore } from "../stores/layoutStore";
import { ChatPanel } from "../components/chat/ChatPanel";
import { CommandPanel } from "../components/commands/CommandPanel";

const panelMap = {
  chat: ChatPanel,
  commands: CommandPanel,
} as const;

export function PanelContainer() {
  const activePanel = useLayoutStore((s) => s.activePanel);
  const Panel = panelMap[activePanel];

  return (
    <div className="flex-1 overflow-hidden">
      <Panel />
    </div>
  );
}
