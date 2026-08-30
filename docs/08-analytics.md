# Analytics & Experimentation

## 1. KPI hierarchy

### North-star metric
**Weekly Completed Clean Heists per Active Player (WCH)** — measures whether
the core loop (plan → fork → collapse → win) is actually being played. A
session with no completed heist is a leak; a player with zero clean runs is
at churn risk.

### Tier 1 (business)

| Metric | Definition | Target (Y1) |
| --- | --- | --- |
| DAU / WAU / MAU | Unique active players per day/week/month | DAU/MAU ≥ 0.22 |
| Stickiness | DAU/WAU | ≥ 0.45 |
| D1 / D7 / D30 retention | New-player cohort returns | 45% / 25% / 12% |
| Churn (monthly) | Active → inactive 28d | ≤ 8% |
| ARPU / ARPPU | Revenue per active / per payer | Season-driven (see `07-monetization.md` §5) |
| Conversion | Active → payer in season | ≥ 3% |

### Tier 2 (loop health)

- **Fork rate per heist** — healthy: 1.5–3 forks. 0 forks = the Rig is being
  ignored (tutorial or UX failure). >5 = players are flailing.
- **Collapse-then-win rate** — players who collapsed a branch and still
  finished: the "second chance feels earned" signal.
- **Prediction usage before commit** — % of heists with ≥1 echo. Should climb
  after the tutorial arc.
- **Median heist length & tick count** — drift upward = difficulty tuning
  issue; sudden drop = exploit hunt (feed to anti-cheat, `06` §2).
- **Compromise tick distribution** — where players get seen. Feeds level
  design directly.

## 2. Funnel analysis

### New player funnel (first session)
```
install → create account → tutorial: tunnel (predict) → first fork
→ first collapse → first clean win → session 2
```
Instrumented per step with drop-off + time-in-step. The two watch-points:
- **first fork** — if <60% of tutorial finishers fork, the concept isn't
  landing (UI or narrative problem).
- **first clean win** — the emotional payoff; time-to-first-win target <25 min.

### Season funnel
```
season start → pass started → pass tier 10 → tier 40 → completed
```
Premium-pass conversion measured at tier 10 (the "hooked" checkpoint), not at
purchase.

## 3. Event instrumentation

- Client events (thin): screen views, UI clicks (fork/collapse buttons),
  client errors.
- Server events (authoritative, from the action log): heist started/ended,
  outcome, ticks, forks, collapses, predictions requested, gadgets used.
- Rule: **the server's action log is the source of truth**; client events are
  UX enrichment only. Determinism gives us perfect replayable telemetry —
  analytics can re-run any heist byte-for-byte.
- Schema: versioned, typed event contracts (breaking changes = new version,
  never mutate old meaning).

## 4. Revenue metrics

- Pass attach rate, direct-cosmetic revenue per season, founder-pack
  sell-through (launch window), subscription MRR + churn.
- Cohort revenue curves by acquisition month; payback on CAC per channel.
- Refund/chargeback rate as a *trust* KPI (target <0.5%) — see `06` §5.

## 5. Experimentation framework

- **Platform**: server-side feature flags with deterministic bucketing
  (`hash(account_id + experiment) % 100`). Deterministic bucketing is a
  natural fit — it's the same hashing discipline as the sim.
- **Assignment units**: account (not device) for progression/economy tests;
  session for UX tests.
- **Guardrail metrics** (auto-halt an experiment): D1 retention, crash rate,
  tick-loop latency p95, refund rate.
- ** cadence**: one primary experiment per fortnight; every experiment ships
  with a pre-registered hypothesis, MDE, and minimum run length (≥2 weeks or
  ≥N players per arm).
- Examples queued: echo-overlay opacity (does clearer prediction increase
  fork rate?), fork-charge economy (free vs. earned charges), tutorial fork
  timing (teach fork before vs. after first compromise).

## 6. Dashboards & operations

- **Live ops board**: concurrent sessions, tick-loop health (p95 step
  latency), error rates — alerting on tick latency regressions (the loop is
  the game).
- **Loop-health board**: Tier 2 metrics per cohort/level band.
- **Revenue board**: season progress, revenue mix vs. `07` §5 targets.
- Data warehouse: events land raw → curated marts (funnel, loop, revenue);
  dashboards refresh hourly, live-ops near-real-time.
- Privacy: no PII in analytics events (account IDs only, pseudonymous);
  GDPR/CCPA deletion propagates to the warehouse.
