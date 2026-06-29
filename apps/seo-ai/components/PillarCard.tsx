"use client";

import { useState } from "react";
import type { PillarScore } from "@/lib/types";
import { gradeColor, statusColor } from "@/lib/utils";

export default function PillarCard({ pillar }: { pillar: PillarScore }) {
  const [open, setOpen] = useState(false);
  const score = Math.round(pillar.score);

  return (
    <div className="card">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="block w-full text-left"
      >
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-base font-semibold leading-snug text-slate-100">{pillar.label}</h3>
          <div className="flex shrink-0 items-baseline gap-1">
            <span className="text-2xl font-bold tabular-nums text-slate-100">{score}</span>
            <span className="text-xs text-slate-500">/100</span>
          </div>
        </div>
        <div className="mt-1">
          <span
            className={`inline-block rounded-md bg-white/5 px-2 py-0.5 text-xs font-semibold ${gradeColor(
              pillar.grade,
            )}`}
          >
            Grade {pillar.grade}
          </span>
        </div>
        <p className="mt-2 text-sm text-slate-400">{pillar.summary}</p>
      </button>

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="mt-3 text-xs font-medium text-slate-400 hover:text-slate-200"
      >
        {open ? "Hide" : "Show"} {pillar.checks.length} check
        {pillar.checks.length === 1 ? "" : "s"}
        <span aria-hidden="true">{open ? " ▲" : " ▼"}</span>
      </button>

      {open && (
        <ul className="mt-3 space-y-2 border-t border-slate-800 pt-3">
          {pillar.checks.map((check) => (
            <li key={check.id} className="flex items-start gap-2">
              <span
                aria-hidden="true"
                className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${statusColor(
                  check.status,
                ).replace("text-", "bg-")}`}
              />
              <div className="min-w-0">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-sm font-medium text-slate-200">{check.label}</span>
                  <span className="shrink-0 text-xs tabular-nums text-slate-500">
                    {check.score}/{check.max}
                  </span>
                </div>
                <p className={`text-xs ${statusColor(check.status)}`}>{check.detail}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
