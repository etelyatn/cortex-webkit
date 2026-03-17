// frontend/src/components/commands/CommandPanel.tsx

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useCommandStore } from "../../stores/commandStore";
import { useConnectionStore } from "../../stores/connectionStore";
import { useHotkeys } from "../../hooks/useHotkeys";
import { api } from "../../lib/api";
import { parseCommandInput } from "../../lib/parseCommand";
import { CommandInput } from "./CommandInput";
import { ParamForm } from "./ParamForm";
import { ResultCard } from "./ResultCard";

// Static risk classification (loaded from backend at startup or hardcoded subset)
const DESTRUCTIVE_PATTERNS = ["*.delete_asset", "*.delete_actors", "core.shutdown", "level.delete_actors", "data.delete_row", "data.delete_rows"];
const MUTATING_PATTERNS = ["blueprint.compile", "level.spawn_actor", "level.set_property", "data.add_row", "data.update_row", "data.set_tags", "material.set_parameter", "umg.set_property"];

function classifyRisk(domain: string, command: string): "destructive" | "mutating" | "read-only" {
  const full = `${domain}.${command}`;
  for (const pattern of DESTRUCTIVE_PATTERNS) {
    if (pattern.startsWith("*.") ? full.endsWith(pattern.slice(1)) : full === pattern) return "destructive";
  }
  for (const pattern of MUTATING_PATTERNS) {
    if (full === pattern) return "mutating";
  }
  return "read-only";
}

