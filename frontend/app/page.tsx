"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import FacilityGrid from "@/components/FacilityGrid";
import TimelinePanel from "@/components/TimelinePanel";
import { api, type Facing, type PredictionResult, type SessionState, type TimelineSummary, type WorldState } from "@/lib/api";

const DIRECTIONS: { dir: Facing; label: string }[] = [
  { dir: "N", label: "↑" },
  { dir: "W", label: "←" },
  { dir: "S", label: "↓" },
  { dir: "E", label: "→" },
];

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unknown connection error";
}

export default function HomePage() {
  const [map, setMap] = useState("tunnel");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [state, setState] = useState<WorldState | null>(null);
  const [timelines, setTimelines] = useState<TimelineSummary[]>([]);
  const [echo, setEcho] = useState<PredictionResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState("Awaiting insertion.");

  const crew = useMemo(
    () => state?.actors.find((actor) => actor.kind === "crew")?.id ?? "crew-1",
    [state],
  );

  const refreshTimelines = useCallback(async (id: string) => {
    setTimelines(await api.timelines(id));
  }, []);

  const startSession = useCallback(async () => {
    setBusy(true);
    setError(null);
    setEcho(null);
    try {
      const result = await api.createSession(map);
      setSessionId(result.session_id);
      setState(result.state);
      await refreshTimelines(result.session_id);
      setNotice(`${map.toUpperCase()} loaded. Operator ${result.state.actors.find((a) => a.kind === "crew")?.id ?? "crew-1"} ready.`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }, [map, refreshTimelines]);

  useEffect(() => {
    void startSession();
  }, [startSession]);

  async function run(action: () => Promise<void>) {
    if (!sessionId) return;
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function move(dir: Facing) {
    if (!sessionId) return;
    await run(async () => {
      await api.queueAction(sessionId, { operator: crew, kind: "move", dir });
      setNotice(`Move ${dir} queued. Press TICK to commit the intent.`);
    });
  }

  async function tick() {
    if (!sessionId) return;
    await run(async () => {
      const result = await api.tick(sessionId);
      setState(result.state);
      setEcho(null);
      await refreshTimelines(sessionId);
      setNotice(`Tick ${result.state.tick} committed.`);
    });
  }

  async function hack() {
    if (!sessionId) return;
    await run(async () => {
      await api.queueAction(sessionId, { operator: crew, kind: "hack" });
      const result = await api.tick(sessionId);
      setState(result.state);
      await refreshTimelines(sessionId);
      setNotice(result.state.vault_hacked ? "VAULT OPEN. Clean extraction." : "Hack queued, but the vault is not adjacent.");
    });
  }

  async function predict() {
    if (!sessionId) return;
    await run(async () => {
      const result = await api.predict(sessionId, [], 8);
      setEcho(result);
      setNotice(result.compromised ? `Echo warns: compromise at tick ${result.compromised_at}.` : "Echo is clean for the next 8 ticks.");
    });
  }

  async function fork() {
    if (!sessionId) return;
    await run(async () => {
      const result = await api.fork(sessionId);
      await refreshTimelines(sessionId);
      setNotice(`Timeline ${result.timeline_id} forked. Continue exploring the branch.`);
    });
  }

  async function collapse(target: string, promote: boolean) {
    if (!sessionId) return;
    await run(async () => {
      await api.collapse(sessionId, target, promote);
      const result: SessionState = await api.getSession(sessionId);
      setState(result.state);
      await refreshTimelines(sessionId);
      setNotice(promote ? `Timeline ${target} promoted to primary.` : `Timeline ${target} collapsed.`);
    });
  }

  return (
    <main className="min-h-screen px-4 py-6 sm:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-6 flex flex-wrap items-end justify-between gap-4 border-b border-[var(--line)] pb-4">
          <div>
            <p className="mb-1 text-xs tracking-[0.35em] text-[var(--accent)]">KESTREL COLLECTIVE // ECHO CONSOLE</p>
            <h1 className="text-3xl font-black tracking-tight">QUANTUM HEIST</h1>
            <p className="mt-1 text-sm text-[var(--muted)]">Every heist you&apos;ll ever run, you&apos;ve already run.</p>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <label htmlFor="map" className="text-[var(--muted)]">FACILITY</label>
            <select id="map" value={map} onChange={(event) => setMap(event.target.value)} disabled={busy} className="rounded border border-[var(--line)] bg-[var(--panel)] px-2 py-2 text-[var(--text)]">
              <option value="tunnel">Tunnel Run</option>
              <option value="office">Meridian Office</option>
            </select>
            <button onClick={() => void startSession()} disabled={busy} className="rounded bg-[var(--accent)] px-3 py-2 font-bold text-[var(--bg)] disabled:opacity-50">NEW HEIST</button>
          </div>
        </header>

        {error && <div className="mb-4 rounded border border-[var(--danger)] bg-[#2a151b] p-3 text-sm text-[var(--danger)]">{error}</div>}

        <section className="grid gap-4 lg:grid-cols-[1fr_340px]">
          <div className="rounded-lg border border-[var(--line)] bg-[var(--panel)] p-4">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3 text-xs">
                <span className="text-[var(--muted)]">SESSION</span><code>{sessionId ?? "—"}</code>
                <span className="text-[var(--muted)]">TICK</span><strong className="text-[var(--accent)]">{state?.tick ?? "—"}</strong>
              </div>
              <div className={`text-xs font-bold ${state?.compromised ? "text-[var(--danger)]" : state?.vault_hacked ? "text-[var(--ok)]" : "text-[var(--muted)]"}`}>
                {state?.compromised ? "● COMPROMISED" : state?.vault_hacked ? "● VAULT SECURED" : "○ UNDETECTED"}
              </div>
            </div>
            <div className="overflow-auto pb-2">
              {state ? <FacilityGrid state={state} echo={echo} /> : <div className="p-12 text-sm text-[var(--muted)]">Connecting to the engine…</div>}
            </div>
            <div className="mt-4 grid gap-4 border-t border-[var(--line)] pt-4 sm:grid-cols-[180px_1fr]">
              <div className="grid grid-cols-3 grid-rows-3 gap-1 text-center">
                <span />
                <button aria-label="Move north" onClick={() => void move("N")} disabled={busy || !state} className="console-button">↑</button>
                <span />
                <button aria-label="Move west" onClick={() => void move("W")} disabled={busy || !state} className="console-button">←</button>
                <button aria-label="Wait" onClick={() => void tick()} disabled={busy || !state} className="console-button text-xs">WAIT</button>
                <button aria-label="Move east" onClick={() => void move("E")} disabled={busy || !state} className="console-button">→</button>
                <span />
                <button aria-label="Move south" onClick={() => void move("S")} disabled={busy || !state} className="console-button">↓</button>
                <span />
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <button onClick={() => void tick()} disabled={busy || !state} className="action-button">TICK</button>
                <button onClick={() => void hack()} disabled={busy || !state} className="action-button border-[#f59e0b] text-[#fbbf24]">HACK</button>
                <button onClick={() => void run(async () => { await api.queueAction(sessionId!, { operator: crew, kind: "emp" }); setNotice("EMP queued. Press TICK to discharge the pulse."); })} disabled={busy || !state} className="action-button border-[#c084fc] text-[#c084fc]">EMP</button>
                <button onClick={() => void predict()} disabled={busy || !state} className="action-button border-[var(--accent-2)] text-[var(--accent-2)]">PREDICT</button>
                <button onClick={() => void fork()} disabled={busy || !state} className="action-button border-[var(--ok)] text-[var(--ok)]">FORK</button>
              </div>
            </div>
            <p className="mt-3 text-xs text-[var(--muted)]">{notice}</p>
          </div>

          <aside className="space-y-4">
            <TimelinePanel timelines={timelines} onCollapse={(id, promote) => void collapse(id, promote)} busy={busy} />
            <div className="rounded-lg border border-[var(--line)] bg-[var(--panel)] p-3 text-xs">
              <h2 className="mb-2 font-bold tracking-wide text-[var(--muted)]">LEGEND</h2>
              <div className="grid grid-cols-2 gap-2">
                <span><b className="mr-2 inline-block h-3 w-3 rounded bg-[var(--accent)]" />OPERATOR</span>
                <span><b className="mr-2 inline-block h-3 w-3 rounded bg-[var(--danger)]" />GUARD</span>
                <span><b className="mr-2 inline-block h-3 w-3 rounded border border-dashed border-[var(--accent)]" />ECHO</span>
                <span><b className="mr-2 inline-block h-3 w-3 rounded bg-[#a16207]" />VAULT</span>
              </div>
            </div>
            {echo && (
              <div className={`rounded-lg border p-3 text-xs ${echo.compromised ? "border-[var(--danger)] bg-[#2a151b]" : "border-[var(--accent)] bg-[#102525]"}`}>
                <h2 className="font-bold">ECHO RESULT</h2>
                <p className="mt-2">Projected tick: {echo.final_state.tick}</p>
                <p>{echo.compromised ? `Compromised at tick ${echo.compromised_at}` : "No compromise detected"}</p>
                <p>{echo.vault_hacked ? "Vault hacked" : "Vault remains locked"}</p>
              </div>
            )}
          </aside>
        </section>
      </div>
    </main>
  );
}
