import type { PillarKey, Recommendation } from "@/lib/types";
import { PILLAR_LABELS } from "@/lib/types";

type Priority = Recommendation["priority"];

const PRIORITY_ORDER: Record<Priority, number> = {
  high: 0,
  medium: 1,
  low: 2,
};

const PRIORITY_PILL: Record<Priority, string> = {
  high: "bg-red-100 text-red-700 ring-1 ring-inset ring-red-200",
  medium: "bg-amber-100 text-amber-700 ring-1 ring-inset ring-amber-200",
  low: "bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200",
};

const PRIORITY_LABEL: Record<Priority, string> = {
  high: "High priority",
  medium: "Medium priority",
  low: "Low priority",
};

function pillarLabel(pillar: PillarKey): string {
  return PILLAR_LABELS[pillar];
}

export default function Recommendations({ items }: { items: Recommendation[] }) {
  if (items.length === 0) {
    return (
      <div className="card flex flex-col items-center justify-center gap-2 py-10 text-center">
        <div
          className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-2xl text-green-600"
          aria-hidden="true"
        >
          ✓
        </div>
        <h3 className="text-lg font-semibold text-slate-800">
          No recommendations — nice work!
        </h3>
        <p className="max-w-md text-sm text-slate-500">
          This page passed the audit cleanly. There are no high-impact fixes to
          make right now. Keep your content fresh and re-run the audit
          periodically.
        </p>
      </div>
    );
  }

  const sorted = [...items].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority],
  );

  return (
    <div className="card">
      <h2 className="mb-1 text-xl font-bold text-slate-900">Recommendations</h2>
      <p className="mb-5 text-sm text-slate-500">
        {sorted.length} {sorted.length === 1 ? "action" : "actions"} to improve
        your AI-age SEO, ordered by priority.
      </p>
      <ul className="flex flex-col gap-4">
        {sorted.map((rec) => (
          <li
            key={rec.id}
            className="rounded-lg border border-slate-200 bg-white p-4"
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${PRIORITY_PILL[rec.priority]}`}
              >
                {PRIORITY_LABEL[rec.priority]}
              </span>
              <span className="text-xs font-medium text-slate-400">
                {pillarLabel(rec.pillar)}
              </span>
            </div>
            <h3 className="text-base font-semibold text-slate-900">
              {rec.title}
            </h3>
            <p className="mt-1 text-sm text-slate-600">{rec.detail}</p>
            <p className="mt-2 text-sm text-slate-500">
              <span className="font-semibold text-slate-700">Impact: </span>
              {rec.impact}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
