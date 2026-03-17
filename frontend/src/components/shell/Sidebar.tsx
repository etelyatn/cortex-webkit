// frontend/src/components/shell/Sidebar.tsx

import { useEffect, useState } from "react";
import { useLayoutStore } from "../../stores/layoutStore";
import { useConnectionStore, selectEditorBusy } from "../../stores/connectionStore";
import { useChatStore } from "../../stores/chatStore";
import { api } from "../../lib/api";

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

function EditorSection() {
  const editorLifecycle = useConnectionStore((s) => s.editorLifecycle);
  const editorStartedAt = useConnectionStore((s) => s.editorStartedAt);
  const editorError = useConnectionStore((s) => s.editorError);
  const uePort = useConnectionStore((s) => s.uePort);
  const uePid = useConnectionStore((s) => s.uePid);
  const ueProject = useConnectionStore((s) => s.ueProject);
  const isBusy = useConnectionStore(selectEditorBusy);

  const [elapsed, setElapsed] = useState(0);
  const [startDisabled, setStartDisabled] = useState(false);
  const [stopDisabled, setStopDisabled] = useState(false);
  const [restartDisabled, setRestartDisabled] = useState(false);
  const [stopConfirm, setStopConfirm] = useState(false);

  // Reset disabled states on lifecycle transition
  useEffect(() => {
    setStartDisabled(false);
    setStopDisabled(false);
    setRestartDisabled(false);
    setStopConfirm(false);
  }, [editorLifecycle]);

  // Elapsed timer during busy states
  useEffect(() => {
    if (!isBusy) {
      setElapsed(0);
      return;
    }
    const base = editorStartedAt ?? Date.now();
    const tick = () => setElapsed(Math.floor((Date.now() - base) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [isBusy, editorStartedAt]);

  const statusLabel = () => {
    switch (editorLifecycle) {
      case 'connected':    return <span className="text-success">Connected</span>;
      case 'disconnected': return <span className="text-error">Disconnected</span>;
      case 'starting':     return <span className="text-warning">Starting... ({elapsed}s)</span>;
      case 'restarting':   return <span className="text-warning">Restarting... ({elapsed}s)</span>;
      case 'stopping':     return <span className="text-warning">Stopping...</span>;
      case 'timed_out':    return <span className="text-error">Timed Out</span>;
      case 'error':        return <span className="text-error">Error</span>;
    }
  };

  const handleStart = () => {
    setStartDisabled(true);
    api.startEditor().catch(() => setStartDisabled(false));
  };

  const handleStop = () => {
    setStopDisabled(true);
    setStopConfirm(false);
    api.stopEditor().catch(() => setStopDisabled(false));
  };

  const handleRestart = () => {
    setRestartDisabled(true);
    api.restartEditor().catch(() => setRestartDisabled(false));
  };

  return (
    <Section id="editor" title="Editor">
      <div className="flex justify-between">
        <span className="text-text-secondary">Status:</span>
        {statusLabel()}
      </div>

      {editorLifecycle === 'connected' && (
        <>
          {ueProject && (
            <div className="flex justify-between">
              <span className="text-text-secondary">Project:</span>
              <span className="font-mono truncate ml-2 text-right">{ueProject}</span>
            </div>
          )}
          {uePid != null && (
            <div className="flex justify-between">
              <span className="text-text-secondary">PID:</span>
              <span className="font-mono">{uePid}</span>
            </div>
          )}
          {uePort != null && (
            <div className="flex justify-between">
              <span className="text-text-secondary">Port:</span>
              <span className="font-mono">{uePort}</span>
            </div>
          )}
          <div className="flex gap-1 pt-1">
            <button
              type="button"
              onClick={handleRestart}
              disabled={restartDisabled}
              className={`px-3 py-1.5 text-xs bg-bg-tertiary border border-border rounded hover:bg-bg-primary ${restartDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              Restart
            </button>
            {!stopConfirm ? (
              <button
                type="button"
                onClick={() => setStopConfirm(true)}
                disabled={stopDisabled}
                className={`px-3 py-1.5 text-xs bg-error/20 text-error border border-error/40 rounded hover:bg-error/30 ${stopDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                Stop
              </button>
            ) : (
              <span className="flex items-center gap-1">
                <span className="text-error">Sure?</span>
                <button
                  type="button"
                  onClick={() => setStopConfirm(false)}
                  className="px-2 py-1 text-xs bg-bg-tertiary border border-border rounded hover:bg-bg-primary"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleStop}
                  className="px-2 py-1 text-xs bg-error/20 text-error border border-error/40 rounded hover:bg-error/30"
                >
                  Stop
                </button>
              </span>
            )}
          </div>
        </>
      )}

      {(editorLifecycle === 'starting' || editorLifecycle === 'restarting') && (
        <div className="flex gap-1 pt-1">
          <button
            type="button"
            disabled
            className="px-3 py-1.5 text-xs bg-warning/20 text-warning border border-warning/40 rounded opacity-50 cursor-not-allowed animate-pulse"
          >
            {editorLifecycle === 'starting' ? `Starting... (${elapsed}s)` : `Restarting... (${elapsed}s)`}
          </button>
          <button
            type="button"
            onClick={() => { setStopDisabled(true); api.stopEditor().catch(() => setStopDisabled(false)); }}
            disabled={stopDisabled}
            className={`px-3 py-1.5 text-xs bg-error/20 text-error border border-error/40 rounded hover:bg-error/30 ${stopDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            Stop
          </button>
        </div>
      )}

      {editorLifecycle === 'stopping' && (
        <button
          type="button"
          disabled
          className="mt-1 w-full px-3 py-1.5 text-xs bg-warning/20 text-warning border border-warning/40 rounded opacity-50 cursor-not-allowed animate-pulse"
        >
          Stopping...
        </button>
      )}

      {editorLifecycle === 'disconnected' && (
        <button
          type="button"
          onClick={handleStart}
          disabled={startDisabled}
          className={`mt-1 w-full px-3 py-1.5 text-xs bg-bg-tertiary border border-border rounded hover:bg-bg-primary ${startDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          Start Editor
        </button>
      )}

      {(editorLifecycle === 'timed_out' || editorLifecycle === 'error') && (
        <>
          {editorError && (
            <div className="text-error mt-1 break-words">{editorError}</div>
          )}
          <button
            type="button"
            onClick={handleStart}
            disabled={startDisabled}
            className={`mt-1 w-full px-3 py-1.5 text-xs bg-bg-tertiary border border-border rounded hover:bg-bg-primary ${startDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            Retry
          </button>
        </>
      )}
    </Section>
  );
}

export function Sidebar() {
  const totalUsage = useChatStore((s) => s.totalUsage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  const contextPct = totalUsage.input_tokens > 0
    ? Math.round((totalUsage.input_tokens / 200000) * 100)
    : 0;
  const contextColor = contextPct > 80 ? "bg-error" : contextPct > 60 ? "bg-warning" : "bg-accent";

  return (
    <div className="w-56 flex flex-col bg-bg-secondary border-r border-border overflow-y-auto shrink-0 hidden md:flex">
      <EditorSection />

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
    </div>
  );
}
