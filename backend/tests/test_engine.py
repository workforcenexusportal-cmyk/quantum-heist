"""Tests for the Quantum Echo Engine core."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engine.maps import build_state
from app.engine.models import Action, Pos
from app.engine.sim import predict, step
from app.engine.timelines import TimelineTree


def actions(*specs):
    out = []
    for operator, kind, *rest in specs:
        out.append(Action(operator=operator, kind=kind, dir=rest[0] if rest else None))
    return out


def test_determinism_same_inputs_same_outcome():
    a = build_state("tunnel")
    b = build_state("tunnel")
    plan = actions(("crew-1", "move", "S"), ("crew-1", "move", "E"))
    for tick in range(5):
        step(a, plan if tick < 2 else [])
        step(b, plan if tick < 2 else [])
    assert a.model_dump() == b.model_dump()


def test_invalid_move_ignored():
    state = build_state("tunnel")
    before = next(a for a in state.actors if a.id == "crew-1").pos.model_copy()
    step(state, actions(("crew-1", "move", "N")))  # wall above spawn
    after = next(a for a in state.actors if a.id == "crew-1")
    assert after.pos == before


def test_guard_patrol_and_facing():
    state = build_state("tunnel")
    guard = next(a for a in state.actors if a.id == "guard-1")
    start = guard.pos.model_copy()
    step(state, [])
    assert guard.pos != start
    assert guard.facing in ("N", "S", "E", "W")


def test_vision_compromises_timeline():
    # Stationary guard facing E with crew 2 cells east on a clear floor line.
    state = build_state("tunnel")
    guard = next(a for a in state.actors if a.id == "guard-1")
    crew = next(a for a in state.actors if a.id == "crew-1")
    guard.patrol = []
    guard.pos = Pos(row=7, col=4)
    guard.facing = "E"
    crew.pos = Pos(row=7, col=6)
    state, events = step(state, [])
    assert state.compromised
    assert state.compromised_at == 0
    assert any("spotted" in e for e in events)


def test_wall_blocks_vision():
    state = build_state("tunnel")
    guard = next(a for a in state.actors if a.id == "guard-1")
    crew = next(a for a in state.actors if a.id == "crew-1")
    guard.patrol = []
    guard.pos = Pos(row=7, col=4)
    guard.facing = "E"
    crew.pos = Pos(row=7, col=8)
    state.grid[7][6] = "wall"  # wall between guard and crew
    state, _ = step(state, [])
    assert not state.compromised


def test_hack_requires_adjacency():
    state = build_state("tunnel")
    step(state, actions(("crew-1", "hack")))
    assert not state.vault_hacked


def test_emp_stuns_nearest_guard():
    state = build_state("tunnel")
    guard = next(a for a in state.actors if a.id == "guard-1")
    crew = next(a for a in state.actors if a.id == "crew-1")
    guard.patrol = []
    guard.pos = Pos(row=7, col=6)
    guard.facing = "E"
    crew.pos = Pos(row=7, col=5)  # within EMP range (Chebyshev <= 3)
    state, events = step(state, actions(("crew-1", "emp")))
    assert guard.stunned_until == 4  # tick 0 + 1 + 3
    assert any("EMP-stunned" in e for e in events)
    # While stunned the guard neither moves nor sees: walk the crew past its nose.
    for i in range(3):
        state, _ = step(state, actions(("crew-1", "move", "E")))
    assert not state.compromised  # crew crossed the guard's facing unseen
    assert guard.pos == Pos(row=7, col=6)  # guard never moved
    # Stun expires: the guard sees the crew now standing right ahead.
    state, _ = step(state, [])
    assert state.compromised


def test_emp_out_of_range_does_nothing():
    state = build_state("tunnel")
    guard = next(a for a in state.actors if a.id == "guard-1")
    guard.patrol = []
    guard.pos = Pos(row=7, col=4)
    crew = next(a for a in state.actors if a.id == "crew-1")
    crew.pos = Pos(row=1, col=1)  # far away
    state, events = step(state, actions(("crew-1", "emp")))
    assert guard.stunned_until == 0
    assert not any("EMP" in e for e in events)


def test_emp_predict_is_deterministic():
    a = build_state("tunnel")
    b = build_state("tunnel")
    plan = {0: actions(("crew-1", "emp"))}
    fa, _ = predict(a, plan, 5)
    fb, _ = predict(b, plan, 5)
    assert fa.model_dump() == fb.model_dump()


def test_predict_does_not_mutate_source():
    state = build_state("tunnel")
    before = state.model_dump()
    plan = {0: actions(("crew-1", "move", "E")), 1: actions(("crew-1", "move", "E"))}
    final, _ = predict(state, plan, 5)
    assert state.model_dump() == before
    assert final.tick == 5
    crew = next(a for a in final.actors if a.id == "crew-1")
    assert (crew.pos.row, crew.pos.col) == (4, 4)


def test_prediction_reports_compromise_tick():
    state = build_state("tunnel")
    guard = next(a for a in state.actors if a.id == "guard-1")
    crew = next(a for a in state.actors if a.id == "crew-1")
    guard.patrol = []
    guard.pos = Pos(row=7, col=4)
    guard.facing = "E"
    crew.pos = Pos(row=7, col=6)
    final, _ = predict(state, {}, 3)
    assert final.compromised
    assert final.compromised_at is not None


def test_timeline_fork_collapse_promote():
    tree = TimelineTree(build_state("tunnel"))
    child = tree.fork()
    assert child is not None
    assert tree.get(child).state.tick == 0

    # advance the child, then promote it
    node = tree.get(child)
    new_state, _ = step(node.state, actions(("crew-1", "move", "S")))
    tree.update_state(child, new_state)
    assert tree.get(child).state.tick == 1

    assert tree.collapse(child, promote=True)
    assert tree.primary_id == child

    # compromised branches can never be promoted
    other = tree.fork()
    node2 = tree.get(other)
    bad = node2.state.model_copy(deep=True)
    bad.compromised = True
    bad.compromised_at = 99
    tree.update_state(other, bad)
    assert not tree.collapse(other, promote=True)
    assert tree.collapse(other, promote=False)
    assert tree.get(other).status == "collapsed"


def test_fork_refuses_compromised_source():
    tree = TimelineTree(build_state("tunnel"))
    node = tree.primary()
    bad = node.state.model_copy(deep=True)
    bad.compromised = True
    tree.update_state("root", bad)
    assert tree.fork() is None


def test_office_map_two_guards():
    state = build_state("office")
    guards = [a for a in state.actors if a.kind == "guard"]
    crew = [a for a in state.actors if a.kind == "crew"]
    assert len(guards) == 2
    assert len(crew) == 1
    for _ in range(10):
        state, _ = step(state, [])
    assert not state.compromised  # crew stays behind the office wall


def test_all_map_rows_have_consistent_width():
    for name in ("tunnel", "office"):
        state = build_state(name)
        assert all(len(row) == state.cols for row in state.grid)
