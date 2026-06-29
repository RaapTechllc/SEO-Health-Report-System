"use client";

import { useEffect, useRef, useState } from "react";
import type { AuditApiError, AuditResult } from "@/lib/types";
import ReportView from "@/components/ReportView";

/** Status messages cycled through while the audit runs. */
const LOADING_MESSAGES: readonly string[] = [
  "Fetching the page…",
  "Reading the HTML…",
  "Checking technical SEO signals…",
  "Evaluating content & authority…",
  "Probing AI visibility…",
  "Scoring the three pillars…",
  "Writing up recommendations…",
];

type Phase = "idle" | "loading" | "done" | "error";

function isApiError(value: unknown): value is AuditApiError {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as Record<string, unknown>).error === "string"
  );
}

export default function AuditForm() {
  const [url, setUrl] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AuditResult | null>(null);
  const [messageIndex, setMessageIndex] = useState(0);

  const abortRef = useRef<AbortController | null>(null);
  const loading = phase === "loading";

  // Rotate the loading status messages while an audit is in flight.
  useEffect(() => {
    if (!loading) return;
    setMessageIndex(0);
    const id = window.setInterval(() => {
      setMessageIndex((i) => (i + 1) % LOADING_MESSAGES.length);
    }, 1800);
    return () => window.clearInterval(id);
  }, [loading]);

  // Abort any in-flight request if the component unmounts.
  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  async function runAudit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;

    const trimmed = url.trim();
    if (!trimmed) {
      setError("Please enter a website URL to audit.");
      setPhase("error");
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setPhase("loading");
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: trimmed }),
        signal: controller.signal,
      });

      const payload: unknown = await res.json().catch(() => null);

      if (!res.ok) {
        const message = isApiError(payload)
          ? payload.error
          : `Audit failed (HTTP ${res.status}). Please try again.`;
        setError(message);
        setPhase("error");
        return;
      }

      if (isApiError(payload)) {
        setError(payload.error);
        setPhase("error");
        return;
      }

      setResult(payload as AuditResult);
      setPhase("done");
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while running the audit.",
      );
      setPhase("error");
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl space-y-8">
      <form onSubmit={runAudit} className="card" aria-busy={loading}>
        <label htmlFor="audit-url" className="block text-sm font-medium text-slate-300">
          Website URL
        </label>
        <p id="audit-url-hint" className="mt-1 text-sm text-slate-400">
          Enter any public page. We&apos;ll grade it across technical SEO, content &amp;
          authority, and AI visibility.
        </p>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            id="audit-url"
            name="url"
            type="text"
            inputMode="url"
            autoComplete="url"
            spellCheck={false}
            placeholder="example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
            aria-describedby="audit-url-hint"
            aria-invalid={phase === "error" ? true : undefined}
            className="flex-1 rounded-xl border border-white/10 bg-ink/60 px-4 py-3 text-base text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/50 disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-accent px-6 py-3 text-base font-semibold text-white shadow-lg transition hover:bg-accent/90 focus:outline-none focus:ring-2 focus:ring-accent2/60 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              <>
                <span
                  className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
                  aria-hidden="true"
                />
                Auditing…
              </>
            ) : (
              "Run audit"
            )}
          </button>
        </div>

        <div aria-live="polite" className="mt-4 min-h-[1.5rem]">
          {loading && (
            <p className="flex items-center gap-2 text-sm text-accent2">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent2/70" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-accent2" />
              </span>
              {LOADING_MESSAGES[messageIndex]}
            </p>
          )}
          {phase === "error" && error && (
            <p role="alert" className="text-sm text-bad">
              {error}
            </p>
          )}
        </div>
      </form>

      {phase === "done" && result && <ReportView result={result} />}
    </div>
  );
}