export function CommandPanel() {
  const rawInput = useCommandStore((s) => s.rawInput);
  const setRawInput = useCommandStore((s) => s.setRawInput);
  const history = useCommandStore((s) => s.history);
  const capabilities = useCommandStore((s) => s.capabilities);
  const setCapabilities = useCommandStore((s) => s.setCapabilities);
  const addResult = useCommandStore((s) => s.addResult);
  const toggleFavorite = useCommandStore((s) => s.toggleFavorite);
  const setIsExecuting = useCommandStore((s) => s.setIsExecuting);
  const ueConnected = useConnectionStore((s) => s.ueConnected);
  const [confirmCommand, setConfirmCommand] = useState<{ domain: string; command: string; params: Record<string, unknown> } | null>(null);
  const confirmCancelRef = useRef<HTMLButtonElement>(null);

  // Structured param form state
  const [paramValues, setParamValues] = useState<Record<string, unknown>>({});

  // Load capabilities on mount
  useEffect(() => {
    api.getCapabilities().then((data) => {
      if (data.domains) {
        setCapabilities(data.domains);
      }
    }).catch(() => {});
  }, [setCapabilities]);

  // Parse current input to find matching command schema
  const parsed = useMemo(() => parseCommandInput(rawInput), [rawInput]);

  const matchedCommand = useMemo(
    () => capabilities
      .find((d) => d.name === parsed.domain)
      ?.commands.find((c) => c.name === parsed.command),
    [capabilities, parsed.domain, parsed.command]
  );

  // Focus Cancel button when destructive confirm dialog appears
  useEffect(() => {
    if (confirmCommand) {
      confirmCancelRef.current?.focus();
    }
  }, [confirmCommand]);

  // Bidirectional sync between rawInput and paramValues
  const syncSourceRef = useRef<"raw" | "form" | null>(null);

  // Reverse sync: hydrate paramValues from rawInput (when user types in raw mode)
  useEffect(() => {
    if (syncSourceRef.current === "form") {
      syncSourceRef.current = null;
      return;
    }
    const parts = rawInput.trim().split(/\s+/).slice(1);
    const fromRaw: Record<string, unknown> = {};
    for (const p of parts) {
      const eq = p.indexOf("=");
      if (eq > 0) fromRaw[p.slice(0, eq)] = p.slice(eq + 1);
    }
    setParamValues(fromRaw);
  }, [rawInput]);

  // Forward sync: write structured params back to rawInput
  const handleParamChange = useCallback((key: string, value: unknown) => {
    syncSourceRef.current = "form";
    setParamValues((prev) => {
      const next = { ...prev, [key]: value };
      const base = `${parsed.domain}.${parsed.command}`;
      const paramStr = Object.entries(next)
        .filter(([, v]) => v !== "" && v != null && !Number.isNaN(v))
        .map(([k, v]) => `${k}=${v}`)
        .join(" ");
      setRawInput(paramStr ? `${base} ${paramStr}` : base);
      return next;
    });
  }, [parsed.domain, parsed.command, setRawInput]);

  const doExecute = useCallback(async (domain: string, command: string, params: Record<string, unknown>) => {
    setIsExecuting(true);
    try {
      const resp = await api.executeCommand({ domain, command, params });
      addResult({
        id: crypto.randomUUID(),
        domain,
        command,
        params,
        response: resp,
        timestamp: Date.now(),
        isFavorite: false,
      });
    } catch (err: any) {
      addResult({
        id: crypto.randomUUID(),
        domain,
        command,
        params,
        response: { success: false, error: err.message },
        timestamp: Date.now(),
        isFavorite: false,
      });
    } finally {
      setIsExecuting(false);
    }
  }, [setIsExecuting, addResult]);

  const execute = useCallback(async () => {
    const parts = rawInput.trim().split(/\s+/);
    const [domainCmd, ...paramParts] = parts;
    const [domain, ...cmdParts] = (domainCmd ?? "").split(".");
    const command = cmdParts.join(".");

    if (!domain || !command) return;

    const params: Record<string, unknown> = {};
    for (const p of paramParts) {
      const eq = p.indexOf("=");
      if (eq > 0) {
        params[p.slice(0, eq)] = p.slice(eq + 1);
      }
    }

    const risk = classifyRisk(domain, command);
    if (risk === "destructive") {
      setConfirmCommand({ domain, command, params });
      return;
    }

    await doExecute(domain, command, params);
  }, [rawInput, doExecute]);

  const hotkeys = useMemo(() => [
    { key: "Enter", ctrl: true, handler: () => execute() },
    { key: "l", ctrl: true, handler: () => setRawInput("") },
    { key: ".", ctrl: true, handler: () => useCommandStore.getState().setInputMode(
      useCommandStore.getState().inputMode === "raw" ? "structured" : "raw"
    )},
    { key: "C", ctrl: true, shift: true, handler: () => {
      const data = history[0]?.response?.data;
      if (data !== undefined && data !== null) {
        navigator.clipboard.writeText(JSON.stringify(data, null, 2)).catch(() => {});
      }
    }},
    { key: "d", ctrl: true, handler: () => {
      if (history.length > 0) {
        const last = history[0];
        const paramStr = Object.entries(last.params ?? {}).map(([k, v]) => `${k}=${v}`).join(" ");
        setRawInput(`${last.domain}.${last.command}${paramStr ? " " + paramStr : ""}`);
      }
    }},
    { key: "Escape", handler: () => setConfirmCommand(null) },
  ], [execute, setRawInput, history]);
  useHotkeys(hotkeys);

  return (
    <div className="h-full flex flex-col">
      {/* Destructive command confirmation dialog */}
      {confirmCommand && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-bg-secondary border border-error/40 rounded p-4 max-w-sm space-y-3">
            <div className="text-error font-semibold text-sm">Destructive Command</div>
            <div className="text-xs text-text-primary">
              <span className="font-mono">{confirmCommand.domain}.{confirmCommand.command}</span> may permanently modify or delete data. Are you sure?
            </div>
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                ref={confirmCancelRef}
                onClick={() => setConfirmCommand(null)}
                className="px-3 py-1.5 text-xs bg-bg-tertiary border border-border rounded hover:bg-bg-primary"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => { void doExecute(confirmCommand.domain, confirmCommand.command, confirmCommand.params); setConfirmCommand(null); }}
                className="px-3 py-1.5 text-xs bg-error/20 text-error border border-error/40 rounded hover:bg-error/30"
              >
                Execute
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="p-3 space-y-3 bg-bg-secondary border-b border-border shrink-0">
        <CommandInput onExecute={execute} />
        {matchedCommand?.params && matchedCommand.params.length > 0 && (
          <ParamForm
            params={matchedCommand.params}
            values={paramValues}
            onChange={handleParamChange}
          />
        )}
      </div>

      {/* Result history */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {history.length === 0 ? (
          <div className="text-center text-text-secondary text-sm py-12">
            Type a command above to get started.
            <br />
            <span className="text-xs">e.g., data.list_datatables filter=Enemy*</span>
          </div>
        ) : (
          history.map((entry) => (
            <ResultCard key={entry.id} entry={entry} onToggleFavorite={toggleFavorite} />
          ))
        )}
      </div>

      {/* Status bar */}
      <div className="px-4 py-1.5 flex items-center gap-3 text-xs bg-bg-secondary border-t border-border shrink-0">
        <span className={`flex items-center gap-1 ${ueConnected ? "text-success" : "text-error"}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${ueConnected ? "bg-success" : "bg-error"}`} />
          {ueConnected ? "Connected" : "Disconnected"}
        </span>
        {history.length > 0 && (
          <span className="text-text-secondary">
            Last: {history[0]?.response.duration_ms}ms
          </span>
        )}
      </div>
    </div>
  );
}
