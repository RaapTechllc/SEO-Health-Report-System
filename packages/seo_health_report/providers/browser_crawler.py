"""
Browser-based SEO crawler using Playwright.
Extracts SEO elements from fully-rendered pages (JavaScript support).
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from playwright.async_api import Browser, Page, async_playwright


@dataclass
class SEOData:
    """Extracted SEO data from a page."""
    url: str
    title: str = ""
    meta_description: str = ""
    meta_robots: str = ""
    canonical_url: str = ""
    h1_tags: list[str] = field(default_factory=list)
    h2_tags: list[str] = field(default_factory=list)
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    schema_json: list[dict] = field(default_factory=list)
    internal_links: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)
    images_without_alt: int = 0
    total_images: int = 0
    page_load_time_ms: float = 0
    html_size_bytes: int = 0
    error: Optional[str] = None


class BrowserCrawler:
    """High-performance browser crawler for SEO audits."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._browser: Optional[Browser] = None
        self._playwright = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def crawl_page(self, url: str, timeout_ms: int = 30000) -> SEOData:
        """Crawl a single page and extract SEO data."""
        if not self._browser:
            raise RuntimeError("Browser not initialized. Use 'async with BrowserCrawler():'")

        data = SEOData(url=url)
        page = await self._browser.new_page()

        try:
            start_time = asyncio.get_event_loop().time()
            response = await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            data.page_load_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            if response:
                data.html_size_bytes = len(await response.body())

            data.title = await self._get_text(page, "title")
            data.meta_description = await self._get_meta(page, "description")
            data.meta_robots = await self._get_meta(page, "robots")
            data.canonical_url = await self._get_link_href(page, 'link[rel="canonical"]')
            data.og_title = await self._get_meta(page, "og:title", is_property=True)
            data.og_description = await self._get_meta(page, "og:description", is_property=True)
            data.og_image = await self._get_meta(page, "og:image", is_property=True)
            data.h1_tags = await self._get_all_text(page, "h1")
            data.h2_tags = await self._get_all_text(page, "h2")
            data.schema_json = await self._extract_schema(page)

            links = await self._extract_links(page, url)
            data.internal_links = links["internal"]
            data.external_links = links["external"]

            images = await self._analyze_images(page)
            data.total_images = images["total"]
            data.images_without_alt = images["without_alt"]

        except Exception as e:
            data.error = str(e)
        finally:
            await page.close()

        return data

    async def _get_text(self, page: Page, selector: str) -> str:
        try:
            el = await page.query_selector(selector)
            return await el.inner_text() if el else ""
        except Exception:
            return ""

    async def _get_meta(self, page: Page, name: str, is_property: bool = False) -> str:
        try:
            attr = "property" if is_property else "name"
            el = await page.query_selector(f'meta[{attr}="{name}"]')
            return await el.get_attribute("content") if el else ""
        except Exception:
            return ""

    async def _get_link_href(self, page: Page, selector: str) -> str:
        try:
            el = await page.query_selector(selector)
            return await el.get_attribute("href") if el else ""
        except Exception:
            return ""

    async def _get_all_text(self, page: Page, selector: str) -> list[str]:
        try:
            elements = await page.query_selector_all(selector)
            return [await el.inner_text() for el in elements]
        except Exception:
            return []

    async def _extract_schema(self, page: Page) -> list[dict]:
        try:
            return await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    return Array.from(scripts).map(s => {
                        try { return JSON.parse(s.textContent); }
                        catch { return null; }
                    }).filter(Boolean);
                }
            """)
        except Exception:
            return []

    async def _extract_links(self, page: Page, base_url: str) -> dict:
        try:
            from urllib.parse import urlparse
            base_domain = urlparse(base_url).netloc

            links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(h => h.startsWith('http'))
            """)

            internal = [l for l in links if urlparse(l).netloc == base_domain]
            external = [l for l in links if urlparse(l).netloc != base_domain]

            return {"internal": list(set(internal)), "external": list(set(external))}
        except Exception:
            return {"internal": [], "external": []}

    async def _analyze_images(self, page: Page) -> dict:
        try:
            return await page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('img');
                    const withoutAlt = Array.from(imgs).filter(i => !i.alt || i.alt.trim() === '').length;
                    return { total: imgs.length, without_alt: withoutAlt };
                }
            """)
        except Exception:
            return {"total": 0, "without_alt": 0}


async def test_crawler(url: str = "https://www.sheetmetalwerks.com"):
    """Test the crawler on a given URL."""
    print(f"🔍 Crawling: {url}")

    async with BrowserCrawler(headless=True) as crawler:
        data = await crawler.crawl_page(url)

    if data.error:
        print(f"❌ Error: {data.error}")
        return data

    print(f"✅ Title: {data.title}")
    print(f"📝 Meta Description: {data.meta_description[:100]}..." if data.meta_description else "📝 Meta Description: (none)")
    print(f"🔗 Canonical: {data.canonical_url}")
    print(f"📰 H1 Tags: {data.h1_tags}")
    print(f"🖼️ Images: {data.total_images} total, {data.images_without_alt} without alt")
    print(f"🔗 Internal Links: {len(data.internal_links)}")
    print(f"🌐 External Links: {len(data.external_links)}")
    print(f"📊 Schema.org: {len(data.schema_json)} blocks")
    print(f"⏱️ Load Time: {data.page_load_time_ms:.0f}ms")
    print(f"📦 Page Size: {data.html_size_bytes / 1024:.1f}KB")

    return data


if __name__ == "__main__":
    asyncio.run(test_crawler())
