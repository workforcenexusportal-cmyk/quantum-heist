"""Deterministic world state models for the Quantum Echo Engine."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

CellKind = Literal["floor", "wall", "vault"]
Facing = Literal["N", "S", "E", "W"]
MoveDir = Literal["N", "S", "E", "W"]
ActorKind = Literal["crew", "guard"]
TimelineStatus = Literal["active", "compromised", "collapsed", "promoted"]


class Pos(BaseModel):
    row: int
    col: int


class Actor(BaseModel):
    id: str
    kind: ActorKind
    pos: Pos
    facing: Facing = "S"
    # guards only: fixed patrol loop of cells, walked one cell per tick
    patrol: List[Pos] = Field(default_factory=list)
    patrol_index: int = 0
    # guards only: while tick < stunned_until the guard neither moves nor sees
    stunned_until: int = 0


class WorldState(BaseModel):
    tick: int = 0
    rows: int
    cols: int
    grid: List[List[CellKind]]
    actors: List[Actor]
    vault_pos: Pos
    vault_hacked: bool = False
    compromised: bool = False
    compromised_at: Optional[int] = None

    def cell(self, pos: Pos) -> CellKind:
        if 0 <= pos.row < self.rows and 0 <= pos.col < self.cols:
            return self.grid[pos.row][pos.col]
        return "wall"


class TraceEntry(BaseModel):
    tick: int
    actors: List[Actor]
    events: List[str] = Field(default_factory=list)


class PredictionResult(BaseModel):
    final_state: WorldState
    compromised: bool
    compromised_at: Optional[int] = None
    vault_hacked: bool
    trace: List[TraceEntry]


class TimelineNode(BaseModel):
    id: str
    parent_id: Optional[str] = None
    state: WorldState
    status: TimelineStatus = "active"
    divergence_tick: Optional[int] = None


class TimelineSummary(BaseModel):
    id: str
    parent_id: Optional[str] = None
    status: TimelineStatus
    divergence_tick: Optional[int] = None
    tick: int
    vault_hacked: bool
    compromised: bool
    is_primary: bool


class Action(BaseModel):
    operator: str
    kind: Literal["move", "hack", "emp"]
    dir: Optional[MoveDir] = None  # required when kind == "move"
