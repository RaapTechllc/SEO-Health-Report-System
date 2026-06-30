// Full audit pipeline orchestrator.
// Normalizes the URL, fetches the page, runs all three pillar analyzers,
// merges/synthesizes recommendations, and assembles the final AuditResult.
// This function NEVER throws: on any failure it returns a valid, low-scored
// AuditResult with meta.error populated so the UI can render gracefully.

import { fetchPage } from "@/lib/audit/fetchPage";
import { analyzeTechnical } from "@/lib/audit/technical";
import { analyzeContent } from "@/lib/audit/content";
import { analyzeAiVisibility } from "@/lib/audit/aiVisibility";
import {
  PILLAR_LABELS,
  PILLAR_WEIGHTS,
  type AuditResult,
  type CheckResult,
  type Grade,
  type PillarKey,
  type PillarScore,
  type Recommendation,
} from "@/lib/types";
import { normalizeUrl, toGrade } from "@/lib/utils";

const PRIORITY_RANK: Record<Recommendation["priority"], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

const MAX_RECOMMENDATIONS = 12;

/** Run the complete three-pillar audit for a single URL. */
export async function runAudit(url: string): Promise<AuditResult> {
  const startedAt = Date.now();
  const fetchedAt = new Date().toISOString();

  // Normalize first. A bad URL should still yield a valid (failed) result.
  let normalized: string;
  try {
    normalized = normalizeUrl(url);
  } catch (err) {
    return buildErrorResult(url, url, fetchedAt, Date.now() - startedAt, messageOf(err));
  }

  try {
    const page = await fetchPage(normalized);

    const technical = analyzeTechnical(page);
    const content = analyzeContent(page);
    const ai = await analyzeAiVisibility(page);

    const aiPillar: PillarScore = {
      key: "aiVisibility",
      label: PILLAR_LABELS.aiVisibility,
      score: ai.score,
      grade: toGrade(ai.score),
      checks: ai.checks,
      summary: ai.summary,
    };

    const pillars: PillarScore[] = [technical, content, aiPillar];

    const overallScore = Math.round(
      pillars.reduce((sum, p) => sum + p.score * PILLAR_WEIGHTS[p.key], 0),
    );
    const grade = toGrade(overallScore);

    const recommendations = mergeRecommendations(technical, content, ai.recommendations);
    const aiSummary = buildExecutiveSummary(overallScore, grade, pillars, page.error);

    return {
      url: normalized,
      finalUrl: page.finalUrl || normalized,
      fetchedAt,
      overallScore,
      grade,
      pillars,
      recommendations,
      aiSummary,
      meta: {
        title: page.title,
        description: page.metaDescription,
        durationMs: Date.now() - startedAt,
        usedLiveAI: ai.usedLiveAI,
        ...(page.error ? { error: page.error } : {}),
      },
    };
  } catch (err) {
    return buildErrorResult(
      normalized,
      normalized,
      fetchedAt,
      Date.now() - startedAt,
      messageOf(err),
    );
  }
}

/** Collect AI recommendations and synthesize ones from failing technical/content checks. */
function mergeRecommendations(
  technical: PillarScore,
  content: PillarScore,
  aiRecs: Recommendation[],
): Recommendation[] {
  const out: Recommendation[] = [...aiRecs];

  out.push(...synthesizeFromChecks(technical.checks, "technical"));
  out.push(...synthesizeFromChecks(content.checks, "content"));

  // De-duplicate by id (AI recs win since they are pushed first).
  const seen = new Set<string>();
  const deduped = out.filter((r) => {
    if (seen.has(r.id)) return false;
    seen.add(r.id);
    return true;
  });

  deduped.sort((a, b) => PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority]);
  return deduped.slice(0, MAX_RECOMMENDATIONS);
}

