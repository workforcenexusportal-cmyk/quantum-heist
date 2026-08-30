"use client";

import type { TimelineSummary } from "@/lib/api";

const STATUS_STYLE: Record<TimelineSummary["status"], string> = {
  active: "text-[var(--accent)]",
  promoted: "text-[var(--ok)]",
  compromised: "text-[var(--danger)]",
  collapsed: "text-[var(--muted)] line-through",
};

export default function TimelinePanel({
  timelines,
  onCollapse,
  busy,
}: {
  timelines: TimelineSummary[];
  onCollapse: (id: string, promote: boolean) => void;
  busy: boolean;
}) {
  return (
    <div className="rounded-lg border border-[var(--line)] bg-[var(--panel)] p-3">
      <h2 className="mb-2 text-sm font-bold tracking-wide text-[var(--muted)]">
        TIMELINES
      </h2>
      <ul className="space-y-1 text-xs">
        {timelines.map((t) => (
          <li
            key={t.id}
            className="flex items-center justify-between gap-2 rounded px-2 py-1 hover:bg-[var(--panel-2)]"
          >
            <span className="flex items-center gap-2">
              <span className="font-bold text-[var(--text)]">
                {t.is_primary ? "★" : "·"} {t.id}
              </span>
              <span className={STATUS_STYLE[t.status]}>{t.status}</span>
              <span className="text-[var(--muted)]">t={t.tick}</span>
              {t.vault_hacked && (
                <span className="text-[var(--ok)]">VAULT ✓</span>
              )}
              {t.compromised && (
                <span className="text-[var(--danger)]">SEEN</span>
              )}
            </span>
            {!t.is_primary && (
              <span className="flex gap-1">
                <button
                  disabled={busy}
                  onClick={() => onCollapse(t.id, false)}
                  className="rounded border border-[var(--line)] px-2 py-0.5 hover:bg-[var(--panel-2)] disabled:opacity-40"
                >
                  collapse
                </button>
                <button
                  disabled={busy || t.compromised}
                  onClick={() => onCollapse(t.id, true)}
                  className="rounded border border-[var(--accent)] px-2 py-0.5 text-[var(--accent)] hover:bg-[var(--panel-2)] disabled:opacity-40"
                  title={
                    t.compromised
                      ? "Compromised branches can never be promoted"
                      : "Promote to primary"
                  }
                >
                  promote
                </button>
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
