// frontend/src/components/commands/CommandInput.tsx

import { useState, useMemo, useRef } from "react";
import { useCommandStore } from "../../stores/commandStore";

interface CommandInputProps {
  onExecute: () => void;
}

export function CommandInput({ onExecute }: CommandInputProps) {
  const rawInput = useCommandStore((s) => s.rawInput);
  const setRawInput = useCommandStore((s) => s.setRawInput);
  const capabilities = useCommandStore((s) => s.capabilities);
  const isExecuting = useCommandStore((s) => s.isExecuting);

  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Parse "domain.command param=value"
  const parsed = useMemo(() => {
    const parts = rawInput.trim().split(/\s+/);
    const [domainCmd, ...paramParts] = parts;
    const [domain, ...cmdParts] = (domainCmd ?? "").split(".");
    const command = cmdParts.join(".");
    const params: Record<string, string> = {};
    for (const p of paramParts) {
      const eq = p.indexOf("=");
      if (eq > 0) {
        params[p.slice(0, eq)] = p.slice(eq + 1);
      }
    }
    return { domain, command, params };
  }, [rawInput]);

  // Autocomplete suggestions
  const suggestions = useMemo(() => {
    if (!rawInput.includes(".") && rawInput.length > 0) {
      // Domain-level suggestions
      return capabilities
        .filter((d) => d.name.startsWith(rawInput))
        .flatMap((d) => d.commands.map((c) => `${d.name}.${c.name}`));
    }
    if (parsed.domain && !parsed.command) {
      const domain = capabilities.find((d) => d.name === parsed.domain);
      return (domain?.commands ?? []).map((c) => `${parsed.domain}.${c.name}`);
    }
    return [];
  }, [rawInput, parsed, capabilities]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      onExecute();
    }
  };

  return (
    <div className="relative">
      <div className="flex gap-2">
        <input
          ref={inputRef}
          value={rawInput}
          onChange={(e) => {
            setRawInput(e.target.value);
            setShowSuggestions(true);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          placeholder="domain.command param=value..."
          disabled={isExecuting}
          className="flex-1 bg-bg-tertiary border border-border rounded px-3 py-2 text-sm font-mono
                     focus:outline-none focus:border-accent placeholder:text-text-secondary
                     disabled:opacity-50"
        />
        <button
          onClick={onExecute}
          disabled={isExecuting || !rawInput.trim()}
          className="px-4 py-2 bg-accent text-white text-sm rounded hover:bg-accent/80
                     disabled:opacity-50 disabled:cursor-not-allowed font-mono"
        >
          {isExecuting ? "..." : "⌘"}
        </button>
      </div>

      {/* Autocomplete dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-bg-tertiary border border-border rounded
                        max-h-48 overflow-y-auto z-10">
          {suggestions.slice(0, 15).map((s) => (
            <button
              key={s}
              onMouseDown={() => {
                setRawInput(s + " ");
                setShowSuggestions(false);
                inputRef.current?.focus();
              }}
              className="w-full text-left px-3 py-1.5 text-xs font-mono hover:bg-bg-secondary"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
