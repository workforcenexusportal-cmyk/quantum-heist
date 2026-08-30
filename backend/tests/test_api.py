"""API tests for terminal mission outcomes and replay metadata."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import REPLAYS, SESSIONS, app

client = TestClient(app)


def setup_function():
    SESSIONS.clear()
    REPLAYS.clear()


def post_action(session_id: str, kind: str, direction: str | None = None):
    body = {"operator": "crew-1", "kind": kind}
    if direction:
        body["dir"] = direction
    assert client.post(f"/sessions/{session_id}/action", json=body).status_code == 200
    return client.post(f"/sessions/{session_id}/tick")


def complete_office(session_id: str):
    # (2,2) -> row 5 left corridor -> row 10 right corridor -> (10,11).
    plan = ["S", "S", "S", "E", "E", "E", "E", "E"] + ["S"] * 5 + ["E"] * 4
    for direction in plan:
        result = post_action(session_id, "move", direction)
        assert result.status_code == 200
        assert result.json()["state"]["compromised"] is False
    return post_action(session_id, "hack")


def test_outcome_is_null_while_session_is_running():
    created = client.post("/sessions", json={"map": "office"}).json()
    response = client.get(f"/sessions/{created['session_id']}/outcome")
    assert response.status_code == 200
    assert response.json() is None


def test_clean_win_persists_replay_metadata():
    created = client.post("/sessions", json={"map": "office"}).json()
    sid = created["session_id"]
    final = complete_office(sid)
    assert final.status_code == 200
    assert final.json()["state"]["vault_hacked"] is True

    outcome = client.get(f"/sessions/{sid}/outcome")
    assert outcome.status_code == 200
    metadata = outcome.json()
    assert metadata["session_id"] == sid
    assert metadata["map_name"] == "office"
    assert metadata["outcome"] == "won"
    assert metadata["action_count"] == 18
    assert len(metadata["final_state_hash"]) == 64
    assert metadata["final_state"]["vault_hacked"] is True

    replay = client.get(f"/replays/{metadata['replay_id']}")
    assert replay.status_code == 200
    assert replay.json()["final_state_hash"] == metadata["final_state_hash"]


def test_compromised_mission_persists_compromise_metadata():
    created = client.post("/sessions", json={"map": "tunnel"}).json()
    sid = created["session_id"]
    session = SESSIONS[sid]
    guard = next(actor for actor in session.tree.primary().state.actors if actor.id == "guard-1")
    crew = next(actor for actor in session.tree.primary().state.actors if actor.id == "crew-1")
    guard.patrol = []
    guard.pos.row, guard.pos.col, guard.facing = 7, 4, "E"
    crew.pos.row, crew.pos.col = 7, 6

    final = client.post(f"/sessions/{sid}/tick")
    assert final.status_code == 200
    assert final.json()["state"]["compromised"] is True

    metadata = client.get(f"/sessions/{sid}/outcome").json()
    assert metadata["outcome"] == "compromised"
    assert metadata["compromised_at"] == 0
    assert metadata["final_state"]["compromised"] is True
    assert metadata["action_count"] == 0
