"""Deterministic tick simulation for the Quantum Echo Engine.

Rules (docs/04-quantum-echo-engine.md section 3):
1. Crew actions resolve (move / hack / emp). Invalid moves are ignored.
2. Guards advance one cell along their patrol loop; facing = step direction.
   A stunned guard (stunned_until > tick) neither moves nor sees.
3. Vision: each guard ray-marches along facing until a wall, up to sight_range.
   Seeing a crew member compromises the timeline.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .models import Action, Actor, Facing, Pos, WorldState

DIRS: Dict[str, Tuple[int, int]] = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}

SIGHT_RANGE = 4
EMP_STUN_TICKS = 3
EMP_RANGE = 3  # Chebyshev distance from the operator to the target guard


def _walkable(state: WorldState, pos: Pos) -> bool:
    return state.cell(pos) != "wall"


def _sees_crew(state: WorldState, guard: Actor) -> Optional[str]:
    dr, dc = DIRS[guard.facing]
    for dist in range(1, SIGHT_RANGE + 1):
        probe = Pos(row=guard.pos.row + dr * dist, col=guard.pos.col + dc * dist)
        if state.cell(probe) == "wall":
            return None
        for actor in state.actors:
            if actor.kind == "crew" and actor.pos == probe:
                return actor.id
    return None


def _step_guard(state: WorldState, guard: Actor) -> None:
    if state.tick < guard.stunned_until:
        return
    if not guard.patrol:
        return
    target = guard.patrol[guard.patrol_index % len(guard.patrol)]
    if guard.pos == target:
        guard.patrol_index = (guard.patrol_index + 1) % len(guard.patrol)
        target = guard.patrol[guard.patrol_index]
    dr = target.row - guard.pos.row
    dc = target.col - guard.pos.col
    if dr == 0 and dc == 0:
        return
    if dr != 0:
        guard.facing = "S" if dr > 0 else "N"
    else:
        guard.facing = "E" if dc > 0 else "W"
    guard.pos = Pos(
        row=guard.pos.row + (1 if dr > 0 else -1) if dr else guard.pos.row,
        col=guard.pos.col + (1 if dc > 0 else -1) if dc else guard.pos.col,
    )


def _nearest_stunnable_guard(state: WorldState, operator: Actor) -> Optional[Actor]:
    best: Optional[Actor] = None
    best_dist = EMP_RANGE + 1
    for actor in state.actors:
        if actor.kind != "guard":
            continue
        dist = max(abs(actor.pos.row - operator.pos.row),
                   abs(actor.pos.col - operator.pos.col))
        if dist <= EMP_RANGE and dist < best_dist:
            best = actor
            best_dist = dist
    return best


def _apply_action(state: WorldState, action: Action) -> Optional[str]:
    actor = next((a for a in state.actors if a.id == action.operator), None)
    if actor is None or actor.kind != "crew":
        return None
    if action.kind == "emp":
        target = _nearest_stunnable_guard(state, actor)
        if target is None:
            return None
        target.stunned_until = max(target.stunned_until, state.tick + 1 + EMP_STUN_TICKS)
        return f"{actor.id} EMP-stunned {target.id} until tick {target.stunned_until - 1}"
    if action.kind == "hack":
        dr = abs(actor.pos.row - state.vault_pos.row)
        dc = abs(actor.pos.col - state.vault_pos.col)
        if max(dr, dc) == 1:
            state.vault_hacked = True
            return f"{actor.id} hacked the vault"
        return None
    if action.kind == "move":
        if action.dir not in DIRS:
            return None
        dr, dc = DIRS[action.dir]
        nxt = Pos(row=actor.pos.row + dr, col=actor.pos.col + dc)
        if _walkable(state, nxt):
            actor.pos = nxt
            actor.facing = action.dir  # type: ignore[assignment]
    return None


def step(state: WorldState, actions: List[Action]) -> Tuple[WorldState, List[str]]:
    """Advance one tick. Mutates and returns (state, events)."""
    events: List[str] = []
    for action in actions:
        event = _apply_action(state, action)
        if event:
            events.append(event)

    for actor in [a for a in state.actors if a.kind == "guard"]:
        _step_guard(state, actor)

    for actor in [a for a in state.actors if a.kind == "guard"]:
        if state.tick < actor.stunned_until:
            continue
        seen = _sees_crew(state, actor)
        if seen and not state.compromised:
            state.compromised = True
            state.compromised_at = state.tick
            events.append(f"{actor.id} spotted {seen} (tick {state.tick})")

    state.tick += 1
    return state, events


def predict(
    state: WorldState,
    actions_by_tick: Dict[int, List[Action]],
    ticks: int,
) -> Tuple[WorldState, List[str]]:
    """Simulate `ticks` on a deep copy without touching stored state.

    actions_by_tick maps tick-offset (0-based) -> actions for that tick.
    """
    sim_state = state.model_copy(deep=True)
    all_events: List[str] = []
    for offset in range(ticks):
        actions = actions_by_tick.get(offset, [])
        sim_state, events = step(sim_state, actions)
        all_events.extend(events)
        if sim_state.vault_hacked:
            break
    return sim_state, all_events


def facing_between(src: Pos, dst: Pos) -> Facing:
    dr = dst.row - src.row
    dc = dst.col - src.col
    if abs(dr) >= abs(dc):
        return "S" if dr > 0 else "N"
    return "E" if dc > 0 else "W"
