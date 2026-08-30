"""Completed mission replay metadata.

The initial backend is intentionally storage-agnostic. This repository uses an
in-memory repository so the API is runnable without PostgreSQL; the metadata
shape is designed to map directly to a future replays table.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .models import Action, WorldState

Outcome = Literal["won", "compromised"]


class ReplayMetadata(BaseModel):
    replay_id: str
    session_id: str
    map_name: str
    outcome: Outcome
    started_at: datetime
    completed_at: datetime
    start_tick: int
    final_tick: int
    action_count: int
    actions: List[Action] = Field(default_factory=list)
    final_state: WorldState
    final_state_hash: str
    compromised_at: Optional[int] = None


class ReplayStore:
    """Small repository abstraction; replace backing dict with PostgreSQL later."""

    def __init__(self) -> None:
        self._items: Dict[str, ReplayMetadata] = {}

    def save(self, replay: ReplayMetadata) -> ReplayMetadata:
        self._items[replay.replay_id] = replay
        return replay

    def get(self, replay_id: str) -> Optional[ReplayMetadata]:
        return self._items.get(replay_id)

    def by_session(self, session_id: str) -> List[ReplayMetadata]:
        return [item for item in self._items.values() if item.session_id == session_id]

    def clear(self) -> None:
        self._items.clear()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
