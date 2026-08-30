// Typed client for the Quantum Heist session API (backend/app/main.py).

export type CellKind = "floor" | "wall" | "vault";
export type Facing = "N" | "S" | "E" | "W";

export interface Pos {
  row: number;
  col: number;
}

export interface Actor {
  id: string;
  kind: "crew" | "guard";
  pos: Pos;
  facing: Facing;
  patrol?: Pos[];
  patrol_index?: number;
}

export interface WorldState {
  tick: number;
  rows: number;
  cols: number;
  grid: CellKind[][];
  actors: Actor[];
  vault_pos: Pos;
  vault_hacked: boolean;
  compromised: boolean;
  compromised_at: number | null;
}

export interface SessionInfo {
  session_id: string;
  map: string;
  primary_timeline_id: string;
  state: WorldState;
}

export interface SessionState {
  session_id: string;
  primary_timeline_id: string;
  state: WorldState;
}

export interface PredictionResult {
  final_state: WorldState;
  compromised: boolean;
  compromised_at: number | null;
  vault_hacked: boolean;
  trace: {
    tick: number;
    actors: Actor[];
    events: string[];
  }[];
}

export interface TimelineSummary {
  id: string;
  parent_id: string | null;
  status: "active" | "compromised" | "collapsed" | "promoted";
  divergence_tick: number | null;
  tick: number;
  vault_hacked: boolean;
  compromised: boolean;
  is_primary: boolean;
}

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  createSession: (map: string) =>
    post<SessionInfo>("/sessions", { map }),

  getSession: (sessionId: string) =>
    get<SessionState>(`/sessions/${sessionId}`),

  queueAction: (
    sessionId: string,
    action: { operator: string; kind: "move" | "hack" | "emp"; dir?: Facing },
  ) => post<{ queued: boolean }>(`/sessions/${sessionId}/action`, action),

  tick: (sessionId: string) =>
    post<SessionState>(`/sessions/${sessionId}/tick`),

  predict: (
    sessionId: string,
    actions: { operator: string; kind: "move" | "hack" | "emp"; dir?: Facing }[],
    ticks: number,
  ) =>
    post<PredictionResult>(`/sessions/${sessionId}/predict`, {
      actions,
      ticks,
    }),

  fork: (sessionId: string, fromTimeline?: string) =>
    post<{ forked: boolean; timeline_id: string }>(
      `/sessions/${sessionId}/fork`,
      { from_timeline: fromTimeline },
    ),

  collapse: (sessionId: string, target: string, promote: boolean) =>
    post<{ collapsed: boolean; promoted: boolean; primary: string }>(
      `/sessions/${sessionId}/collapse`,
      { target, promote },
    ),

  timelines: (sessionId: string) =>
    get<TimelineSummary[]>(`/sessions/${sessionId}/timelines`),
};
