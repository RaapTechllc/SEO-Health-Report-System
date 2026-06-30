import type { AuditResult, PillarScore } from "@/lib/types";
import { gradeColor } from "@/lib/utils";
import ScoreGauge from "@/components/ScoreGauge";
import PillarCard from "@/components/PillarCard";
import Recommendations from "@/components/Recommendations";

export default function ReportView({ result }: { result: AuditResult }) {
  const host = (() => {
    try {
      return new URL(result.finalUrl).host;
    } catch {
      return result.finalUrl;
    }
  })();

  return (
    <div className="space-y-8">
      <header className="flex flex-col items-start gap-6 rounded-2xl border border-slate-800 bg-slate-900/50 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            AI-Age SEO Report
          </p>
          <h1 className="mt-1 truncate text-2xl font-semibold text-slate-100">
            {host}
          </h1>
          <a
            href={result.finalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 block truncate text-sm text-slate-400 hover:text-slate-200"
          >
            {result.finalUrl}
          </a>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <span className={`font-semibold ${gradeColor(result.grade)}`}>
              Grade {result.grade}
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400">
              {Math.round(result.overallScore)}/100 overall
            </span>
            <span className="text-slate-600">•</span>
            <span
              className={
                result.meta.usedLiveAI
                  ? "rounded-full bg-good/10 px-2 py-0.5 font-medium text-good"
                  : "rounded-full bg-slate-700/40 px-2 py-0.5 font-medium text-slate-400"
              }
            >
              {result.meta.usedLiveAI ? "Live Claude" : "Heuristic"}
            </span>
          </div>
        </div>
        <div className="shrink-0">
          <ScoreGauge score={result.overallScore} grade={result.grade} />
        </div>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {result.pillars.map((pillar: PillarScore) => (
          <PillarCard key={pillar.key} pillar={pillar} />
        ))}
      </section>

      {result.aiSummary ? (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Executive Summary
          </h2>
          <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-slate-200">
            {result.aiSummary}
          </p>
        </section>
      ) : null}

      <section>
        <Recommendations items={result.recommendations} />
      </section>
    </div>
  );
}
