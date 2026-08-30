# Quantum Heist

A co-op cyber-heist strategy game built around the **Quantum Echo Engine (QEE)** —
a deterministic simulation where every heist is a branching timeline you can
rewind, fork, and collapse.

## Status

Early build. Docs and code grow together:

- `docs/` — game design, engine spec, architecture
- `backend/` — FastAPI + deterministic heist simulation (the QEE core)
- `frontend/` — Next.js client (planned next)

## Quick start (backend)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# API docs at http://127.0.0.1:8000/docs
```

Run the engine tests:

```bash
pytest
```

## The Quantum Echo Engine in one paragraph

A heist is a deterministic state machine: a grid map, guards with fixed patrol
routes, and a crew of operators. Every player action advances the world by one
tick. Because the sim is fully deterministic (seeded RNG, no wall-clock), the
engine can:

1. **Predict** — simulate N ticks ahead without mutating the real timeline.
2. **Fork** — snapshot the state and explore an alternate branch ("what if I
   cut the power instead?").
3. **Collapse** — discard a branch, or promote it to the primary timeline.

Players see echoes of their own possible futures — the flagship mechanic is
just applied determinism.

## Docs map

| Doc | Contents |
| --- | --- |
| `docs/00-executive-summary.md` | Pitch, pillars, scope of the build |
| `docs/01-vision.md` | Fantasy, tone, design pillars |
| `docs/02-game-design-document.md` | Systems spec the code implements |
| `docs/03-story-bible.md` | World, factions, characters |
| `docs/04-quantum-echo-engine.md` | Engine spec: data structures, algorithms |
| `docs/05-multiplayer-architecture.md` | Co-op sessions, sync, matchmaking, sharding |
| `docs/06-security-anticheat.md` | Replay validation, zero trust, economy integrity |
| `docs/07-monetization.md` | Cosmetic-only store, battle pass, founder pack |
| `docs/08-analytics.md` | KPIs, funnels, experimentation framework |
