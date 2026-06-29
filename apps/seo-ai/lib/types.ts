// Shared data contracts for the SEO-AI audit pipeline.
// Every analyzer, the scoring engine, the API route, and the UI depend on these.
// Do NOT change a field without updating all consumers.

export type Grade = "A" | "B" | "C" | "D" | "F";

export type PillarKey = "technical" | "content" | "aiVisibility";

export type CheckStatus = "pass" | "warn" | "fail" | "info";

/** Pillar weights for the overall score. Must sum to 1.0. */
export const PILLAR_WEIGHTS: Record<PillarKey, number> = {
  technical: 0.3,
  content: 0.35,
  aiVisibility: 0.35,
};

export const PILLAR_LABELS: Record<PillarKey, string> = {
  technical: "Technical SEO",
  content: "Content & Authority",
  aiVisibility: "AI Visibility",
};

/** A single graded check inside a pillar. */
export interface CheckResult {
  id: string;
  label: string;
  status: CheckStatus;
  detail: string;
  /** Points awarded, 0..max. */
  score: number;
  /** Maximum points this check can contribute. */
  max: number;
}

export interface Recommendation {
  id: string;
  pillar: PillarKey;
  priority: "high" | "medium" | "low";
  title: string;
  /** What to do, concretely. */
  detail: string;
  /** Why it matters for AI-age SEO. */
  impact: string;
}

export interface PillarScore {
  key: PillarKey;
  label: string;
  /** Normalized 0..100. */
  score: number;
  grade: Grade;
  checks: CheckResult[];
  summary: string;
}

/** Normalized page data produced by the fetcher and consumed by analyzers. */
export interface PageData {
  url: string;
  finalUrl: string;
  status: number;
  ok: boolean;
  html: string;
  headers: Record<string, string>;
  title: string | null;
  metaDescription: string | null;
  canonical: string | null;
  robotsMeta: string | null;
  headings: Array<{ level: number; text: string }>;
  links: Array<{ href: string; text: string; internal: boolean }>;
  images: Array<{ src: string; alt: string | null }>;
  jsonLd: unknown[];
  openGraph: Record<string, string>;
  text: string;
  wordCount: number;
  robotsTxt: string | null;
  sitemapXml: string | null;
  https: boolean;
  loadMs: number;
  /** Populated when the fetch failed; analyzers should degrade gracefully. */
  error?: string;
}

/** Output of the AI-visibility analyzer (may be live or mocked). */
export interface AiVisibilityResult {
  score: number; // 0..100
  summary: string;
  checks: CheckResult[];
  recommendations: Recommendation[];
  /** True if a live model produced this; false for deterministic fallback. */
  usedLiveAI: boolean;
}

export interface AuditResult {
  url: string;
  finalUrl: string;
  fetchedAt: string; // ISO timestamp
  overallScore: number; // 0..100
  grade: Grade;
  pillars: PillarScore[];
  recommendations: Recommendation[];
  aiSummary: string;
  meta: {
    title: string | null;
    description: string | null;
    durationMs: number;
    usedLiveAI: boolean;
    error?: string;
  };
}

export interface AuditRequest {
  url: string;
}

export interface AuditApiError {
  error: string;
}
