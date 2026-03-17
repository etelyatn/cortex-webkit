// frontend/src/components/commands/ResultCard.tsx

import { useState, memo } from "react";
import type { CommandHistoryEntry } from "../../types/commands";
import { JsonTree } from "./JsonTree";

interface ResultCardProps {
  entry: CommandHistoryEntry;
  onToggleFavorite: (id: string) => void;
}

export const ResultCard = memo(function ResultCard({ entry, onToggleFavorite }: ResultCardProps) {
  const [expanded, setExpanded] = useState(true);
  const [viewMode, setViewMode] = useState<"tree" | "table" | "raw">("tree");

  // Detect array data for table view
  const arrayData = (() => {
    if (!entry.response.data || typeof entry.response.data !== "object") return null;
    const d = entry.response.data as Record<string, unknown>;
    const arr = d["items"] ?? d["results"];

    if (!Array.isArray(arr) || arr.length === 0) return null;
    // Check if flat objects (all values are primitives)
    const first = arr[0];
    if (typeof first !== "object" || first === null) return null;
    if (!Object.values(first as Record<string, unknown>).every(v => v === null || typeof v !== "object")) return null;
    return arr as Record<string, unknown>[];
  })();
  const hasTable = arrayData !== null;

  return (
    <div className={`border rounded ${entry.response.success ? "border-border" : "border-error/40"}`}>
      {/* Header */}
      <div className="px-3 py-1.5 flex items-center gap-2 text-xs bg-bg-tertiary">
        <button
          type="button"
          onClick={() => onToggleFavorite(entry.id)}
          className={`${entry.isFavorite ? "text-warning" : "text-text-secondary"} hover:text-warning`}
        >
          ★
        </button>
        <button type="button" onClick={() => setExpanded(!expanded)} className="flex-1 text-left flex items-center gap-2">
          <span className="font-mono text-accent">{entry.domain}.{entry.command}</span>
          {Object.keys(entry.params ?? {}).length > 0 && (
            <span className="text-text-secondary font-mono truncate">
              {Object.entries(entry.params ?? {}).map(([k, v]) => `${k}=${v}`).join(" ")}
            </span>
          )}
        </button>
        <span className="text-text-secondary">{entry.response.duration_ms}ms</span>
        <span className={entry.response.success ? "text-success" : "text-error"}>
          {entry.response.success ? "✓" : "✗"}
        </span>
      </div>

      {/* Body */}
      {expanded && (
        <div className="px-3 py-2 border-t border-border">
          <div className="flex gap-1 mb-2">
            <button
              type="button"
              onClick={() => setViewMode("tree")}
              className={`px-2 py-0.5 text-xs rounded ${viewMode === "tree" ? "bg-accent/20 text-accent" : "text-text-secondary"}`}
            >
              Tree
            </button>
            {hasTable && (
              <button
                type="button"
                onClick={() => setViewMode("table")}
                className={`px-2 py-0.5 text-xs rounded ${viewMode === "table" ? "bg-accent/20 text-accent" : "text-text-secondary"}`}
              >
                Table
              </button>
            )}
            <button
              type="button"
              onClick={() => setViewMode("raw")}
              className={`px-2 py-0.5 text-xs rounded ${viewMode === "raw" ? "bg-accent/20 text-accent" : "text-text-secondary"}`}
            >
              Raw
            </button>
          </div>

          <div className="font-mono text-xs overflow-x-auto max-h-64 overflow-y-auto">
            {entry.response.error ? (
              <div className="text-error">{entry.response.error}</div>
            ) : viewMode === "table" && arrayData ? (
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-border">
                    {Object.keys(arrayData[0]).map((key) => (
                      <th key={key} className="px-2 py-1 text-text-secondary font-normal">{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {arrayData.map((row, i) => (
                    <tr key={i} className="border-b border-border/50">
                      {Object.values(row).map((val, j) => (
                        <td key={j} className="px-2 py-1">{String(val ?? "")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : viewMode === "tree" ? (
              <JsonTree data={entry.response.data} />
            ) : (
              <pre>{JSON.stringify(entry.response.data, null, 2)}</pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
});
