// Content & Authority pillar analyzer.
// Evaluates a single page's content depth, structure, readability, keyword
// alignment, internal linking, image accessibility, and social metadata.
// All work is deterministic and offline — no network, no AI calls.

import type { CheckResult, CheckStatus, PageData, PillarScore } from "@/lib/types";
import { PILLAR_LABELS } from "@/lib/types";
import { checksToScore, toGrade } from "@/lib/utils";

const STOP_WORDS = new Set([
  "the", "and", "for", "with", "you", "your", "our", "are", "this", "that",
  "from", "have", "has", "was", "were", "will", "can", "all", "but", "not",
  "out", "use", "how", "why", "what", "who", "get", "more", "new", "now",
  "a", "an", "of", "to", "in", "on", "is", "it", "as", "at", "by", "or",
  "be", "we", "us", "do", "if", "so", "up", "no", "my", "me", "he", "she",
]);

/** Split text into rough sentences for the readability proxy. */
function splitSentences(text: string): string[] {
  return text
    .split(/[.!?]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

/** Extract meaningful lowercase tokens (alphabetic, length >= 4, not stop words). */
function meaningfulTerms(input: string): string[] {
  const tokens = input
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length >= 4 && !STOP_WORDS.has(w));
  return tokens;
}

/** Build a check, clamping score into [0, max]. */
function check(
  id: string,
  label: string,
  status: CheckStatus,
  detail: string,
  score: number,
  max: number,
): CheckResult {
  return { id, label, status, detail, score: Math.max(0, Math.min(score, max)), max };
}

export function analyzeContent(page: PageData): PillarScore {
  const checks: CheckResult[] = [];

  // Graceful degradation: if the fetch failed, mark every content check as
  // failed/info so the pillar reports an honest zero-ish score with context.
  if (page.error) {
    const reason = page.error;
    const failed: Array<[string, string]> = [
      ["content-depth", "Word count depth"],
      ["content-headings", "Heading structure"],
      ["content-readability", "Readability"],
      ["content-keyword-alignment", "Title/body keyword alignment"],
      ["content-internal-links", "Internal linking"],
      ["content-image-alt", "Image alt coverage"],
      ["content-og", "Open Graph metadata"],
    ];
    for (const [id, label] of failed) {
      checks.push(
        check(id, label, "fail", `Page could not be analyzed: ${reason}`, 0, 10),
      );
    }
    const failScore = checksToScore(checks);
    return {
      key: "content",
      label: PILLAR_LABELS.content,
      score: failScore,
      grade: toGrade(failScore),
      checks,
      summary: `Content could not be evaluated because the page failed to load (${reason}).`,
    };
  }

  // 1. Word count depth ------------------------------------------------------
  const wc = page.wordCount;
  if (wc >= 800) {
    checks.push(
      check("content-depth", "Word count depth", "pass",
        `${wc} words — strong depth for ranking and AI extraction.`, 15, 15),
    );
  } else if (wc >= 300) {
    checks.push(
      check("content-depth", "Word count depth", "warn",
        `${wc} words — acceptable, but 800+ gives AI engines more to cite.`, 9, 15),
    );
  } else {
    checks.push(
      check("content-depth", "Word count depth", "fail",
        `${wc} words — thin content; aim for at least 300, ideally 800+.`, 2, 15),
    );
  }

  // 2. Heading structure (needs an H1 and multiple H2s) ----------------------
  const h1s = page.headings.filter((h) => h.level === 1);
  const h2s = page.headings.filter((h) => h.level === 2);
  if (h1s.length === 1 && h2s.length >= 2) {
    checks.push(
      check("content-headings", "Heading structure", "pass",
        `Exactly one H1 and ${h2s.length} H2 sections — clean, scannable hierarchy.`, 12, 12),
    );
  } else if (h1s.length >= 1 && h2s.length >= 1) {
    const h1Note = h1s.length > 1 ? `${h1s.length} H1s (use one)` : "1 H1";
    checks.push(
      check("content-headings", "Heading structure", "warn",
        `${h1Note} and ${h2s.length} H2(s) — add more H2 sections for clearer structure.`, 7, 12),
    );
  } else {
    checks.push(
      check("content-headings", "Heading structure", "fail",
        `${h1s.length} H1 and ${h2s.length} H2 — missing a clear heading hierarchy.`, 2, 12),
    );
  }

  // 3. Readability proxy (average words per sentence) ------------------------
  const sentences = splitSentences(page.text);
  if (sentences.length === 0 || wc === 0) {
    checks.push(
      check("content-readability", "Readability", "fail",
        "No readable sentences detected in body text.", 0, 12),
    );
  } else {
    const avg = wc / sentences.length;
    const avgr = Math.round(avg * 10) / 10;
    if (avg <= 20) {
      checks.push(
        check("content-readability", "Readability", "pass",
          `~${avgr} words per sentence — easy to read and quote.`, 12, 12),
      );
    } else if (avg <= 28) {
      checks.push(
        check("content-readability", "Readability", "warn",
          `~${avgr} words per sentence — a bit dense; shorten some sentences.`, 7, 12),
      );
    } else {
      checks.push(
        check("content-readability", "Readability", "fail",
          `~${avgr} words per sentence — too dense for easy reading or AI parsing.`, 3, 12),
      );
    }
  }

  // 4. Keyword/title alignment ----------------------------------------------
  const titleTerms = page.title ? Array.from(new Set(meaningfulTerms(page.title))) : [];
  if (titleTerms.length === 0) {
    checks.push(
      check("content-keyword-alignment", "Title/body keyword alignment", "fail",
        "No title (or no meaningful title terms) to align with body content.", 0, 12),
    );
  } else {
    const bodyTerms = new Set(meaningfulTerms(page.text));
    const matched = titleTerms.filter((t) => bodyTerms.has(t));
    const ratio = matched.length / titleTerms.length;
    const pct = Math.round(ratio * 100);
    if (ratio >= 0.6) {
      checks.push(
        check("content-keyword-alignment", "Title/body keyword alignment", "pass",
          `${pct}% of title terms appear in the body — strong topical alignment.`, 12, 12),
      );
    } else if (ratio >= 0.3) {
      checks.push(
        check("content-keyword-alignment", "Title/body keyword alignment", "warn",
          `${pct}% of title terms appear in the body — reinforce your topic in the copy.`, 7, 12),
      );
    } else {
      checks.push(
        check("content-keyword-alignment", "Title/body keyword alignment", "fail",
          `Only ${pct}% of title terms appear in the body — title and content are misaligned.`, 2, 12),
      );
    }
  }

  // 5. Internal linking ------------------------------------------------------
  const internalLinks = page.links.filter((l) => l.internal).length;
  if (internalLinks >= 3) {
    checks.push(
      check("content-internal-links", "Internal linking", "pass",
        `${internalLinks} internal links — good site structure and crawl paths.`, 10, 10),
    );
  } else if (internalLinks >= 1) {
    checks.push(
      check("content-internal-links", "Internal linking", "warn",
        `${internalLinks} internal link(s) — add more to connect related pages (aim for 3+).`, 5, 10),
    );
  } else {
    checks.push(
      check("content-internal-links", "Internal linking", "fail",
        "No internal links found — orphaned pages are hard to crawl and rank.", 1, 10),
    );
  }

  // 6. Image alt coverage ----------------------------------------------------
  const totalImages = page.images.length;
  if (totalImages === 0) {
    checks.push(
      check("content-image-alt", "Image alt coverage", "info",
        "No images on the page — nothing to caption.", 8, 8),
    );
  } else {
    const withAlt = page.images.filter((i) => i.alt !== null && i.alt.trim() !== "").length;
    const cov = withAlt / totalImages;
    const pct = Math.round(cov * 100);
    if (cov >= 0.9) {
      checks.push(
        check("content-image-alt", "Image alt coverage", "pass",
          `${pct}% of ${totalImages} images have alt text — accessible and indexable.`, 8, 8),
      );
    } else if (cov >= 0.5) {
      checks.push(
        check("content-image-alt", "Image alt coverage", "warn",
          `${pct}% of ${totalImages} images have alt text — add descriptions to the rest.`, 4, 8),
      );
    } else {
      checks.push(
        check("content-image-alt", "Image alt coverage", "fail",
          `Only ${pct}% of ${totalImages} images have alt text — most images are inaccessible.`, 1, 8),
      );
    }
  }

  // 7. Open Graph / social metadata richness --------------------------------
  const og = page.openGraph;
  const ogTitle = !!(og["og:title"] && og["og:title"].trim());
  const ogDesc = !!(og["og:description"] && og["og:description"].trim());
  const ogImage = !!(og["og:image"] && og["og:image"].trim());
  const ogCount = [ogTitle, ogDesc, ogImage].filter(Boolean).length;
  if (ogCount === 3) {
    checks.push(
      check("content-og", "Open Graph metadata", "pass",
        "og:title, og:description, and og:image all present — rich social/AI previews.", 11, 11),
    );
  } else if (ogCount >= 1) {
    const missing = [
      !ogTitle ? "og:title" : null,
      !ogDesc ? "og:description" : null,
      !ogImage ? "og:image" : null,
    ].filter((x): x is string => x !== null);
    checks.push(
      check("content-og", "Open Graph metadata", "warn",
        `Missing ${missing.join(", ")} — incomplete previews when shared or surfaced by AI.`, 6, 11),
    );
  } else {
    checks.push(
      check("content-og", "Open Graph metadata", "fail",
        "No Open Graph metadata — links render as bare URLs in social and AI surfaces.", 1, 11),
    );
  }

  // Aggregate ----------------------------------------------------------------
  const score = checksToScore(checks);
  const grade = toGrade(score);

  const passCount = checks.filter((c) => c.status === "pass").length;
  const weakCount = checks.filter((c) => c.status === "warn" || c.status === "fail").length;
  const summary =
    weakCount === 0
      ? `Content is well-structured and AI-ready, passing all ${checks.length} content checks (grade ${grade}).`
      : `Content scored ${score}/100 (grade ${grade}): ${passCount} checks passed, ${weakCount} need attention.`;

  return {
    key: "content",
    label: PILLAR_LABELS.content,
    score,
    grade,
    checks,
    summary,
  };
}
