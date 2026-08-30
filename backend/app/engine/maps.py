"""Static facility layouts for the Quantum Echo Engine.

ASCII legend: W=wall, .=floor, V=vault, G=guard spawn, C=crew spawn.
Patrols are explicit waypoint loops per guard (all on floor cells).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .models import Actor, Pos, WorldState

CellGrid = List[List[str]]


def _parse(layout: str) -> Tuple[CellGrid, Pos, List[Pos], List[Pos]]:
    lines = [line for line in layout.strip().splitlines() if line.strip()]
    width = len(lines[0]) if lines else 0
    if any(len(line) != width for line in lines):
        raise ValueError("map rows must have equal widths")
    grid: CellGrid = []
    vault = Pos(row=0, col=0)
    guards: List[Pos] = []
    crew: List[Pos] = []
    for r, line in enumerate(lines):
        row: List[str] = []
        for c, ch in enumerate(line):
            if ch == "V":
                vault = Pos(row=r, col=c)
                row.append("vault")
            elif ch == "G":
                guards.append(Pos(row=r, col=c))
                row.append("floor")
            elif ch == "C":
                crew.append(Pos(row=r, col=c))
                row.append("floor")
            elif ch == "W":
                row.append("wall")
            else:
                row.append("floor")
        grid.append(row)
    return grid, vault, guards, crew


_TUNNEL = """
WWWWWWWWWWWW
W..........W
W.WWWWWWWW.W
W.W......W.W
W.C......V.W
W.W......W.W
W.W.GWWWWW.W
W..........W
WWWWWWWWWWWW
"""

# Open central corridor from the crew spawn to the vault approach.
_OFFICE = """
WWWWWWWWWWWWWW
W....W.......W
W.C..W...G...W
W....W.......W
W....W.......W
W............W
W....W.......W
W....W...G...W
W............W
W....W.......W
W....W......VW
W....W......VW
WWWWWWWWWWWWWW
"""

MAPS: Dict[str, str] = {"tunnel": _TUNNEL, "office": _OFFICE}

PATROLS: Dict[str, List[List[Pos]]] = {
    "tunnel": [
        [Pos(row=6, col=4), Pos(row=7, col=4), Pos(row=7, col=10), Pos(row=6, col=10)],
    ],
    "office": [
        [Pos(row=2, col=9), Pos(row=2, col=12), Pos(row=3, col=12), Pos(row=3, col=9)],
        [Pos(row=7, col=9), Pos(row=7, col=12), Pos(row=8, col=12), Pos(row=8, col=9)],
    ],
}


def build_state(name: str) -> WorldState:
    """Build the initial WorldState for a named map."""
    if name not in MAPS:
        raise KeyError(f"unknown map '{name}' (available: {sorted(MAPS)})")
    grid, vault, guards, crew = _parse(MAPS[name])
    actors: List[Actor] = []
    for i, pos in enumerate(crew):
        actors.append(Actor(id=f"crew-{i + 1}", kind="crew", pos=pos))
    for i, pos in enumerate(guards):
        patrol = PATROLS[name][i] if i < len(PATROLS[name]) else [pos]
        actors.append(
            Actor(id=f"guard-{i + 1}", kind="guard", pos=pos, facing="E", patrol=patrol)
        )
    return WorldState(
        rows=len(grid),
        cols=len(grid[0]) if grid else 0,
        grid=grid,  # type: ignore[arg-type]
        actors=actors,
        vault_pos=vault,
    )
