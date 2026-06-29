// AI Visibility analyzer.
//
// Scores how "citable" a page is by AI answer engines (Claude, ChatGPT,
// Perplexity, Gemini, Grok). When a live Anthropic key is configured we ask
// Claude to act as an AEO analyst and return strict JSON; otherwise (or on any
// failure) we fall back to a deterministic heuristic computed entirely from the
// signals already present in PageData.
//
// This module NEVER throws: it always resolves an AiVisibilityResult.

import { isLiveAIEnabled, askClaudeJSON } from "@/lib/ai/anthropic";
import { clamp, checksToScore } from "@/lib/utils";
import type {
  AiVisibilityResult,
  CheckResult,
  CheckStatus,
  PageData,
  Recommendation,
} from "@/lib/types";

const MAX_EXCERPT = 2000;

/** Shape Claude is instructed to return. We validate/normalize it defensively. */
interface RawAiCheck {
  id?: unknown;
  label?: unknown;
  status?: unknown;
  detail?: unknown;
  score?: unknown;
  max?: unknown;
}

interface RawAiRecommendation {
  id?: unknown;
  priority?: unknown;
  title?: unknown;
  detail?: unknown;
  impact?: unknown;
}

interface RawAiResponse {
  score?: unknown;
  summary?: unknown;
  checks?: unknown;
  recommendations?: unknown;
}

const SYSTEM_PROMPT = [
  "You are an AI Answer Engine Optimization (AEO) analyst.",
  "Your job is to assess how likely a web page is to be discovered, understood,",
  "and cited by AI answer engines such as Claude, ChatGPT, Perplexity, Gemini,",
  "and Grok. Evaluate entity/brand clarity, structured data, heading hierarchy,",
  "answer-friendly Q&A content, concise metadata, and overall machine readability.",
  "",
  "Respond with STRICT JSON only — no markdown, no prose, no code fences.",
  "Use exactly this shape:",
  "{",
  '  "score": <number 0-100>,',
  '  "summary": "<one or two sentences>",',
  '  "checks": [',
  '    { "id": "<slug>", "label": "<short>", "status": "pass|warn|fail|info",',
  '      "detail": "<short>", "score": <number>, "max": <number> }',
  "  ],",
  '  "recommendations": [',
  '    { "id": "<slug>", "priority": "high|medium|low", "title": "<short>",',
  '      "detail": "<actionable>", "impact": "<why it matters for AI SEO>" }',
  "  ]",
  "}",
  "Provide 5-7 checks and 3-5 recommendations.",
].join("\n");

/** Build a compact, token-frugal prompt from the page signals. */
function buildUserPrompt(page: PageData): string {
  const excerpt = (page.text || "").slice(0, MAX_EXCERPT);
  const headings = page.headings
    .slice(0, 25)
    .map((h) => `H${h.level}: ${h.text}`)
    .join("\n");
  const hasStructuredData = Array.isArray(page.jsonLd) && page.jsonLd.length > 0;
  const ogKeys = Object.keys(page.openGraph || {});

  const lines: string[] = [
    `URL: ${page.finalUrl || page.url}`,
    `Title: ${page.title ?? "(none)"}`,
    `Meta description: ${page.metaDescription ?? "(none)"}`,
    `Structured data (JSON-LD) present: ${hasStructuredData ? "yes" : "no"} (${
      hasStructuredData ? page.jsonLd.length : 0
    } block(s))`,
    `OpenGraph keys: ${ogKeys.length > 0 ? ogKeys.join(", ") : "(none)"}`,
    `Word count: ${page.wordCount}`,
    "",
    "Headings:",
    headings || "(none)",
    "",
    "Text excerpt:",
    excerpt || "(no extractable text)",
  ];

  return lines.join("\n");
}

const VALID_STATUSES: ReadonlySet<string> = new Set([
  "pass",
  "warn",
  "fail",
  "info",
]);

function asString(v: unknown, fallback: string): string {
  return typeof v === "string" && v.trim().length > 0 ? v : fallback;
}

