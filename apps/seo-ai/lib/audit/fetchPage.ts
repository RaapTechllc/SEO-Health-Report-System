import type { PageData } from "@/lib/types";

// Honor an outbound egress proxy (HTTP_PROXY/HTTPS_PROXY/NO_PROXY) for the
// server-side fetches below. Node's global fetch does not pick these up
// automatically before Node 24, so wire undici's env proxy agent once.
let proxyConfigured = false;
async function ensureProxyDispatcher(): Promise<void> {
  if (proxyConfigured) return;
  proxyConfigured = true;
  const hasProxy =
    process.env.HTTPS_PROXY ||
    process.env.https_proxy ||
    process.env.HTTP_PROXY ||
    process.env.http_proxy;
  if (!hasProxy) return;
  try {
    const { setGlobalDispatcher, EnvHttpProxyAgent } = await import("undici");
    setGlobalDispatcher(new EnvHttpProxyAgent());
  } catch {
    // Proxy support is best-effort; fall back to direct fetch.
  }
}

const USER_AGENT =
  "Mozilla/5.0 (compatible; RankwiseBot/1.0; +https://rankwise.app/bot)";
const FETCH_TIMEOUT_MS = 12_000;
const SUBRESOURCE_TIMEOUT_MS = 5_000;

/** Build an empty PageData shell, used for both failures and as a base. */
function emptyPageData(url: string, error?: string): PageData {
  return {
    url,
    finalUrl: url,
    status: 0,
    ok: false,
    html: "",
    headers: {},
    title: null,
    metaDescription: null,
    canonical: null,
    robotsMeta: null,
    headings: [],
    links: [],
    images: [],
    jsonLd: [],
    openGraph: {},
    text: "",
    wordCount: 0,
    robotsTxt: null,
    sitemapXml: null,
    https: url.startsWith("https"),
    loadMs: 0,
    ...(error ? { error } : {}),
  };
}

/**
 * Reject hostnames that obviously point at local/private targets by NAME.
 * This is a best-effort SSRF guard operating on the literal hostname only.
 */
function isPrivateHostname(hostname: string): boolean {
  const host = hostname.toLowerCase().replace(/^\[/, "").replace(/\]$/, "");

  if (host === "localhost" || host.endsWith(".localhost")) return true;
  if (host === "0.0.0.0") return true;
  if (host === "::1" || host === "::" || host === "0:0:0:0:0:0:0:1") return true;
  if (host.endsWith(".local")) return true;

  // 127.0.0.0/8
  if (/^127\./.test(host)) return true;
  // 169.254.0.0/16 (link-local)
  if (/^169\.254\./.test(host)) return true;
  // RFC1918: 10.0.0.0/8
  if (/^10\./.test(host)) return true;
  // RFC1918: 192.168.0.0/16
  if (/^192\.168\./.test(host)) return true;
  // RFC1918: 172.16.0.0/12 -> 172.16.* .. 172.31.*
  if (/^172\.(1[6-9]|2\d|3[01])\./.test(host)) return true;

  // IPv6 unique-local / link-local literals.
  if (/^f[cd][0-9a-f]{2}:/.test(host)) return true;
  if (/^fe80:/.test(host)) return true;

  return false;
}

/** Collapse Headers into a plain Record. */
function headersToRecord(headers: Headers): Record<string, string> {
  const out: Record<string, string> = {};
  headers.forEach((value, key) => {
    out[key] = value;
  });
  return out;
}

