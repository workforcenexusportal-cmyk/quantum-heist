"use client";

import type { Actor, PredictionResult, WorldState } from "@/lib/api";

const CELL: Record<string, string> = {
  wall: "bg-[#232a3a]",
  floor: "bg-[#0f1420]",
  vault: "bg-[#3b2f14] border border-[#a16207]",
};

function actorClass(a: Actor): string {
  if (a.kind === "guard") return "bg-[#f87171] text-[#0b0e14]";
  return "bg-[#5eead4] text-[#0b0e14]";
}

function facingArrow(f: string): string {
  return { N: "▲", S: "▼", E: "▶", W: "◀" }[f] ?? "•";
}

export default function FacilityGrid({
  state,
  echo,
}: {
  state: WorldState;
  echo?: PredictionResult | null;
}) {
  const rows = state.rows;
  const cols = state.cols;

  const cellActors = new Map<string, Actor[]>();
  for (const a of state.actors) {
    const key = `${a.pos.row},${a.pos.col}`;
    cellActors.set(key, [...(cellActors.get(key) ?? []), a]);
  }

  const echoActors = new Map<string, boolean>();
  if (echo) {
    for (const a of echo.final_state.actors) {
      echoActors.set(`${a.pos.row},${a.pos.col}`, a.kind === "guard");
    }
  }

  return (
    <div
      className="inline-grid gap-[2px] rounded-lg border border-[var(--line)] bg-[var(--panel)] p-2"
      style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
    >
      {Array.from({ length: rows }).map((_, r) =>
        Array.from({ length: cols }).map((_, c) => {
          const kind = state.grid[r][c];
          const key = `${r},${c}`;
          const actors = cellActors.get(key) ?? [];
          const hasEcho = echoActors.has(key);
          const echoIsGuard = echoActors.get(key);
          const isVault = kind === "vault";
          const hacked = isVault && state.vault_hacked;
          return (
            <div
              key={key}
              className={`relative flex h-8 w-8 items-center justify-center rounded text-sm font-bold ${CELL[kind]} ${
                hacked ? "!bg-[#14532d] border border-[var(--ok)]" : ""
              }`}
              title={`${r},${c}`}
            >
              {hasEcho && actors.length === 0 && (
                <span
                  className={`absolute inset-1 rounded opacity-40 border border-dashed ${
                    echoIsGuard
                      ? "border-[var(--danger)]"
                      : "border-[var(--accent)]"
                  }`}
                />
              )}
              {actors.map((a) => (
                <span
                  key={a.id}
                  className={`z-10 flex h-6 w-6 items-center justify-center rounded ${actorClass(a)}`}
                  title={`${a.id} (${a.facing})`}
                >
                  {a.kind === "guard" ? facingArrow(a.facing) : a.id.slice(-1)}
                </span>
              ))}
            </div>
          );
        }),
      )}
    </div>
  );
}
