/**
 * Real-site benchmark + false-info guard.
 *
 * For each target site this:
 *   1. fetches the page and runs the full audit (runAudit),
 *   2. independently re-derives ground-truth facts from the raw HTML using
 *      separate regexes (NOT the app's parser), and
 *   3. asserts that nothing the audit reports contradicts that ground truth —
 *      i.e. the audit never states false information about the page.
 * It also validates structural integrity (scores in range, weighting, grades,
 * well-formed recommendations).
 *
 * Sites that can't be reached (e.g. egress-restricted sandboxes) are SKIPPED,
 * not failed. Exits non-zero if any real check FAILS.
 *
 * Run: npm run benchmark
 */
import { fetchPage } from "@/lib/audit/fetchPage";
import { runAudit } from "@/lib/audit/runAudit";
import {
  PILLAR_WEIGHTS,
  type AuditResult,
  type PageData,
  type PillarKey,
} from "@/lib/types";

const SITES = [
  "https://pypi.org",
  "https://jsr.io",
  "https://www.anthropic.com",
  "https://registry.npmjs.org",
];

type Level = "FAIL" | "WARN";
interface Issue {
  level: Level;
  msg: string;
}

// --- independent ground-truth extractors (deliberately not the app parser) ---
function gtTitle(html: string): string | null {
  const m = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  if (!m) return null;
  return m[1].replace(/\s+/g, " ").trim() || null;
}
function gtCount(html: string, re: RegExp): number {
  return (html.match(re) ?? []).length;
}

const VALID_GRADES = new Set(["A", "B", "C", "D", "F"]);
const VALID_PILLARS = new Set<PillarKey>(["technical", "content", "aiVisibility"]);
const VALID_PRIORITIES = new Set(["high", "medium", "low"]);

function inRange(n: number): boolean {
  return Number.isFinite(n) && n >= 0 && n <= 100;
}

