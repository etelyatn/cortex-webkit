// frontend/src/lib/api.ts

const BASE = "";  // Same origin (proxied in dev)

function getToken(): string {
  // Token embedded in HTML by server (localhost) or entered by user (remote)
  return (window as any).__CORTEX_TOKEN__ ?? localStorage.getItem("cortex_token") ?? "";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
      ...options.headers,
    },
  });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${resp.status}`);
  }

  return resp.json();
}

export const api = {
  getStatus: () => request<any>("/api/status"),
  getCapabilities: () => request<any>("/api/capabilities"),
  executeCommand: (body: any) => request<any>("/api/commands", { method: "POST", body: JSON.stringify(body) }),
  getSessions: () => request<{ sessions: any[] }>("/api/sessions"),
  createSession: (body?: any) => request<any>("/api/sessions", { method: "POST", body: JSON.stringify(body ?? {}) }),
  getSession: (id: string) => request<any>(`/api/sessions/${id}`),
  deleteSession: (id: string) => request<any>(`/api/sessions/${id}`, { method: "DELETE" }),
  getSettings: () => request<any>("/api/settings"),
  updateSettings: (body: any) => request<any>("/api/settings", { method: "PUT", body: JSON.stringify(body) }),
  startEditor: () => request<{ state: string; started_at: number }>("/api/editor/start", { method: "POST" }),
  stopEditor: () => request<{ state: string }>("/api/editor/stop", { method: "POST" }),
  restartEditor: () => request<{ state: string; started_at: number }>("/api/editor/restart", { method: "POST" }),
  getEditorStatus: () => request<{ state: string; started_at: number | null; error: string | null; port: number | null; pid: number | null; project: string | null }>("/api/editor/status"),
};
