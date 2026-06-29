/**
 * Offline smoke test.
 *
 * Feeds realistic HTML fixtures straight through the parser + analyzers +
 * scoring to prove the analysis pipeline works end-to-end without any network
 * access. Useful in CI and in egress-restricted environments.
 *
 * Run: npm run smoke
 */
import { parseHtml } from "@/lib/audit/fetchPage";
import { analyzeTechnical } from "@/lib/audit/technical";
import { analyzeContent } from "@/lib/audit/content";
import { analyzeAiVisibility } from "@/lib/audit/aiVisibility";
import { PILLAR_WEIGHTS, type PageData } from "@/lib/types";
import { toGrade } from "@/lib/utils";

function buildPage(html: string, url: string, opts: Partial<PageData> = {}): PageData {
  const p = parseHtml(html, url);
  return {
    url,
    finalUrl: url,
    status: 200,
    ok: true,
    html,
    headers: { "content-type": "text/html" },
    title: p.title,
    metaDescription: p.metaDescription,
    canonical: p.canonical,
    robotsMeta: p.robotsMeta,
    headings: p.headings,
    links: p.links,
    images: p.images,
    jsonLd: p.jsonLd,
    openGraph: p.openGraph,
    text: p.text,
    wordCount: p.wordCount,
    robotsTxt: "User-agent: *\nAllow: /\nSitemap: https://demo.test/sitemap.xml",
    sitemapXml: "<?xml version='1.0'?><urlset><url><loc>https://demo.test/</loc></url></urlset>",
    https: url.startsWith("https"),
    loadMs: 240,
    ...opts,
  };
}

const RICH_HTML = `<!doctype html><html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Best Tankless Water Heaters (2026 Buyer's Guide) | FlowPro</title>
<meta name="description" content="An expert 2026 guide to choosing a tankless water heater: sizing, efficiency, installation costs, and the top models compared by a licensed plumber.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://demo.test/tankless-water-heaters">
<meta property="og:title" content="Best Tankless Water Heaters (2026)">
<meta property="og:description" content="Expert guide to tankless water heaters.">
<meta property="og:image" content="https://demo.test/og.jpg">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":"Best Tankless Water Heaters 2026","author":{"@type":"Person","name":"Jane Doe"}}</script>
</head><body>
<h1>Best Tankless Water Heaters for 2026</h1>
<p>Choosing a tankless water heater means balancing flow rate, energy efficiency, and installation cost. ${"In this guide we walk through everything a homeowner needs to know before buying. ".repeat(20)}</p>
<h2>How to size a tankless water heater</h2>
<p>${"Sizing depends on your peak hot-water demand measured in gallons per minute. ".repeat(20)}</p>
<h2>Gas vs electric models</h2>
<p>${"Gas units offer higher flow rates while electric units are easier to install. ".repeat(20)}</p>
<h2>Frequently asked questions</h2>
<p>${"How long do tankless heaters last? Typically 20 years with maintenance. ".repeat(15)}</p>
<a href="/installation-costs">Installation cost breakdown</a>
<a href="/maintenance">Maintenance tips</a>
<a href="/reviews">Customer reviews</a>
<a href="https://external.example.com/ref">External reference</a>
<img src="/img/unit.jpg" alt="A wall-mounted tankless water heater">
<img src="/img/diagram.png" alt="Sizing diagram for tankless heaters">
<img src="/img/spacer.gif">
</body></html>`;

const THIN_HTML = `<!doctype html><html><head><title>Home</title></head>
<body><h1>Welcome</h1><p>Hello world.</p></body></html>`;

async function scoreFixture(name: string, html: string) {
  const page = buildPage(html, "https://demo.test/page");
  const tech = analyzeTechnical(page);
  const content = analyzeContent(page);
  const ai = await analyzeAiVisibility(page); // no API key -> heuristic
  const aiScore = ai.score;
  const overall = Math.round(
    tech.score * PILLAR_WEIGHTS.technical +
      content.score * PILLAR_WEIGHTS.content +
      aiScore * PILLAR_WEIGHTS.aiVisibility,
  );
  console.log(`\n=== ${name} ===`);
  console.log(`parsed: title=${JSON.stringify(page.title)} h=${page.headings.length} links=${page.links.length} imgs=${page.images.length} jsonLd=${page.jsonLd.length} words=${page.wordCount}`);
  console.log(`technical  ${String(tech.score).padStart(3)} ${tech.grade}  (${tech.checks.length} checks)`);
  console.log(`content    ${String(content.score).padStart(3)} ${content.grade}  (${content.checks.length} checks)`);
  console.log(`aiVisib.   ${String(aiScore).padStart(3)} ${toGrade(aiScore)}  (${ai.checks.length} checks, live=${ai.usedLiveAI})`);
  console.log(`OVERALL    ${String(overall).padStart(3)} ${toGrade(overall)}`);
}

(async () => {
  await scoreFixture("RICH page (optimized)", RICH_HTML);
  await scoreFixture("THIN page (minimal)", THIN_HTML);
})();
