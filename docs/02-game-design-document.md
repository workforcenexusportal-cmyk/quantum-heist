# Game Design Document — Core Loop

This document describes **exactly what the code implements today** and the
near-term extensions. The engine spec with data structures lives in
`04-quantum-echo-engine.md`.

## 1. The world model

### 1.1 Map

A facility is a grid (default 12×9) of cells. Cell kinds:

| Kind | Walkable | Blocks sight | Notes |
| --- | --- | --- | --- |
| `floor` | yes | no | — |
| `wall` | no | yes | — |
| `vault` | no | yes | Objective cell; crew must reach an adjacent floor cell and `hack` it |

Maps are defined as ASCII art in code (easy authoring, diff-friendly):

```
W = wall, . = floor, V = vault, G = guard spawn, C = crew spawn
```

### 1.2 Actors

**Crew (players).** One operator per player. Each tick an operator may either
`move` one cell (4-directional) or `hack` the vault when adjacent. Operators
have no HP in the core loop — getting *seen* is the failure state.

**Guards (deterministic AI).** A guard walks a fixed patrol loop (a list of
waypoints, walked cell-by-cell) and has a facing direction. A guard *sees*
along its facing ray until a wall, up to `sight_range` (default 4).

### 1.3 Ticks

The world advances in discrete ticks. Each tick:

1. Every actor's queued action resolves (move or hack; invalid moves are
   ignored — the actor stays).
2. Guards advance one step along their patrol and update facing.
3. **Vision check**: if any guard sees any operator, the timeline is
   *compromised* (see 2.3).

## 2. The Quantum Echo Engine (player-facing)

### 2.1 Predict (echo)

The client can ask: *simulate the next N ticks with my queued actions and show
me the result.* The engine clones the state, simulates, and returns:

- final grid + actor positions,
- whether the echo got compromised and at which tick,
- a per-tick trace for the UI to animate.

The real timeline is untouched. Echoes are rendered as translucent overlays —
your ghost crew walking a future that hasn't happened.

### 2.2 Fork (branch)

At any tick the player may fork: the current state is snapshotted and the
player continues on a **branch**. Branches are full timelines — they can
themselves be forked, predicted, and collapsed. The engine keeps a branch tree
(a `TimelineNode` tree keyed by timeline id).

Cost model (near-term): forking is free in solo; in co-op it will require a
shared *fork charge* earned by clean play, so forking stays a decision.

### 2.3 Collapse

A branch that gets compromised is not deleted — it stays inspectable, but can
never be promoted. The player may:

- **collapse (discard)** a branch to return to its parent,
- **promote** a clean branch to become the primary timeline.

Win condition: the primary timeline reaches `hacked` on the vault before any
compromise.

### 2.4 Divergence marker

When a branch's state first differs from its parent's continuation (different
action at the same tick), the engine records a **divergence point** — the UI
uses it to show "this is where your plan changed."

## 3. Session API (implemented)

| Route | Purpose |
| --- | --- |
| `POST /sessions` | Create a session (solo). Body: `{ "map": "tunnel|office" }` |
| `GET /sessions/{id}` | Current primary timeline state |
| `POST /sessions/{id}/action` | Queue an action: `{ "operator": "crew-1", "kind": "move", "dir": "N|S|E|W" }` or `{ "kind": "hack" }` |
| `POST /sessions/{id}/tick` | Advance one tick |
| `POST /sessions/{id}/predict` | Echo: `{ "actions": [...], "ticks": N }` |
| `POST /sessions/{id}/fork` | Fork the primary timeline |
| `POST /sessions/{id}/collapse` | `{ "target": "timeline-id", "promote": bool }` |
| `GET /sessions/{id}/timelines` | The branch tree with statuses |

## 4. Near-term roadmap (in priority order)

1. **Co-op ticks** — multiple operators, per-operator action queues (the sim
   already supports N actors; the session layer needs a queue per operator).
2. **Fork charges** — the cost model from 2.2.
3. **Gadgets** (pure sim extensions): `EMP` (**implemented** — stuns the
   nearest guard within Chebyshev range 3 for 3 ticks: it neither moves nor
   sees while `tick < stunned_until`), `decoy` (diverts a facing),
   `repeater` (records 5 actions, replays them).
4. **Procedural facility assembly** — rooms + patrol loops stitched from
   seeded templates.
5. **Replay validation** — server re-simulates the submitted action log and
   compares hashes (anti-cheat falls out of determinism for free).
