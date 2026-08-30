"""Pydantic models for the Quantum Heist API and the QEE engine."""

from __future__ import annotations

from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

CellKind = Literal["floor", "wall", "vault"]
Facing = Literal["N", "S", "E", "W"]
ActorKind = Literal["crew", "guard"]


class Actor(BaseModel):
    id: str
    kind: ActorKind
    pos: Tuple[int, int]
    facing: Facing = "S"
    # guards only
    patrol: List[Tuple[int, int]] = Field(default_factory=list)


class WorldState(BaseModel):
    tick: int
    map: List[List[CellKind]]
    actors: List[Actor]
    vault_hacked: bool
    compromised: bool
    compromised_at: Optional[int] = None


class Action(BaseModel):
    actor_id: str
    kind: Literal["move", "hack"]
    dir: Optional[Facing] = None  # required when kind == "move"


class PredictionRequest(BaseModel):
    actions: List[Action]
    ticks: int = Field(default=10, ge=1, le=60)


class PredictionResult(BaseModel):
    final_state: WorldState
    compromised: bool
    compromised_at: Optional[int] = None
    trace: List[WorldState] = Field(default_factory=list)


class TimelineStatus(BaseModel):
    id: str
    status: Literal["active", "compromised", "collapsed", "promoted"]
    divergence_tick: Optional[int] = None
    tick: int
    vault_hacked: bool


class SessionResponse(BaseModel):
    session_id: str
    primary_timeline_id: str
    state: WorldState
