"""Session store for the Quantum Heist API."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .maps import build_state
from .models import Action, PredictionResult, TraceEntry, WorldState
from .replays import ReplayMetadata, utc_now
from .sim import predict, step
from .timelines import TimelineTree


class Session:
    """One heist session: a timeline tree plus per-tick action queues."""

    def __init__(self, map_name: str) -> None:
        self.id = uuid.uuid4().hex[:12]
        self.map_name = map_name
        self.tree = TimelineTree(build_state(map_name))
        self.pending: Dict[str, Action] = {}
        self.actions: List[Action] = []
        self.started_at = utc_now()
        self.completed_replay: Optional[ReplayMetadata] = None

    def queue_action(self, action: Action) -> None:
        """Queue one action per operator for the next tick (last wins)."""
        self.pending[action.operator] = action

    def tick(self) -> WorldState:
        node = self.tree.primary()
        actions = list(self.pending.values())
        self.pending.clear()
        self.actions.extend(action.model_copy(deep=True) for action in actions)
        new_state, _events = step(node.state, actions)
        self.tree.update_state(node.id, new_state)
        self._complete_if_terminal(new_state)
        return new_state

    def _complete_if_terminal(self, state: WorldState) -> None:
        if self.completed_replay is not None or not (state.vault_hacked or state.compromised):
            return
        canonical_actions = [action.model_dump(mode="json") for action in self.actions]
        canonical_state = state.model_dump(mode="json")
        digest = hashlib.sha256(
            json.dumps(
                {"session_id": self.id, "actions": canonical_actions, "final_state": canonical_state},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.completed_replay = ReplayMetadata(
            replay_id=uuid.uuid4().hex,
            session_id=self.id,
            map_name=self.map_name,
            outcome="won" if state.vault_hacked else "compromised",
            started_at=self.started_at,
            completed_at=utc_now(),
            start_tick=0,
            final_tick=state.tick,
            action_count=len(self.actions),
            actions=[action.model_copy(deep=True) for action in self.actions],
            final_state=state.model_copy(deep=True),
            final_state_hash=digest,
            compromised_at=state.compromised_at,
        )

    def predict(self, actions_by_tick: Dict[int, List[Action]], ticks: int) -> PredictionResult:
        """Echo: simulate ahead on a copy of the primary timeline."""
        final_state, events = predict(self.tree.primary().state, actions_by_tick, ticks)
        trace = [TraceEntry(tick=final_state.tick, actors=final_state.actors, events=events)]
        return PredictionResult(
            final_state=final_state,
            compromised=final_state.compromised,
            compromised_at=final_state.compromised_at,
            vault_hacked=final_state.vault_hacked,
            trace=trace,
        )

    def fork(self, from_id: Optional[str] = None) -> Optional[str]:
        return self.tree.fork(from_id)

    def collapse(self, timeline_id: str, promote: bool = False) -> bool:
        return self.tree.collapse(timeline_id, promote=promote)

    def summaries(self):
        return self.tree.summaries()
