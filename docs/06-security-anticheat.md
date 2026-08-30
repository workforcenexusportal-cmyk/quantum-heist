# Security & Anti-Cheat

## 1. The big advantage: determinism *is* the anti-cheat

Because the QEE sim is a pure function, the server can verify any claimed
outcome by re-running it:

```
hash(replay(state_seed, action_log)) == hash(claimed_final_state)  →  valid
```

### 1.1 Replay validation (implemented concept, server-side)

- Every session keeps its **action log** (operator, tick, action) — the only
  authoritative input.
- At RESOLVED, a background validator re-simulates the log from the initial
  state and compares the final state hash.
- Mismatch → session flagged, results not scored, replay quarantined for
  manual review. Determinism means zero false positives: any mismatch is a
  tampered log, a race, or an engine bug — all investigable byte-for-byte.

### 1.2 Server authority

- Clients send *intent only* (actions). Positions, vision, compromise, vault
  state — all computed server-side. A modified client cannot "teleport": its
  moves are validated against walkability on the server (invalid moves are
  ignored by the sim itself).
- Echoes/predictions are computed server-side too (the `/predict` route);
  the client's local prediction is a UX optimization, never evidence.

## 2. Threat model & mitigations

| Threat | Mitigation |
| --- | --- |
| Modified client claims impossible outcomes | Replay validation (1.1); unscored until validated |
| Speed-hacking / action flooding | One action per operator per tick, enforced server-side; tick rate fixed by the server |
| Info leaks (seeing through walls) | The server sends only what the actor can know; guard data beyond sight range is coarsened in deltas for untrusted tiers (roadmap) |
| Bot farming (leaderboard/economy) | Behavioral scoring: reaction-time regularity, action entropy, impossible-optimal play detection; replay spot-checks on leaderboard outliers |
| Session hijacking | Short-lived JWT per socket connection, bound to `session_id` + operator claim |
| MITM | TLS 1.2+ everywhere; WebSocket over WSS |
| Griefing (fork/collapse abuse) | Collapse/promote restricted to fork author or host (see `05-multiplayer-architecture.md` §2.3) |

## 3. Account & transport security

- **AuthN**: OAuth (Google/Discord) + email; opaque refresh tokens rotated on
  use, access tokens ≤15 min. Passwords only in the email path (argon2id).
- **AuthZ**: role checks (`player`, `moderator`, `admin`) on every route;
  operator-claim enforcement on every action.
- **Encryption**: TLS in transit; at rest, disk-level encryption plus
  column-level encryption for PII (emails, purchase records). No secrets in
  the DB — secrets live in a managed vault (Azure Key Vault).
- **Zero-trust posture**: every internal service call is authenticated
  (mTLS between services), least-privilege IAM per service, no implicit
  trust from network position. The tick worker, API, and validator each have
  their own identity.

## 4. Infrastructure protection

- **DDoS**: anycast CDN/WAF in front (Azure Front Door), L7 rate limiting per
  IP + per account, WebSocket connection caps per IP. Synthetic-login
  challenges (proof-of-work, not CAPTCHAs) under attack mode.
- **Rate limiting**: token bucket per route class — auth (strict), actions
  (bounded by tick rate anyway), economy/marketplace (moderate). 429s with
  `Retry-After`; repeated abuse → escalating cooldowns.
- **Validation**: every request body through schema validation (pydantic /
  zod); unknown fields rejected; enum-tight enums. The sim itself is the
  final validator — garbage in, no-op out.

## 5. Economy integrity

- All currency mutations are **server-transacted, append-only ledger entries**
  (no `UPDATE balance` — balances are derived from the ledger).
- Marketplace trades settle atomically (DB transaction + row locks on both
  wallets); no client-supplied prices on the settlement path.
- Anomaly jobs flag: impossible income rates, dupe-pattern ledger shapes,
  trade-circle networks (graph analysis over the ledger).
- Fraud prevention on purchases: provider-side receipt validation, velocity
  checks, chargeback → cosmetic suspension (never gameplay punishment for
  payment disputes beyond the disputed item).

## 6. Moderation & admin

- Ban system supports scoped bans (chat, trade, leaderboard, game), duration,
  and reason codes — audited, reversible.
- Every admin action writes to an immutable audit log (actor, target, before,
  after, reason).
- Support tooling reads replays: any flagged session can be re-watched tick by
  tick — determinism makes "what actually happened" a settled question.