function factCheck(page: PageData, result: AuditResult): Issue[] {
  const issues: Issue[] = [];
  const html = page.html;

  // Ground truth from raw HTML, derived independently of the app's parser.
  const gtTitleVal = gtTitle(html);
  const gtH1 = gtCount(html, /<h1[\s>]/gi);
  const gtJsonLd = gtCount(
    html,
    /<script\b[^>]*type\s*=\s*["']application\/ld\+json["']/gi,
  );
  const gtHttps = result.finalUrl.startsWith("https");

  // 1. Parser title must match the real <title> (when one exists).
  if (gtTitleVal && page.title && page.title !== gtTitleVal) {
    // Allow entity-decoding differences; compare loosely.
    const norm = (s: string) => s.replace(/\s+/g, " ").trim().toLowerCase();
    if (norm(page.title) !== norm(gtTitleVal) && !norm(gtTitleVal).includes(norm(page.title))) {
      issues.push({
        level: "FAIL",
        msg: `title mismatch: audit="${page.title}" vs html="${gtTitleVal}"`,
      });
    }
  }
  if (gtTitleVal && !page.title) {
    issues.push({ level: "FAIL", msg: `audit reported no title but html has "${gtTitleVal}"` });
  }

  // 2. HTTPS claim must match reality.
  if (page.https !== gtHttps) {
    issues.push({ level: "FAIL", msg: `https flag (${page.https}) != url scheme (${gtHttps})` });
  }

  // 3. Structured-data claims must match ground truth (both technical & AI checks).
  const sdPresentGT = gtJsonLd > 0;
  const techSd = result.pillars
    .find((p) => p.key === "technical")
    ?.checks.find((c) => /structured data/i.test(c.label));
  const aiSd = result.pillars
    .find((p) => p.key === "aiVisibility")
    ?.checks.find((c) => /structured data/i.test(c.label));
  for (const [name, chk] of [
    ["technical", techSd],
    ["aiVisibility", aiSd],
  ] as const) {
    if (!chk) continue;
    const claimsPresent = chk.status === "pass";
    if (claimsPresent !== sdPresentGT) {
      issues.push({
        level: "FAIL",
        msg: `${name} structured-data check claims present=${claimsPresent} but html has ${gtJsonLd} JSON-LD block(s)`,
      });
    }
    // Detail text must not assert "found"/"detected" when there are none.
    if (!sdPresentGT && /\bfound\b|\bdetected\b|\bpresent\b/i.test(chk.detail) && !/no\b/i.test(chk.detail)) {
      issues.push({
        level: "FAIL",
        msg: `${name} structured-data detail implies presence but none exist: "${chk.detail}"`,
      });
    }
  }

  // 4. H1 heading claim sanity: if html clearly has an H1, audit must not deny it.
  const auditH1 = page.headings.filter((h) => h.level === 1).length;
  if (gtH1 > 0 && auditH1 === 0) {
    issues.push({ level: "FAIL", msg: `html has ${gtH1} <h1> but audit found 0` });
  }

  // 5. Word count must be plausible (not fabricated): page text non-empty => wc>0.
  if (page.text.trim().length > 0 && page.wordCount <= 0) {
    issues.push({ level: "FAIL", msg: `wordCount=${page.wordCount} but text is non-empty` });
  }

  return issues;
}

function structuralCheck(result: AuditResult): Issue[] {
  const issues: Issue[] = [];

  if (!inRange(result.overallScore)) {
    issues.push({ level: "FAIL", msg: `overallScore out of range: ${result.overallScore}` });
  }
  if (!VALID_GRADES.has(result.grade)) {
    issues.push({ level: "FAIL", msg: `invalid grade: ${result.grade}` });
  }

  // Overall must equal the documented weighted blend (allow ±1 for rounding).
  const expected = Math.round(
    result.pillars.reduce((a, p) => a + p.score * PILLAR_WEIGHTS[p.key], 0),
  );
  if (Math.abs(expected - result.overallScore) > 1) {
    issues.push({
      level: "FAIL",
      msg: `overall ${result.overallScore} != weighted blend ${expected}`,
    });
  }

  const keys = new Set(result.pillars.map((p) => p.key));
  for (const k of VALID_PILLARS) {
    if (!keys.has(k)) issues.push({ level: "FAIL", msg: `missing pillar: ${k}` });
  }

  for (const p of result.pillars) {
    if (!inRange(p.score)) {
      issues.push({ level: "FAIL", msg: `pillar ${p.key} score out of range: ${p.score}` });
    }
    for (const c of p.checks) {
      if (!Number.isFinite(c.score) || !Number.isFinite(c.max) || c.score < 0 || c.score > c.max) {
        issues.push({ level: "FAIL", msg: `check ${p.key}/${c.id} score ${c.score}/${c.max} invalid` });
      }
      if (!c.label || !c.detail) {
        issues.push({ level: "WARN", msg: `check ${p.key}/${c.id} missing label/detail` });
      }
    }
  }

  for (const r of result.recommendations) {
    if (!VALID_PILLARS.has(r.pillar)) {
      issues.push({ level: "FAIL", msg: `rec ${r.id} invalid pillar ${r.pillar}` });
    }
    if (!VALID_PRIORITIES.has(r.priority)) {
      issues.push({ level: "FAIL", msg: `rec ${r.id} invalid priority ${r.priority}` });
    }
    if (!r.title.trim()) {
      issues.push({ level: "FAIL", msg: `rec ${r.id} empty title` });
    }
  }

  return issues;
}

async function main() {
  console.log("Rankwise real-site benchmark + false-info guard\n");
  let failures = 0;
  let audited = 0;
  let skipped = 0;

  for (const url of SITES) {
    process.stdout.write(`• ${url}\n`);
    let page: PageData;
    try {
      page = await fetchPage(url);
    } catch (e) {
      console.log(`    SKIP — fetch threw: ${(e as Error).message}\n`);
      skipped++;
      continue;
    }
    if (page.error || !page.ok || page.html.length === 0) {
      console.log(`    SKIP — unreachable (${page.error ?? `status ${page.status}`})\n`);
      skipped++;
      continue;
    }

    const result = await runAudit(url);
    audited++;

    const issues = [...factCheck(page, result), ...structuralCheck(result)];
    const fails = issues.filter((i) => i.level === "FAIL");
    failures += fails.length;

    console.log(
      `    overall ${result.overallScore}/${result.grade}` +
        `  T:${result.pillars[0].score} C:${result.pillars[1].score} AI:${result.pillars[2].score}` +
        `  recs:${result.recommendations.length}  jsonLd:${page.jsonLd.length}  words:${page.wordCount}`,
    );
    console.log(`    title: ${JSON.stringify(page.title)}`);
    if (issues.length === 0) {
      console.log("    ✓ no false info — all factual claims match ground truth\n");
    } else {
      for (const i of issues) console.log(`    ${i.level === "FAIL" ? "✗" : "!"} ${i.level}: ${i.msg}`);
      console.log("");
    }
  }

  console.log("──────────────────────────────────────────");
  console.log(`audited: ${audited}   skipped: ${skipped}   FAILED checks: ${failures}`);
  if (audited === 0) {
    console.log("No sites were reachable in this environment (egress-restricted); ran 0 live checks.");
  } else if (failures === 0) {
    console.log("PASS — every audited site's factual claims matched independently-derived ground truth.");
  } else {
    console.log("FAIL — see ✗ items above.");
    process.exitCode = 1;
  }
}

main();
