// frontend/src/components/chat/ToolCallCard.tsx

import { useState, memo } from "react";
import type { ToolCall } from "../../types/chat";

interface ToolCallCardProps {
  toolCall: ToolCall;
}

export const ToolCallCard = memo(function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false);

  const domain = toolCall.name.split(".")[0] ?? "";

  return (
    <div
      className={`border rounded my-1 text-xs ${
        toolCall.isError ? "border-error/40" : "border-border"
      }`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-3 py-1.5 flex items-center gap-2 hover:bg-bg-tertiary"
      >
        <span className="text-text-secondary">{expanded ? "▾" : "▸"}</span>
        <span className="text-accent font-mono">{domain}</span>
        <span className="font-mono text-text-primary">{toolCall.name.split(".").slice(1).join(".")}</span>
        <span className="ml-auto flex items-center gap-2">
          {toolCall.durationMs != null && (
            <span className="text-text-secondary">{toolCall.durationMs}ms</span>
          )}
          {toolCall.isComplete ? (
            <span className={toolCall.isError ? "text-error" : "text-success"}>
              {toolCall.isError ? "✗" : "✓"}
            </span>
          ) : (
            <span className="text-warning animate-pulse">⋯</span>
          )}
        </span>
      </button>
      {expanded && (
        <div className="border-t border-border px-3 py-2 space-y-2">
          {toolCall.input && (
            <div>
              <div className="text-text-secondary mb-1">Input</div>
              <pre className="bg-bg-primary p-2 rounded overflow-x-auto font-mono">
                {typeof toolCall.input === "string"
                  ? toolCall.input
                  : JSON.stringify(toolCall.input, null, 2)}
              </pre>
            </div>
          )}
          {toolCall.isComplete && toolCall.result != null && (
            <div>
              <div className="text-text-secondary mb-1">Result</div>
              <pre className="bg-bg-primary p-2 rounded overflow-x-auto font-mono max-h-48 overflow-y-auto">
                {typeof toolCall.result === "string"
                  ? toolCall.result
                  : JSON.stringify(toolCall.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
});
