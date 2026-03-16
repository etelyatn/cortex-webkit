// frontend/src/types/commands.ts

export interface CommandRequest {
  domain: string;
  command: string;
  params?: Record<string, unknown>;
}

export interface CommandResponse {
  success: boolean;
  data?: unknown;
  error?: string;
  duration_ms?: number;
}

export interface CapabilityDomain {
  name: string;
  description: string;
  version: string;
  commands: CapabilityCommand[];
}

export interface CapabilityCommand {
  name: string;
  description: string;
  params?: CapabilityParam[];
}

export interface CapabilityParam {
  name: string;
  type: "string" | "integer" | "number" | "boolean" | "array" | "object";
  description?: string;
  required?: boolean;
  default?: unknown;
  enum?: string[];
}

export interface CommandHistoryEntry {
  id: string;
  domain: string;
  command: string;
  params?: Record<string, unknown>;
  response: CommandResponse;
  timestamp: number;
  isFavorite: boolean;
}

export interface Settings {
  model: string;
  effort: string;
  workflow: string;
  access_mode: string;
  directive: string;
  max_sessions: number;
}
