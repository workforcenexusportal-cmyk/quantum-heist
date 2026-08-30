# Vision

## The fantasy

You are a *temporal operator* — a thief who doesn't outrun the guards, but
remembers futures that never happened. The gear is near-future, grounded, and
cool rather than neon-noir: signal forks, dead-drop drones, and a military-grade
echo rig that most people would call impossible and your crew calls Tuesday.

## Tone

Grounded heist thriller with one clean sci-fi twist. Reference points: the
planning-space tension of *Payday* + the deterministic elegance of *Into the
Breach* + the "your choices were real" weight of a good *Outer Wilds* loop.

## Design pillars

### 1. Determinism is the mechanic

No RNG in the sim. Same seed + same actions = same outcome, always. This gives
us prediction, forking, replays, and anti-cheat from one property.

### 2. Plans, not reflexes

The player wins by understanding: guard routes, camera cones, tick budgets.
Failure states are legible — the replay shows exactly which tick broke the
plan.

### 3. Legible failure, earned mastery

When a timeline collapses, the UI highlights the decision that diverged from
the successful echo. Dying is a lesson with a timestamp.

### 4. Fair play always

Monetization is cosmetic-only. The QEE core doubles as the replay validator,
so cheat detection is a byproduct of honest engineering, not a bolt-on.

## Player journey (first 30 minutes)

1. **Tunnel (0–5 min)** — Solo map, two guards, one vault. Learn tick/act.
2. **First echo (5–15 min)** — The rig comes online. Predict 10 ticks. Watch
   your plan fail in the echo. Change one input. Watch it succeed.
3. **First fork (15–25 min)** — At the vault door, fork the timeline: go loud
   vs. wait for the patrol. Both branches play out. Keep the one you like.
4. **First collapse (25–30 min)** — A branch goes wrong; collapse it, promote
   the clean one. The mission completes. The rig hums.

## What we are explicitly not

- Not a shooter-first game (combat exists, but is a plan failure state).
- Not pay-to-win, ever (see `docs/monetization` when written).
- Not lore-heavy at the expense of legibility. Story arrives through
  mission structure, not cutscenes.
