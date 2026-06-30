import type { CheckResult, CheckStatus, PageData, PillarScore } from "@/lib/types";
import { PILLAR_LABELS } from "@/lib/types";
import { checksToScore, toGrade } from "@/lib/utils";

/** Build a single CheckResult with consistent shape. */
function mkCheck(
  id: string,
  label: string,
  status: CheckStatus,
  detail: string,
  score: number,
  max: number,
): CheckResult {
  return { id, label, status, detail, score, max };
}

/**
 * Analyze the Technical SEO pillar (crawlability, indexability, mobile,
 * structured data). Produces 6-9 graded checks normalized to a 0..100 score.
 */
export function analyzeTechnical(page: PageData): PillarScore {
  const key = "technical" as const;
  const label = PILLAR_LABELS[key];

  // If the page could not be fetched, return a low-scoring pillar.
  if (page.error) {
    const checks: CheckResult[] = [
      mkCheck(
        "reachable",
        "Site reachable",
        "fail",
        `Could not fetch the site: ${page.error}`,
        0,
        100,
      ),
    ];
    return {
      key,
      label,
      score: 0,
      grade: toGrade(0),
      checks,
      summary:
        "The site could not be fetched, so no technical checks could run. " +
        "Confirm the URL is correct and the server is reachable.",
    };
  }

  const checks: CheckResult[] = [];
  const html = page.html || "";

  // 1. HTTPS
  checks.push(
    page.https
      ? mkCheck("https", "HTTPS enabled", "pass", "Served securely over HTTPS.", 10, 10)
      : mkCheck(
          "https",
          "HTTPS enabled",
          "fail",
          "Site is not served over HTTPS; secure transport is expected by browsers and AI crawlers.",
          0,
          10,
        ),
  );

  // 2. Reachable / 200 status
  if (page.ok && page.status === 200) {
    checks.push(
      mkCheck("status", "HTTP 200 status", "pass", `Returned ${page.status} OK.`, 12, 12),
    );
  } else if (page.status >= 200 && page.status < 400) {
    checks.push(
      mkCheck(
        "status",
        "HTTP 200 status",
        "warn",
        `Returned ${page.status} (redirect/non-200); a direct 200 is preferred.`,
        7,
        12,
      ),
    );
  } else {
    checks.push(
      mkCheck(
        "status",
        "HTTP 200 status",
        "fail",
        `Returned ${page.status || "no"} status; the page is not serving content normally.`,
        0,
        12,
      ),
    );
  }

  // 3. <title> present & length 10-60
  const title = page.title?.trim() ?? "";
  if (!title) {
    checks.push(
      mkCheck("title", "Title tag", "fail", "No <title> tag found.", 0, 12),
    );
  } else if (title.length >= 10 && title.length <= 60) {
    checks.push(
      mkCheck(
        "title",
        "Title tag",
        "pass",
        `Title is ${title.length} characters, within the 10-60 range.`,
        12,
        12,
      ),
    );
  } else {
    checks.push(
      mkCheck(
        "title",
        "Title tag",
        "warn",
        `Title is ${title.length} characters; aim for 10-60 to avoid truncation.`,
        6,
        12,
      ),
    );
  }

  // 4. Meta description present & length 50-160
  const desc = page.metaDescription?.trim() ?? "";
  if (!desc) {
    checks.push(
      mkCheck(
        "meta-description",
        "Meta description",
        "fail",
        "No meta description found; search and AI snippets have nothing to summarize.",
        0,
        10,
      ),
    );
  } else if (desc.length >= 50 && desc.length <= 160) {
    checks.push(
      mkCheck(
        "meta-description",
        "Meta description",
        "pass",
        `Meta description is ${desc.length} characters, within the 50-160 range.`,
        10,
        10,
      ),
    );
  } else {
    checks.push(
      mkCheck(
        "meta-description",
        "Meta description",
        "warn",
        `Meta description is ${desc.length} characters; aim for 50-160.`,
        5,
        10,
      ),
    );
  }

  // 5. Exactly one H1
  const h1Count = page.headings.filter((h) => h.level === 1).length;
  if (h1Count === 1) {
    checks.push(
      mkCheck("h1", "Single H1", "pass", "Exactly one H1 heading, as expected.", 10, 10),
    );
  } else if (h1Count === 0) {
    checks.push(
      mkCheck(
        "h1",
        "Single H1",
        "fail",
        "No H1 heading found; the page lacks a clear primary topic.",
        0,
        10,
      ),
    );
  } else {
    checks.push(
      mkCheck(
        "h1",
        "Single H1",
        "warn",
        `Found ${h1Count} H1 headings; use exactly one for a clear topic hierarchy.`,
        5,
        10,
      ),
    );
  }

  // 6. Canonical present
  const canonical = page.canonical?.trim() ?? "";
  checks.push(
    canonical
      ? mkCheck(
          "canonical",
          "Canonical URL",
          "pass",
          "Canonical link is set, consolidating duplicate-content signals.",
          8,
          8,
        )
      : mkCheck(
          "canonical",
          "Canonical URL",
          "warn",
          "No canonical link found; duplicate URLs may dilute ranking signals.",
          0,
          8,
        ),
  );

  // 7. Robots meta not "noindex"
  const robotsMeta = (page.robotsMeta ?? "").toLowerCase();
  if (robotsMeta.includes("noindex")) {
    checks.push(
      mkCheck(
        "robots-meta",
        "Indexable (robots meta)",
        "fail",
        'Robots meta contains "noindex"; the page is blocked from search and AI indexes.',
        0,
        10,
      ),
    );
  } else {
    checks.push(
      mkCheck(
        "robots-meta",
        "Indexable (robots meta)",
        "pass",
        robotsMeta
          ? "Robots meta present and does not block indexing."
          : "No restrictive robots meta; the page is indexable by default.",
        10,
        10,
      ),
    );
  }

  // 8. robots.txt present
  checks.push(
    page.robotsTxt && page.robotsTxt.trim()
      ? mkCheck(
          "robots-txt",
          "robots.txt",
          "pass",
          "robots.txt is present to guide crawlers.",
          6,
          6,
        )
      : mkCheck(
          "robots-txt",
          "robots.txt",
          "warn",
          "No robots.txt found; crawlers and AI bots lack explicit crawl guidance.",
          0,
          6,
        ),
  );

  // 9. sitemap.xml present
  checks.push(
    page.sitemapXml && page.sitemapXml.trim()
      ? mkCheck(
          "sitemap",
          "XML sitemap",
          "pass",
          "An XML sitemap is available to help crawlers discover pages.",
          6,
          6,
        )
      : mkCheck(
          "sitemap",
          "XML sitemap",
          "warn",
          "No sitemap.xml found; page discovery relies on link crawling alone.",
          0,
          6,
        ),
  );

  // 10. Mobile viewport meta present
  const hasViewport = /<meta[^>]+name=["']?viewport["']?[^>]*>/i.test(html);
  checks.push(
    hasViewport
      ? mkCheck(
          "viewport",
          "Mobile viewport",
          "pass",
          "A responsive viewport meta tag is set for mobile rendering.",
          8,
          8,
        )
      : mkCheck(
          "viewport",
          "Mobile viewport",
          "fail",
          "No viewport meta tag; the page will not render well on mobile devices.",
          0,
          8,
        ),
  );

  // 11. Structured data (JSON-LD)
  const jsonLdCount = Array.isArray(page.jsonLd) ? page.jsonLd.length : 0;
  checks.push(
    jsonLdCount > 0
      ? mkCheck(
          "structured-data",
          "Structured data (JSON-LD)",
          "pass",
          `Found ${jsonLdCount} JSON-LD block(s); machine-readable context helps AI systems.`,
          8,
          8,
        )
      : mkCheck(
          "structured-data",
          "Structured data (JSON-LD)",
          "warn",
          "No JSON-LD structured data; AI systems get no explicit entity context.",
          0,
          8,
        ),
  );

  const score = checksToScore(checks);
  const grade = toGrade(score);

  const passCount = checks.filter((c) => c.status === "pass").length;
  const failCount = checks.filter((c) => c.status === "fail").length;
  const summary =
    `Technical SEO scored ${score}/100 (grade ${grade}), passing ${passCount} of ${checks.length} checks` +
    (failCount > 0
      ? ` with ${failCount} critical failure(s) to address first.`
      : " with no critical failures.");

  return { key, label, score, grade, checks, summary };
}
