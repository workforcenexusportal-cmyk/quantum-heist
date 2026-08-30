# Quantum Echo Engine — Specification

This spec describes the engine implemented in `backend/app/engine/`. Where
the code and this doc disagree, fix one of them — they are meant to be the
same thing.

## 1. Core properties

- **Deterministic**: a timeline's entire future is a pure function of
  `(state, queued actions)`. No wall clock, no RNG (maps are static; the
  seeded-RNG hook exists for procedural maps later).
- **Immutable branches**: a fork snapshots state; the parent is never mutated
  by the child. Timeline identity = `timeline_id`.
- **Total order**: every event happens on an integer tick. Traces record
  per-tick deltas so the client can animate without re-simulating.

## 2. Data structures

### 2.1 State (`engine/models.py`)

```python
Pos       = (row, col)  # ints
CellKind  = Literal["floor", "wall", "vault"]
Actor     = { id, kind: "crew"|"guard", pos, facing, patrol?, patrol_index? }
WorldState = {
    tick: int,
    map: [[CellKind]],
    actors: [Actor],
    vault_hacked: bool,
    compromised: bool,          # a guard saw a crew member
    compromised_at: int | None,
}
```

### 2.2 Timeline tree (`engine/timelines.py`)

```python
TimelineNode = {
    id: str,                    # uuid4 hex
    parent_id: str | None,      # root = None
    state: WorldState,          # snapshot at fork time (or root init)
    status: "active" | "compromised" | "collapsed" | "promoted",
    divergence_tick: int | None # first tick this branch acted differently
}
```

- Exactly one timeline is **primary** at a time (`active` or `promoted`).
- `fork(parent_id)` deep-copies the parent state into a new node.
- `collapse(id, promote=False)` marks the node `collapsed` and re-activates
  its parent; `promote=True` marks it `promoted` and makes it primary.
- Compromised branches are inspectable but never promotable.

## 3. Simulation rules (`engine/sim.py`)

Per tick, in order:

1. **Crew actions resolve.** Each queued action belongs to
   `(timeline, operator)`:
   - `move` + dir: move one cell if the target is walkable, else stay.
   - `hack`: if the operator is orthogonally adjacent to the vault, set
     `vault_hacked = True`.
   - `emp`: stun the **nearest guard within Chebyshev distance 3** for
     **3 ticks** (`stunned_until = tick + 1 + 3`). A stunned guard neither
     moves (its patrol step is skipped) nor sees (its vision check is
     skipped). Out of range → no-op. Implemented in `sim.py`.
   - Actions are consumed after the tick (queue what you need each tick; the
     API accepts one action per operator per tick).
2. **Guards advance.** A guard walks its patrol waypoint list one cell per
   tick, wrapping around. Facing = direction of the step just taken.
3. **Vision.** For each guard: ray-march along `facing` up to
   `sight_range` (default 4). Walls stop the ray. If the ray reaches a crew
   cell → `compromised = True`, `compromised_at = tick`.
4. **Tick counter increments.**

Terminal conditions: `vault_hacked` (win) or `compromised` (loss — the sim
keeps running so the client can show the aftermath, but the timeline is no
longer promotable).

## 4. Prediction (echoes)

`predict(state, actions, ticks)` clones the state, applies the queued actions
per tick (actions may specify a `tick` offset; otherwise they apply on the
first tick), and simulates `ticks` steps. Returns:

```python
PredictionResult = {
    final_state: WorldState,
    compromised: bool,
    compromised_at: int | None,
    vault_hacked: bool,
    trace: [ { tick, actors: [ {id, pos, facing} ], events: [...] } ]
}
```

Prediction never mutates stored timelines. The client renders traces as ghost
overlays.

## 5. Why this design

- **Anti-cheat is free**: the server re-simulates any submitted action log and
  compares final state hashes. A client claiming an impossible outcome
  produces a different hash — rejected.
- **Replays are free**: a replay *is* the action log; determinism reproduces
  the run exactly.
- **Networking is cheap**: the server sends states + traces, not video.
  Bandwidth per tick is a few hundred bytes.
- **The Rig is honest**: because prediction is the same code as the live sim,
  the in-fiction rule "echoes never lie" is literally true. When CLEANROOM
  (adversarial prediction) arrives, it will be a *different* predictor that
  can be wrong — which is what makes it scary.

## 6. Extension points

- `sim.py:step()` is the only place world rules live; gadgets (EMP done,
  decoy/repeater next) are new action kinds resolved in step 1.
- Procedural maps: `maps.py` accepts any ASCII layout; a seeded generator can
  produce layouts without touching the engine.
- Co-op: the action queue is already keyed by actor id; the session layer
  needs per-player ownership of operators (auth), not engine changes.
