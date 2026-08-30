# Multiplayer Architecture

Scope: co-op heists (1–4 operators), shared timelines, and the server's role
as the single authority over the deterministic sim.

## 1. Core principle: server-authoritative determinism

The Quantum Echo Engine is deterministic, so the server never needs to trust a
client's claim about outcomes. The **server owns the WorldState**; clients own
*intent* (queued actions). Every tick:

1. Clients send actions for the next tick (per operator, one action each).
2. The server collects them until the tick deadline (see 3.2).
3. The server applies `step(state, actions)` and broadcasts the new state +
   event log.

Clients never simulate the *authoritative* timeline. They may run the same
engine locally for **client-side prediction** (instant feedback on their own
moves) and for rendering **echoes** — but the server's state always wins on
reconciliation.

## 2. Session model

### 2.1 Session lifecycle

```
LOBBY → COUNTDOWN → RUNNING → RESOLVED (win | lost | abandoned)
```

- **LOBBY** — host creates the session (`POST /sessions`), shares the
  `session_id`; players join with an operator claim (see 2.2).
- **COUNTDOWN** — 10s ready-check; host starts or the server auto-starts when
  all claimed operators are ready.
- **RUNNING** — tick loop driven by the server (see 3.2).
- **RESOLVED** — vault hacked (win) or all operators disconnected/forfeit
  (lost). Session state is persisted for replays and stats.

### 2.2 Operator ownership

Each player claims one operator (`crew-1`…`crew-4`) at join time; the claim is
enforced server-side: only the owning connection may queue actions for that
operator. Solo play is the degenerate case (one claim, local tick loop via the
REST route).

### 2.3 Shared timelines, individual intent

The timeline tree is session-wide: any player may fork, and any player may
collapse/promote — but:

- **Fork** creates a branch visible to everyone (it's a shared decision
  point, announced in the event feed).
- **Collapse/promote** requires the *fork author* or the *host* (prevents
  griefing a clean branch mid-run).
- Compromised branches auto-lock for everyone (the engine already refuses
  promotion; the session layer also refuses further ticks on them).

## 3. Real-time transport

### 3.1 Protocol

WebSocket per client (Socket.IO-style rooms keyed by `session_id`). Two
channel semantics:

| Direction | Messages |
| --- | --- |
| client → server | `action` (queued intent), `ready`, `fork`, `collapse`, `ping` |
| server → client | `state` (full snapshot), `delta` (per-tick actors + events), `echo` (prediction trace), `lobby`, `error` |

Full `state` snapshots on join, fork, collapse, and every 30 ticks;
lightweight `delta`s (actor positions/facings + events, ~200–400 bytes) on
every other tick.

### 3.2 Tick loop

Server-driven, fixed rate **2 ticks/second** (500 ms budget per tick):

- Actions arriving before the deadline apply to the next tick; late actions
  apply to the tick after (never dropped silently — the event feed says so).
- If no actions arrive, the world still advances (guards walk) — tension
  comes from the clock, not just the guards.
- The loop pauses in LOBBY/COUNTDOWN/RESOLVED.

### 3.3 Latency & reconciliation

- Clients render their own operator instantly (local prediction) and other
  actors from the last `delta`.
- On each `delta`, clients snap remote actors to server positions; if a
  client's local predicted diverges from the authoritative state, the server
  state wins and the divergence is surfaced in the UI (same "legible failure"
  principle as the sim).

## 4. Matchmaking

Phased, simple first:

1. **Friends/party first** — share a lobby code (primary path; heists are a
   communication-heavy genre).
2. **Quick heist** — region-scoped queue by level band + map preference;
   fills solo players into 2–4 crews. Waiting >30s widens the band, >60s
   relaxes region to same-continent.
3. **Cross-region play** — allowed explicitly ("play with a friend abroad");
   the tick loop runs on the *host region's* server, remote players get
   interpolated deltas. Determinism means no simulation drift across regions —
   only input latency differs.

## 5. Sharding & scaling

- **Session shards**: one tick-loop worker per running session (a single
  process owns a session — no distributed state during a run). Sessions are
  cheap (pure in-memory sim), so one worker handles hundreds.
- **Redis** for session registry + lobby queues (which worker owns which
  session); **PostgreSQL** for accounts, results, replays (written at
  RESOLVED, not during the run).
- Horizontal scale = add workers; the registry routes join requests to the
  owning worker. No cross-session state, so no distributed locking.

## 6. Event streaming & persistence

- Every tick's event log is appended to the session's **action log**
  (authoritative record).
- At RESOLVED: action log + final state hash → PostgreSQL (`replays` table).
  The hash is what anti-cheat validates (see `06-security-anticheat.md`).
- Replays double as: spectating, "watch the successful echo", and the
  leaderboard evidence trail.

## 7. Faction battles (post-core)

The deterministic engine makes faction wars tractable: aggregate weekly
per-faction stats (successful heists, clean-run rate, Meridian assets
exposed) computed by background jobs over replay records — no live
cross-session simulation needed. Faction scoreboards are eventually
consistent by design.
