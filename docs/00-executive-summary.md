# Executive Summary

**Quantum Heist** is a co-op cyber-heist strategy game where the core mechanic
is time itself. Players plan and execute heists on a deterministic simulation,
then exploit the **Quantum Echo Engine (QEE)** to predict futures, fork
timelines, and collapse the ones they don't like.

## The pitch

> *Every heist you'll ever run, you've already run — in a timeline you chose
> not to keep.*

A crew of 1–4 operators infiltrates procedurally-assembled facilities. Guards
patrol on fixed, learnable routes. Every action advances a global tick. Because
the simulation is fully deterministic, the engine can show each player honest
echoes of their own possible futures — and let them walk into one.

## Design pillars

1. **Determinism is the mechanic.** No hidden dice. If the engine shows you a
   future, that future is real — until *you* change something.
2. **Plans, not reflexes.** Success comes from reading patrol routes and
   forking smart branches, not twitch skill.
3. **Fair play always.** All paid content is cosmetic. Power is earned in the
   simulation, never at the checkout.
4. **The engine is the product.** QEE is a reusable, server-authoritative
   simulation core — the same code powers single-player, co-op, and the
   anti-cheat replay validator.

## What exists in this repository today

| Layer | Status |
| --- | --- |
| QEE design spec (`docs/04-quantum-echo-engine.md`) | Written to match the code |
| Deterministic heist sim + QEE core (`backend/app/engine/`) | Implemented, unit-tested |
| FastAPI session API (`backend/app/main.py`) | Implemented |
| Next.js client (`frontend/`) | Next milestone |
| Multiplayer, persistence, AI directors | Designed in docs, built after the core loop is fun |

## Why this build order

The riskiest assumption is not "can we render a city" — it is **"is
timeline-forking fun?"** So the first milestone is a playable, deterministic
core loop: one map, guards, forking, prediction, collapse. Everything else
(economy, battle pass, tournaments) is downstream of that answer.
