import AuditForm from "@/components/AuditForm";

const FEATURES: readonly { title: string; detail: string }[] = [
  {
    title: "Three-pillar audit",
    detail: "Technical health, content authority, and AI visibility in one pass.",
  },
  {
    title: "Answer-engine ready",
    detail: "See how ChatGPT, Claude, Perplexity, and Gemini read your site.",
  },
  {
    title: "Actionable fixes",
    detail: "Prioritized recommendations you can ship today, not vague advice.",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[480px] bg-gradient-to-b from-indigo-600/20 via-slate-950/0 to-transparent" />

      <section className="mx-auto flex max-w-3xl flex-col items-center px-6 pt-20 pb-12 text-center sm:pt-28">
        <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-slate-700/70 bg-slate-900/60 px-4 py-1.5 text-xs font-medium uppercase tracking-widest text-indigo-300">
          AI-age SEO
        </span>

        <h1 className="bg-gradient-to-br from-white via-slate-200 to-indigo-300 bg-clip-text text-5xl font-bold tracking-tight text-transparent sm:text-6xl">
          Rankwise
        </h1>

        <p className="mt-5 max-w-xl text-balance text-lg leading-relaxed text-slate-300 sm:text-xl">
          Optimize your site for the answer-engine age. Rankwise audits how
          ChatGPT, Claude, Perplexity, and Gemini discover, read, and recommend
          your pages — not just how Google crawls them.
        </p>

        <ul className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-3 text-sm text-slate-400">
          {FEATURES.map((feature) => (
            <li key={feature.title} className="flex items-center gap-2">
              <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
              <span className="font-medium text-slate-200">{feature.title}</span>
            </li>
          ))}
        </ul>

        <div className="mt-12 w-full">
          <AuditForm />
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-24">
        <div className="grid gap-4 sm:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 text-left"
            >
              <h2 className="text-sm font-semibold text-slate-100">{feature.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{feature.detail}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
            How scoring works
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-slate-400">
            Your overall grade is a weighted blend of three pillars: a single
            number you can track over time.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-slate-800/50 px-4 py-3">
              <p className="text-2xl font-bold text-indigo-300">30%</p>
              <p className="mt-1 text-xs font-medium text-slate-300">Technical</p>
              <p className="mt-0.5 text-xs text-slate-500">
                Crawlability, speed, security, structured data.
              </p>
            </div>
            <div className="rounded-xl bg-slate-800/50 px-4 py-3">
              <p className="text-2xl font-bold text-indigo-300">35%</p>
              <p className="mt-1 text-xs font-medium text-slate-300">Content</p>
              <p className="mt-0.5 text-xs text-slate-500">
                Depth, clarity, headings, and authority signals.
              </p>
            </div>
            <div className="rounded-xl bg-slate-800/50 px-4 py-3">
              <p className="text-2xl font-bold text-indigo-300">35%</p>
              <p className="mt-1 text-xs font-medium text-slate-300">AI Visibility</p>
              <p className="mt-0.5 text-xs text-slate-500">
                How well answer engines can cite and surface you.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
