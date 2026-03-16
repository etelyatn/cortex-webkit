// frontend/src/components/commands/JsonTree.tsx

import { useState, memo } from "react";

interface JsonTreeProps {
  data: unknown;
  depth?: number;
}

export const JsonTree = memo(function JsonTree({ data, depth = 0 }: JsonTreeProps) {
  const [expanded, setExpanded] = useState(depth < 2);

  if (data === null || data === undefined) {
    return <span className="text-text-secondary">null</span>;
  }

  if (typeof data === "string") {
    return <span className="text-success">"{data}"</span>;
  }

  if (typeof data === "number" || typeof data === "boolean") {
    return <span className="text-warning">{String(data)}</span>;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-text-secondary">[]</span>;
    return (
      <span>
        <button onClick={() => setExpanded(!expanded)} className="text-text-secondary hover:text-text-primary">
          {expanded ? "▾" : "▸"} [{data.length}]
        </button>
        {expanded && (
          <div className="ml-4">
            {data.map((item, i) => (
              <div key={i}>
                <span className="text-text-secondary">{i}: </span>
                <JsonTree data={item} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </span>
    );
  }

  if (typeof data === "object") {
    const entries = Object.entries(data as Record<string, unknown>);
    if (entries.length === 0) return <span className="text-text-secondary">{"{}"}</span>;
    return (
      <span>
        <button onClick={() => setExpanded(!expanded)} className="text-text-secondary hover:text-text-primary">
          {expanded ? "▾" : "▸"} {"{"}...{"}"}
        </button>
        {expanded && (
          <div className="ml-4">
            {entries.map(([key, val]) => (
              <div key={key}>
                <span className="text-accent">{key}</span>
                <span className="text-text-secondary">: </span>
                <JsonTree data={val} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </span>
    );
  }

  return <span>{String(data)}</span>;
});