function asNumber(v: unknown, fallback: number): number {
  return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

function asStatus(v: unknown): CheckStatus {
  return typeof v === "string" && VALID_STATUSES.has(v)
    ? (v as CheckStatus)
    : "info";
}

function asPriority(v: unknown): Recommendation["priority"] {
  return v === "high" || v === "medium" || v === "low" ? v : "medium";
}

/** Convert a validated raw AI payload into an AiVisibilityResult. */
function normalizeAiResponse(raw: RawAiResponse): AiVisibilityResult {
  const rawChecks = Array.isArray(raw.checks) ? raw.checks : [];
  const checks: CheckResult[] = rawChecks.map((c, i) => {
    const rc = (c ?? {}) as RawAiCheck;
    const max = clamp(asNumber(rc.max, 10), 0, 1000);
    return {
      id: asString(rc.id, `ai-${i + 1}`),
      label: asString(rc.label, "AI visibility signal"),
      status: asStatus(rc.status),
      detail: asString(rc.detail, ""),
      score: clamp(asNumber(rc.score, 0), 0, max),
      max,
    };
  });

  const rawRecs = Array.isArray(raw.recommendations) ? raw.recommendations : [];
  const recommendations: Recommendation[] = rawRecs.map((r, i) => {
    const rr = (r ?? {}) as RawAiRecommendation;
    return {
      id: asString(rr.id, `ai-rec-${i + 1}`),
      pillar: "aiVisibility",
      priority: asPriority(rr.priority),
      title: asString(rr.title, "Improve AI visibility"),
      detail: asString(rr.detail, ""),
      impact: asString(rr.impact, ""),
    };
  });

  // Prefer the model's own 0-100 score; if it's missing/garbage, derive it.
  let score = asNumber(raw.score, NaN);
  if (!Number.isFinite(score)) {
    score = checks.length > 0 ? checksToScore(checks) : 0;
  }
  score = Math.round(clamp(score, 0, 100));

  const summary = asString(
    raw.summary,
    "AI answer-engine optimization analysis completed.",
  );

  return { score, summary, checks, recommendations, usedLiveAI: true };
}

/**
 * Heuristic, fully deterministic AEO scoring computed from PageData alone.
 * Used when live AI is disabled or when the live call fails for any reason.
 */
function heuristicAnalysis(page: PageData): AiVisibilityResult {
  const checks: CheckResult[] = [];

  // 1. Structured data (JSON-LD) — strongest machine-readability signal.
  const jsonLdCount = Array.isArray(page.jsonLd) ? page.jsonLd.length : 0;
  checks.push({
    id: "ai-structured-data",
    label: "Structured data (JSON-LD)",
    status: jsonLdCount > 0 ? "pass" : "fail",
    detail:
      jsonLdCount > 0
        ? `${jsonLdCount} JSON-LD block(s) found — helps AI engines extract entities.`
        : "No JSON-LD found. AI engines rely on schema.org markup to understand entities.",
    score: jsonLdCount > 0 ? 25 : 0,
    max: 25,
  });

  // 2. Heading hierarchy — exactly one H1, with deeper headings present.
  const h1s = page.headings.filter((h) => h.level === 1);
  const subHeadings = page.headings.filter((h) => h.level >= 2);
  let headingScore = 0;
  let headingStatus: CheckStatus = "fail";
  let headingDetail: string;
  if (h1s.length === 1 && subHeadings.length >= 2) {
    headingScore = 18;
    headingStatus = "pass";
    headingDetail = `Single H1 with ${subHeadings.length} sub-heading(s) — clear, parseable structure.`;
  } else if (h1s.length >= 1) {
    headingScore = 10;
    headingStatus = "warn";
    headingDetail =
      h1s.length > 1
        ? `${h1s.length} H1 tags found — use exactly one H1 for a clear topic.`
        : "Single H1 but few sub-headings; add H2/H3 structure for AI parsing.";
  } else {
    headingDetail = "No H1 found. AI engines use the H1 to identify the page topic.";
  }
  checks.push({
    id: "ai-heading-hierarchy",
    label: "Heading hierarchy",
    status: headingStatus,
    detail: headingDetail,
    score: headingScore,
    max: 18,
  });

  // 3. Concise, present meta description.
  const desc = page.metaDescription ?? "";
  const descLen = desc.trim().length;
  let descScore = 0;
  let descStatus: CheckStatus = "fail";
  let descDetail: string;
  if (descLen === 0) {
    descDetail = "No meta description. Provide a concise summary AI engines can quote.";
  } else if (descLen >= 50 && descLen <= 160) {
    descScore = 12;
    descStatus = "pass";
    descDetail = `Meta description is a concise ${descLen} characters.`;
  } else {
    descScore = 6;
    descStatus = "warn";
    descDetail =
      descLen < 50
        ? `Meta description is short (${descLen} chars); aim for 50-160.`
        : `Meta description is long (${descLen} chars); trim to 50-160.`;
  }
  checks.push({
    id: "ai-meta-description",
    label: "Concise meta description",
    status: descStatus,
    detail: descDetail,
    score: descScore,
    max: 12,
  });

  // 4. Entity / brand clarity — title carries a brand-like proper noun.
  const title = page.title ?? "";
  const hasBrandSignal = detectBrandSignal(title);
  checks.push({
    id: "ai-entity-clarity",
    label: "Entity / brand clarity",
    status: title.trim().length === 0 ? "fail" : hasBrandSignal ? "pass" : "warn",
    detail:
      title.trim().length === 0
        ? "No title tag — AI engines cannot identify the brand/entity."
        : hasBrandSignal
          ? "Title contains a brand-like proper noun, aiding entity recognition."
          : "Title lacks a distinct brand name; include your brand for entity clarity.",
    score: title.trim().length === 0 ? 0 : hasBrandSignal ? 15 : 8,
    max: 15,
  });

  // 5. FAQ / Q&A-style answer content — directly citable by answer engines.
  const qaHeadings = page.headings.filter((h) => isQuestionLike(h.text));
  const hasFaqSchema = hasFaqStructuredData(page.jsonLd);
  let qaScore = 0;
  let qaStatus: CheckStatus = "fail";
  let qaDetail: string;
  if (hasFaqSchema || qaHeadings.length >= 2) {
    qaScore = 15;
    qaStatus = "pass";
    qaDetail = hasFaqSchema
      ? "FAQ structured data detected — ideal for AI answer extraction."
      : `${qaHeadings.length} question-style heading(s) found — answer-friendly content.`;
  } else if (qaHeadings.length === 1) {
    qaScore = 8;
    qaStatus = "warn";
    qaDetail = "Some Q&A content present; expand FAQ-style sections for AI citability.";
  } else {
    qaDetail =
      "No FAQ/Q&A content. Question-and-answer sections are highly citable by AI engines.";
  }
  checks.push({
    id: "ai-qa-content",
    label: "FAQ / Q&A answer content",
    status: qaStatus,
    detail: qaDetail,
    score: qaScore,
    max: 15,
  });

  // 6. OpenGraph / social metadata — aids preview and source attribution.
  const ogKeys = Object.keys(page.openGraph || {});
  const hasCoreOg =
    ogKeys.includes("og:title") || ogKeys.includes("og:description");
  checks.push({
    id: "ai-open-graph",
    label: "OpenGraph metadata",
    status: ogKeys.length === 0 ? "fail" : hasCoreOg ? "pass" : "warn",
    detail:
      ogKeys.length === 0
        ? "No OpenGraph tags. They give AI/social systems a clean title & summary."
        : hasCoreOg
          ? `OpenGraph metadata present (${ogKeys.length} tag(s)).`
          : `Some OpenGraph tags present but missing og:title/og:description.`,
    score: ogKeys.length === 0 ? 0 : hasCoreOg ? 8 : 4,
    max: 8,
  });

  // 7. Content depth — enough substance to be worth citing.
  const wc = page.wordCount;
  let depthScore = 0;
  let depthStatus: CheckStatus = "fail";
  let depthDetail: string;
  if (wc >= 600) {
    depthScore = 7;
    depthStatus = "pass";
    depthDetail = `${wc} words — substantial content AI engines can draw from.`;
  } else if (wc >= 250) {
    depthScore = 4;
    depthStatus = "warn";
    depthDetail = `${wc} words — moderate depth; richer content improves citability.`;
  } else {
    depthDetail = `${wc} words — thin content is rarely cited by AI answer engines.`;
  }
  checks.push({
    id: "ai-content-depth",
    label: "Content depth",
    status: depthStatus,
    detail: depthDetail,
    score: depthScore,
    max: 7,
  });

  const score = checksToScore(checks);

  const recommendations = buildHeuristicRecommendations(checks);

  const passing = checks.filter((c) => c.status === "pass").length;
  const summary = page.error
    ? "AI-visibility analysis ran on limited data because the page could not be fully fetched."
    : `Heuristic AEO analysis: ${passing}/${checks.length} signals passed. ` +
      (score >= 70
        ? "This page is reasonably positioned for AI answer engines."
        : "There is meaningful room to improve how AI engines understand and cite this page.");

  return { score, summary, checks, recommendations, usedLiveAI: false };
}

/** Heuristic: does the title contain a brand-like proper noun? */
function detectBrandSignal(title: string): boolean {
  const t = title.trim();
  if (t.length === 0) return false;

  // A separator (| - – — :) commonly delimits "Page Title | Brand".
  if (/[|–—‒:•·]/.test(t)) return true;

  // A capitalized token that isn't a generic stop/lead word.
  const stop = new Set([
    "the",
    "a",
    "an",
    "and",
    "or",
    "for",
    "your",
    "our",
    "best",
    "top",
    "how",
    "what",
    "why",
    "welcome",
    "home",
  ]);
  const tokens = t.split(/\s+/);
  let properCount = 0;
  for (const tok of tokens) {
    const clean = tok.replace(/[^A-Za-z0-9]/g, "");
    if (clean.length < 2) continue;
    if (stop.has(clean.toLowerCase())) continue;
    // Proper-noun-ish: TitleCase word, an all-caps acronym, or interior-capital
    // CamelCase brand (e.g. "YouTube", "iPhone").
    if (
      /^[A-Z][a-z]/.test(clean) ||
      /^[A-Z]{2,}$/.test(clean) ||
      /[a-z][A-Z]/.test(clean)
    ) {
      properCount++;
    }
  }
  return properCount >= 1;
}

/** Heuristic: is a heading phrased as a question / direct query? */
function isQuestionLike(text: string): boolean {
  const t = text.trim().toLowerCase();
  if (t.length === 0) return false;
  if (t.endsWith("?")) return true;
  return /^(how|what|why|when|where|who|which|can|do|does|is|are|should)\b/.test(t);
}

/** Heuristic: does any JSON-LD block declare an FAQPage / QAPage type? */
function hasFaqStructuredData(jsonLd: unknown[]): boolean {
  if (!Array.isArray(jsonLd)) return false;
  const blob = JSON.stringify(jsonLd).toLowerCase();
  return (
    blob.includes("faqpage") ||
    blob.includes("qapage") ||
    blob.includes('"question"') ||
    blob.includes("answer")
  );
}

/** Derive 3-5 prioritized recommendations from failing/warning checks. */
function buildHeuristicRecommendations(checks: CheckResult[]): Recommendation[] {
  const byId = new Map(checks.map((c) => [c.id, c]));
  const recs: Recommendation[] = [];

  const sd = byId.get("ai-structured-data");
  if (sd && sd.status !== "pass") {
    recs.push({
      id: "ai-rec-structured-data",
      pillar: "aiVisibility",
      priority: "high",
      title: "Add schema.org JSON-LD structured data",
      detail:
        "Embed JSON-LD describing your organization, products, articles, or FAQs so AI engines can extract precise entities.",
      impact:
        "Structured data is the single strongest signal for being correctly understood and cited by AI answer engines.",
    });
  }

  const qa = byId.get("ai-qa-content");
  if (qa && qa.status !== "pass") {
    recs.push({
      id: "ai-rec-qa-content",
      pillar: "aiVisibility",
      priority: "high",
      title: "Add FAQ / Q&A-style content",
      detail:
        "Create sections with explicit questions as headings and concise direct answers, optionally marked up with FAQPage schema.",
      impact:
        "Answer engines preferentially quote question-and-answer content, increasing the chance your page is surfaced as the answer.",
    });
  }

  const entity = byId.get("ai-entity-clarity");
  if (entity && entity.status !== "pass") {
    recs.push({
      id: "ai-rec-entity-clarity",
      pillar: "aiVisibility",
      priority: "medium",
      title: "Strengthen brand & entity clarity",
      detail:
        "Include your brand name in the title tag and reinforce it consistently across headings, OpenGraph, and structured data.",
      impact:
        "Clear entity signals help AI systems associate the page with your brand and cite you by name.",
    });
  }

  const heading = byId.get("ai-heading-hierarchy");
  if (heading && heading.status !== "pass") {
    recs.push({
      id: "ai-rec-heading-hierarchy",
      pillar: "aiVisibility",
      priority: "medium",
      title: "Fix heading hierarchy",
      detail:
        "Use exactly one H1 for the page topic and organize supporting content under descriptive H2/H3 headings.",
      impact:
        "A clean heading outline helps AI engines segment the page and extract the right passage to cite.",
    });
  }

  const desc = byId.get("ai-meta-description");
  if (desc && desc.status !== "pass") {
    recs.push({
      id: "ai-rec-meta-description",
      pillar: "aiVisibility",
      priority: "low",
      title: "Write a concise meta description",
      detail:
        "Summarize the page in 50-160 characters that directly state what it offers.",
      impact:
        "A tight summary gives AI and search systems a ready-made snippet to quote.",
    });
  }

  const og = byId.get("ai-open-graph");
  if (recs.length < 3 && og && og.status !== "pass") {
    recs.push({
      id: "ai-rec-open-graph",
      pillar: "aiVisibility",
      priority: "low",
      title: "Add OpenGraph metadata",
      detail:
        "Provide og:title, og:description, and og:image so AI and social systems render a clean, attributable preview.",
      impact:
        "OpenGraph tags give answer engines a reliable title and summary for source attribution.",
    });
  }

  // Guarantee at least 3 recommendations even on a strong page.
  if (recs.length < 3) {
    const filler: Recommendation[] = [
      {
        id: "ai-rec-freshness",
        pillar: "aiVisibility",
        priority: "low",
        title: "Keep content fresh and dated",
        detail:
          "Add visible publish/updated dates and refresh key facts periodically; expose dates via Article schema.",
        impact: "AI engines favor current, clearly-dated sources when forming answers.",
      },
      {
        id: "ai-rec-citations",
        pillar: "aiVisibility",
        priority: "low",
        title: "Cite primary sources and data",
        detail:
          "Reference authoritative sources and include concrete statistics that AI systems can quote and attribute.",
        impact: "Well-sourced, factual content is more likely to be trusted and cited.",
      },
      {
        id: "ai-rec-semantic-html",
        pillar: "aiVisibility",
        priority: "low",
        title: "Use semantic, accessible HTML",
        detail:
          "Mark up content with semantic elements (article, section, nav, lists) so machines can parse structure.",
        impact: "Clean semantics improve how reliably AI engines extract meaning from the page.",
      },
    ];
    for (const f of filler) {
      if (recs.length >= 3) break;
      if (!recs.some((r) => r.id === f.id)) recs.push(f);
    }
  }

  return recs.slice(0, 5);
}

/**
 * Analyze a page's AI-answer-engine visibility.
 *
 * Uses live Claude analysis when enabled; otherwise (or on any error) returns a
 * deterministic heuristic result. Never throws.
 */
export async function analyzeAiVisibility(
  page: PageData,
): Promise<AiVisibilityResult> {
  if (isLiveAIEnabled()) {
    try {
      const raw = await askClaudeJSON<RawAiResponse>(
        SYSTEM_PROMPT,
        buildUserPrompt(page),
      );
      const result = normalizeAiResponse(raw);
      // Guard against a degenerate model reply with no usable content.
      if (result.checks.length > 0 || result.recommendations.length > 0) {
        return result;
      }
    } catch {
      // Fall through to the heuristic below.
    }
  }

  return heuristicAnalysis(page);
}
