"""Timeline tree for the Quantum Echo Engine.

Tracks branches: fork, collapse, promote, and status queries.
See docs/04-quantum-echo-engine.md section 2.2.
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from .models import TimelineNode, TimelineSummary, WorldState


class TimelineTree:
    """Tracks branches: fork, collapse, promote, and status queries."""

    def __init__(self, root_state: WorldState) -> None:
        root = TimelineNode(id="root", parent_id=None, state=root_state)
        self.nodes: Dict[str, TimelineNode] = {"root": root}
        self.primary_id: str = root.id

    def fork(self, from_id: Optional[str] = None) -> Optional[str]:
        """Fork the given timeline (defaults to primary). Returns new id."""
        src = self.nodes.get(from_id or self.primary_id)
        if src is None or src.status in ("collapsed", "compromised"):
            return None
        child_id = uuid.uuid4().hex[:8]
        self.nodes[child_id] = TimelineNode(
            id=child_id,
            parent_id=src.id,
            state=src.state.model_copy(deep=True),
        )
        return child_id

    def get(self, timeline_id: Optional[str] = None) -> Optional[TimelineNode]:
        return self.nodes.get(timeline_id or self.primary_id)

    def primary(self) -> TimelineNode:
        return self.nodes[self.primary_id]

    def update_state(self, timeline_id: str, state: WorldState) -> None:
        node = self.nodes.get(timeline_id)
        if node is not None:
            node.state = state
            if state.compromised:
                node.status = "compromised"

    def collapse(self, timeline_id: str, promote: bool = False) -> bool:
        """Collapse a branch. If promote, make it primary; else return to parent."""
        node = self.nodes.get(timeline_id)
        if node is None or node.id == self.primary_id:
            return False
        if node.status == "compromised" and promote:
            return False  # compromised branches can never be promoted
        if promote:
            node.status = "promoted"
            self.primary_id = node.id
            return True
        node.status = "collapsed"
        parent = self.nodes.get(node.parent_id) if node.parent_id else None
        if parent is not None and parent.status in ("active", "promoted"):
            self.primary_id = parent.id
        return True

    def summaries(self) -> List[TimelineSummary]:
        out: List[TimelineSummary] = []
        for node in self.nodes.values():
            out.append(
                TimelineSummary(
                    id=node.id,
                    parent_id=node.parent_id,
                    status=node.status,
                    divergence_tick=node.divergence_tick,
                    tick=node.state.tick,
                    vault_hacked=node.state.vault_hacked,
                    compromised=node.state.compromised,
                    is_primary=node.id == self.primary_id,
                )
            )
        return out