/** Turn each failing/warning check into a concrete Recommendation. */
function synthesizeFromChecks(checks: CheckResult[], pillar: PillarKey): Recommendation[] {
  const recs: Recommendation[] = [];
  for (const check of checks) {
    if (check.status !== "fail" && check.status !== "warn") continue;

    const priority: Recommendation["priority"] = check.status === "fail" ? "high" : "medium";
    const fraction = check.max > 0 ? check.score / check.max : 0;
    const impact = impactLabel(pillar, priority, fraction);

    recs.push({
      id: `rec-${pillar}-${check.id}`,
      pillar,
      priority,
      title: `Fix: ${check.label}`,
      detail: check.detail || `Address the "${check.label}" check to improve your ${PILLAR_LABELS[pillar]} score.`,
      impact,
    });
  }
  return recs;
}

/** Human-readable impact statement for a synthesized recommendation. */
function impactLabel(pillar: PillarKey, priority: Recommendation["priority"], fraction: number): string {
  const lift = priority === "high" ? "a meaningful" : "an incremental";
  const where =
    pillar === "technical"
      ? "crawlability and how reliably AI agents can retrieve your page"
      : pillar === "content"
        ? "topical authority and how well LLMs can summarize and cite your content"
        : "your visibility across AI assistants and answer engines";
  const gap = fraction <= 0 ? "This is currently scoring zero" : "There is room to improve here";
  return `${gap}; resolving it delivers ${lift} lift to ${where}.`;
}

/** Build a 2-3 sentence executive summary from the computed scores. */
function buildExecutiveSummary(
  overallScore: number,
  grade: Grade,
  pillars: PillarScore[],
  pageError?: string,
): string {
  const byKey = (k: PillarKey): number => pillars.find((p) => p.key === k)?.score ?? 0;
  const tech = byKey("technical");
  const content = byKey("content");
  const ai = byKey("aiVisibility");

  const sorted = [...pillars].sort((a, b) => a.score - b.score);
  const weakest = sorted[0];
  const strongest = sorted[sorted.length - 1];

  const standing =
    overallScore >= 80
      ? "is in strong shape for the AI age of search"
      : overallScore >= 55
        ? "has a solid foundation but meaningful gaps remain"
        : "needs significant work to compete in AI-driven discovery";

  const lead = `This site scores ${overallScore}/100 (grade ${grade}) and ${standing}.`;
  const breakdown = `Pillar scores: Technical ${tech}, Content & Authority ${content}, AI Visibility ${ai}.`;
  const guidance =
    weakest.key === strongest.key
      ? `Focus on broad improvements across all three pillars.`
      : `Your strongest area is ${strongest.label} (${strongest.score}); prioritize ${weakest.label} (${weakest.score}), where the biggest gains await.`;

  const note = pageError ? ` Note: the page could not be fully retrieved (${pageError}), so some checks are estimated.` : "";

  return `${lead} ${breakdown} ${guidance}${note}`;
}

/** Assemble a valid AuditResult representing a total fetch/analysis failure. */
function buildErrorResult(
  url: string,
  finalUrl: string,
  fetchedAt: string,
  durationMs: number,
  error: string,
): AuditResult {
  const emptyChecks: CheckResult[] = [];
  const pillars: PillarScore[] = (Object.keys(PILLAR_LABELS) as PillarKey[]).map((key) => ({
    key,
    label: PILLAR_LABELS[key],
    score: 0,
    grade: toGrade(0),
    checks: emptyChecks,
    summary: "Could not be evaluated because the page could not be analyzed.",
  }));

  return {
    url,
    finalUrl,
    fetchedAt,
    overallScore: 0,
    grade: toGrade(0),
    pillars,
    recommendations: [
      {
        id: "rec-fetch-failed",
        pillar: "technical",
        priority: "high",
        title: "Make the site reachable and crawlable",
        detail: `The audit could not load this URL: ${error}. Verify the site is online, returns a 200 response, and is not blocking automated requests.`,
        impact:
          "If a basic fetcher cannot reach your page, search crawlers and AI agents cannot either — nothing else can be indexed or cited.",
      },
    ],
    aiSummary: `The audit could not be completed because the page could not be retrieved (${error}). Confirm the URL is correct and publicly accessible, then re-run the audit.`,
    meta: {
      title: null,
      description: null,
      durationMs,
      usedLiveAI: false,
      error,
    },
  };
}

function messageOf(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (typeof err === "string") return err;
  return "Unknown error";
}
