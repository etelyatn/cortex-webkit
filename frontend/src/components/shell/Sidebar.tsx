// frontend/src/components/shell/Sidebar.tsx

import { useLayoutStore } from "../../stores/layoutStore";
import { useConnectionStore } from "../../stores/connectionStore";
import { useChatStore } from "../../stores/chatStore";

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  const collapsed = useLayoutStore((s) => s.sidebarSections[id] ?? false);
  const toggleSection = useLayoutStore((s) => s.toggleSection);

  return (
    <div className="border-b border-border">
      <button
        onClick={() => toggleSection(id)}
        className="w-full px-3 py-2 text-xs font-semibold uppercase tracking-wider text-text-secondary hover:text-text-primary flex items-center"
      >
        <span className="mr-1">{collapsed ? "▸" : "▾"}</span>
        {title}
      </button>
      {!collapsed && <div className="px-3 pb-3 text-xs space-y-1">{children}</div>}
    </div>
  );
}

export function Sidebar() {
  const ueConnected = useConnectionStore((s) => s.ueConnected);
  const uePort = useConnectionStore((s) => s.uePort);
  const totalUsage = useChatStore((s) => s.totalUsage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  const contextPct = totalUsage.input_tokens > 0
    ? Math.round((totalUsage.input_tokens / 200000) * 100)
    : 0;
  const contextColor = contextPct > 80 ? "bg-error" : contextPct > 60 ? "bg-warning" : "bg-accent";

  return (
    <div className="w-56 flex flex-col bg-bg-secondary border-r border-border overflow-y-auto shrink-0 hidden md:flex">
      <Section id="model" title="AI Model">
        <div className="font-mono text-text-primary">claude-sonnet-4-6</div>
      </Section>

      <Section id="connection" title="Connection">
        <div className="flex justify-between">
          <span className="text-text-secondary">Session:</span>
          <span className={isStreaming ? "text-warning" : "text-success"}>
            {isStreaming ? "Processing" : "Idle"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">Access:</span>
          <span className="font-mono">Full</span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">Effort:</span>
          <span className="font-mono">Medium</span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">Workflow:</span>
          <span className="font-mono">Direct</span>
        </div>
      </Section>

      <Section id="directive" title="Directive">
        <textarea
          placeholder="Custom system prompt..."
          className="w-full h-16 bg-bg-tertiary border border-border rounded px-2 py-1 text-xs font-mono resize-y
                     focus:outline-none focus:border-accent placeholder:text-text-secondary/50"
        />
      </Section>

      <Section id="tokens" title="Tokens">
        <div className="flex justify-between">
          <span className="text-text-secondary">Input:</span>
          <span className="font-mono">{totalUsage.input_tokens.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">Output:</span>
          <span className="font-mono">{totalUsage.output_tokens.toLocaleString()}</span>
        </div>
        <div className="mt-1">
          <div className="h-1.5 bg-bg-tertiary rounded-sm overflow-hidden">
            <div className={`h-full ${contextColor} transition-all`} style={{ width: `${Math.min(contextPct, 100)}%` }} />
          </div>
          <div className="text-text-secondary mt-0.5">{contextPct}% context</div>
        </div>
      </Section>

      <Section id="ue" title="Unreal Engine">
        <div className="flex justify-between">
          <span className="text-text-secondary">Status:</span>
          <span className={ueConnected ? "text-success" : "text-error"}>
            {ueConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
        {uePort && (
          <div className="flex justify-between">
            <span className="text-text-secondary">Port:</span>
            <span className="font-mono">{uePort}</span>
          </div>
        )}
      </Section>
    </div>
  );
}
