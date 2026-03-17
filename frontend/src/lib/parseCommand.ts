// frontend/src/lib/parseCommand.ts

export interface ParsedCommand {
  domain: string;
  command: string;
  params: Record<string, string>;
}

export function parseCommandInput(raw: string): ParsedCommand {
  const parts = raw.trim().split(/\s+/);
  const [domainCmd = "", ...paramParts] = parts;
  const dotIdx = domainCmd.indexOf(".");
  const domain = dotIdx >= 0 ? domainCmd.slice(0, dotIdx) : domainCmd;
  const command = dotIdx >= 0 ? domainCmd.slice(dotIdx + 1) : "";
  const params: Record<string, string> = {};
  for (const p of paramParts) {
    const eq = p.indexOf("=");
    if (eq > 0) {
      params[p.slice(0, eq)] = p.slice(eq + 1);
    }
  }
  return { domain, command, params };
}