/** Extract the inner content of the first matching tag attribute, decoded. */
function decodeEntities(input: string): string {
  return input
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#0?39;/g, "'")
    .replace(/&#x27;/gi, "'")
    .replace(/&apos;/g, "'")
    .replace(/&nbsp;/g, " ");
}

/** Pull an attribute value out of a tag string (e.g. content="..."). */
function getAttr(tag: string, attr: string): string | null {
  const re = new RegExp(
    `${attr}\\s*=\\s*("([^"]*)"|'([^']*)'|([^\\s"'>]+))`,
    "i",
  );
  const m = tag.match(re);
  if (!m) return null;
  const raw = m[2] ?? m[3] ?? m[4] ?? "";
  return decodeEntities(raw);
}

/** Resolve a possibly-relative href against the page's final URL. */
function resolveHref(href: string, base: string): string | null {
  try {
    return new URL(href, base).toString();
  } catch {
    return null;
  }
}

interface ParsedHtml {
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
}

export function parseHtml(html: string, baseUrl: string): ParsedHtml {
  // --- <title> ---
  let title: string | null = null;
  const titleMatch = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  if (titleMatch) {
    title = decodeEntities(titleMatch[1].replace(/\s+/g, " ").trim()) || null;
  }

  // --- <meta> tags (description, robots, og:*) ---
  let metaDescription: string | null = null;
  let robotsMeta: string | null = null;
  const openGraph: Record<string, string> = {};
  const metaTags = html.match(/<meta\b[^>]*>/gi) ?? [];
  for (const tag of metaTags) {
    const name = (getAttr(tag, "name") ?? "").toLowerCase();
    const property = (getAttr(tag, "property") ?? "").toLowerCase();
    const content = getAttr(tag, "content");
    if (content == null) continue;
    if (name === "description" && metaDescription == null) {
      metaDescription = content.trim() || null;
    } else if (name === "robots" && robotsMeta == null) {
      robotsMeta = content.trim() || null;
    }
    if (property.startsWith("og:")) {
      openGraph[property] = content;
    }
  }

  // --- <link rel="canonical"> ---
  let canonical: string | null = null;
  const linkTags = html.match(/<link\b[^>]*>/gi) ?? [];
  for (const tag of linkTags) {
    const rel = (getAttr(tag, "rel") ?? "").toLowerCase();
    if (rel.split(/\s+/).includes("canonical")) {
      const href = getAttr(tag, "href");
      if (href) {
        canonical = resolveHref(href, baseUrl) ?? href;
        break;
      }
    }
  }

  // --- headings h1-h6 ---
  const headings: Array<{ level: number; text: string }> = [];
  const headingRe = /<h([1-6])\b[^>]*>([\s\S]*?)<\/h\1>/gi;
  let hMatch: RegExpExecArray | null;
  while ((hMatch = headingRe.exec(html)) !== null) {
    const level = Number(hMatch[1]);
    const text = decodeEntities(
      hMatch[2].replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim(),
    );
    if (text) headings.push({ level, text });
  }

  // --- anchors ---
  const links: Array<{ href: string; text: string; internal: boolean }> = [];
  let baseHost = "";
  try {
    baseHost = new URL(baseUrl).host.toLowerCase();
  } catch {
    baseHost = "";
  }
  const anchorRe = /<a\b([^>]*)>([\s\S]*?)<\/a>/gi;
  let aMatch: RegExpExecArray | null;
  while ((aMatch = anchorRe.exec(html)) !== null) {
    const hrefRaw = getAttr(`<a ${aMatch[1]}>`, "href");
    if (hrefRaw == null) continue;
    const href = hrefRaw.trim();
    if (!href || href.startsWith("#")) continue;
    if (/^(mailto:|tel:|javascript:|data:)/i.test(href)) continue;
    const text = decodeEntities(
      aMatch[2].replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim(),
    );
    let internal: boolean;
    if (/^https?:\/\//i.test(href) || /^\/\//.test(href)) {
      const resolved = resolveHref(href, baseUrl);
      let linkHost = "";
      if (resolved) {
        try {
          linkHost = new URL(resolved).host.toLowerCase();
        } catch {
          linkHost = "";
        }
      }
      internal = linkHost !== "" && linkHost === baseHost;
    } else {
      // relative (or scheme-relative handled above) -> same host
      internal = true;
    }
    links.push({ href, text, internal });
  }

  // --- images ---
  const images: Array<{ src: string; alt: string | null }> = [];
  const imgTags = html.match(/<img\b[^>]*>/gi) ?? [];
  for (const tag of imgTags) {
    const src = getAttr(tag, "src") ?? getAttr(tag, "data-src");
    if (src == null) continue;
    const alt = getAttr(tag, "alt");
    images.push({ src, alt: alt == null ? null : alt });
  }

  // --- JSON-LD blocks ---
  const jsonLd: unknown[] = [];
  const ldRe =
    /<script\b[^>]*type\s*=\s*["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let ldMatch: RegExpExecArray | null;
  while ((ldMatch = ldRe.exec(html)) !== null) {
    const raw = ldMatch[1].trim();
    if (!raw) continue;
    try {
      jsonLd.push(JSON.parse(raw));
    } catch {
      // ignore malformed JSON-LD
    }
  }

  // --- visible text ---
  const stripped = html
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ")
    .replace(/<noscript\b[^>]*>[\s\S]*?<\/noscript>/gi, " ")
    .replace(/<!--[\s\S]*?-->/g, " ")
    .replace(/<[^>]+>/g, " ");
  const text = decodeEntities(stripped).replace(/\s+/g, " ").trim();
  const wordCount = text ? text.split(/\s+/).length : 0;

  return {
    title,
    metaDescription,
    canonical,
    robotsMeta,
    headings,
    links,
    images,
    jsonLd,
    openGraph,
    text,
    wordCount,
  };
}

/** Best-effort fetch of a subresource (robots.txt / sitemap.xml). */
async function fetchSubresource(target: string): Promise<string | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), SUBRESOURCE_TIMEOUT_MS);
  try {
    const res = await fetch(target, {
      method: "GET",
      redirect: "follow",
      signal: controller.signal,
      headers: {
        "User-Agent": USER_AGENT,
        Accept: "text/plain, application/xml, text/xml, */*",
      },
    });
    if (!res.ok) return null;
    return await res.text();
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Fetch and normalize a web page into PageData.
 * NEVER throws — failures resolve to a PageData with `ok:false` and `error`.
 */
export async function fetchPage(url: string): Promise<PageData> {
  // Validate / parse the URL up front.
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return emptyPageData(url, "Invalid URL.");
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    return emptyPageData(url, "Only http(s) URLs are supported.");
  }

  // SSRF guard by hostname name/literal.
  if (isPrivateHostname(parsed.hostname)) {
    return emptyPageData(
      url,
      "Refusing to fetch a local or private network address.",
    );
  }

  await ensureProxyDispatcher();

  const https = url.startsWith("https");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  const started = Date.now();

  let response: Response;
  try {
    response = await fetch(parsed.toString(), {
      method: "GET",
      redirect: "follow",
      signal: controller.signal,
      headers: {
        "User-Agent": USER_AGENT,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      },
    });
  } catch (err) {
    clearTimeout(timer);
    const loadMs = Date.now() - started;
    const message =
      err instanceof Error && err.name === "AbortError"
        ? "Request timed out."
        : err instanceof Error
          ? err.message
          : "Failed to fetch the page.";
    const base = emptyPageData(url, message);
    base.https = https;
    base.loadMs = loadMs;
    return base;
  } finally {
    clearTimeout(timer);
  }

  const finalUrl = response.url || parsed.toString();

  let html = "";
  try {
    html = await response.text();
  } catch {
    html = "";
  }
  const loadMs = Date.now() - started;

  const parsedHtml = parseHtml(html, finalUrl);

  // Best-effort subresources, relative to the final origin.
  let robotsTxt: string | null = null;
  let sitemapXml: string | null = null;
  try {
    const origin = new URL(finalUrl).origin;
    const [robots, sitemap] = await Promise.all([
      fetchSubresource(`${origin}/robots.txt`),
      fetchSubresource(`${origin}/sitemap.xml`),
    ]);
    robotsTxt = robots;
    sitemapXml = sitemap;
  } catch {
    robotsTxt = null;
    sitemapXml = null;
  }

  return {
    url,
    finalUrl,
    status: response.status,
    ok: response.ok,
    html,
    headers: headersToRecord(response.headers),
    title: parsedHtml.title,
    metaDescription: parsedHtml.metaDescription,
    canonical: parsedHtml.canonical,
    robotsMeta: parsedHtml.robotsMeta,
    headings: parsedHtml.headings,
    links: parsedHtml.links,
    images: parsedHtml.images,
    jsonLd: parsedHtml.jsonLd,
    openGraph: parsedHtml.openGraph,
    text: parsedHtml.text,
    wordCount: parsedHtml.wordCount,
    robotsTxt,
    sitemapXml,
    https,
    loadMs,
  };
}
