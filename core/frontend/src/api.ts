// Тонкий клиент Aziral Core API.

export interface Scope {
  domains: string[];
  emails: string[];
  usernames: string[];
  hosts: string[];
  ip_ranges: string[];
}

export interface Target {
  id: number;
  name: string;
  description: string;
  scope: Partial<Scope>;
  authorized_by: string;
  created_by: string;
  created_at: string;
}

export interface Job {
  id: number;
  target_id: number;
  tool: string;
  status: "pending" | "running" | "completed" | "failed" | "blocked";
  log: string;
  created_at: string;
}

export interface Entity {
  id: number;
  kind: string;
  value: string;
}

export interface Finding {
  id: number;
  source_tool: string;
  confidence: number;
  raw_json: Record<string, unknown>;
  discovered_at: string;
}

const BASE = "/api";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const api = {
  health: () => http<{ status: string }>("/health"),
  tools: () => http<{ tools: string[] }>("/tools"),
  listTargets: () => http<Target[]>("/targets"),
  getTarget: (id: number) => http<Target>(`/targets/${id}`),
  createTarget: (payload: Partial<Target>) =>
    http<Target>("/targets", { method: "POST", body: JSON.stringify(payload) }),
  listJobs: () => http<Job[]>("/scans"),
  launchScan: (payload: { target_id: number; tool: string; kind: string; value: string }) =>
    http<Job>("/scans", { method: "POST", body: JSON.stringify(payload) }),
  entities: (targetId: number) => http<Entity[]>(`/targets/${targetId}/entities`),
  findings: (targetId: number) => http<Finding[]>(`/targets/${targetId}/findings`),
};
