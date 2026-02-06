"""
HTTP response mocks for offline testing.

Provides builders for common SEO-related HTTP responses including
robots.txt, sitemaps, and HTML pages with various configurations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class MockResponse:
    """Mock HTTP response for testing."""

    status_code: int = 200
    content: str = ""
    content_type: str = "text/html"
    headers: dict[str, str] = field(default_factory=dict)
    response_time_ms: int = 100
    redirect_to: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status_code": self.status_code,
            "content": self.content,
            "content_type": self.content_type,
            "headers": self.headers,
            "response_time_ms": self.response_time_ms,
            "redirect_to": self.redirect_to,
        }


class MockResponseBuilder:
    """Builder for creating mock HTTP responses."""

    def __init__(self):
        self.responses: dict[str, MockResponse] = {}

    def add_robots_txt(
        self,
        base_url: str,
        allow_all: bool = True,
        disallow_paths: Optional[list[str]] = None,
        sitemap_urls: Optional[list[str]] = None,
        crawl_delay: Optional[int] = None,
    ) -> "MockResponseBuilder":
        """Add a robots.txt response."""
        content = build_robots_txt(
            allow_all=allow_all,
            disallow_paths=disallow_paths or [],
            sitemap_urls=sitemap_urls or [],
            crawl_delay=crawl_delay,
        )
        self.responses[f"{base_url}/robots.txt"] = MockResponse(
            status_code=200,
            content=content,
            content_type="text/plain",
        )
        return self

    def add_sitemap(
        self,
        url: str,
        page_urls: list[str],
        include_lastmod: bool = True,
    ) -> "MockResponseBuilder":
        """Add a sitemap.xml response."""
        content = build_sitemap_xml(
            urls=page_urls,
            include_lastmod=include_lastmod,
        )
        self.responses[url] = MockResponse(
            status_code=200,
            content=content,
            content_type="application/xml",
        )
        return self

    def add_html_page(
        self,
        url: str,
        title: str = "Test Page",
        description: Optional[str] = None,
        canonical: Optional[str] = None,
        noindex: bool = False,
        schema: Optional[dict[str, Any]] = None,
        has_viewport: bool = True,
        internal_links: Optional[list[str]] = None,
    ) -> "MockResponseBuilder":
        """Add an HTML page response."""
        content = build_html_page(
            title=title,
            description=description,
            canonical=canonical,
            noindex=noindex,
            schema=schema,
            has_viewport=has_viewport,
            internal_links=internal_links or [],
        )
        self.responses[url] = MockResponse(
            status_code=200,
            content=content,
            content_type="text/html",
            headers={"X-Content-Type-Options": "nosniff"},
        )
        return self

    def add_redirect(
        self,
        from_url: str,
        to_url: str,
        status_code: int = 301,
    ) -> "MockResponseBuilder":
        """Add a redirect response."""
        self.responses[from_url] = MockResponse(
            status_code=status_code,
            content="",
            redirect_to=to_url,
            headers={"Location": to_url},
        )
        return self

    def add_error(
        self,
        url: str,
        status_code: int = 404,
        message: str = "Not Found",
    ) -> "MockResponseBuilder":
        """Add an error response."""
        self.responses[url] = MockResponse(
            status_code=status_code,
            content=message,
            content_type="text/plain",
        )
        return self

    def build(self) -> dict[str, MockResponse]:
        """Build and return all mock responses."""
        return self.responses


def build_robots_txt(
    allow_all: bool = True,
    disallow_paths: Optional[list[str]] = None,
    sitemap_urls: Optional[list[str]] = None,
    crawl_delay: Optional[int] = None,
    user_agent: str = "*",
) -> str:
    """
    Build a robots.txt content string.

    Args:
        allow_all: If True, allows all paths (default behavior)
        disallow_paths: Paths to disallow
        sitemap_urls: Sitemap URLs to include
        crawl_delay: Optional crawl delay in seconds
        user_agent: User agent to apply rules to

    Returns:
        robots.txt content as string
    """
    lines = [f"User-agent: {user_agent}"]

    if allow_all and not disallow_paths:
        lines.append("Allow: /")
    elif disallow_paths:
        for path in disallow_paths:
            lines.append(f"Disallow: {path}")

    if crawl_delay is not None:
        lines.append(f"Crawl-delay: {crawl_delay}")

    if sitemap_urls:
        for sitemap_url in sitemap_urls:
            lines.append(f"Sitemap: {sitemap_url}")

    return "\n".join(lines)


def build_sitemap_xml(
    urls: list[str],
    include_lastmod: bool = True,
    include_changefreq: bool = False,
    include_priority: bool = False,
) -> str:
    """
    Build a sitemap.xml content string.

    Args:
        urls: List of page URLs to include
        include_lastmod: Include lastmod dates
        include_changefreq: Include change frequency
        include_priority: Include priority values

    Returns:
        sitemap.xml content as string
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    today = datetime.now().strftime("%Y-%m-%d")

    for i, url in enumerate(urls):
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")

        if include_lastmod:
            lines.append(f"    <lastmod>{today}</lastmod>")

        if include_changefreq:
            freq = "weekly" if i == 0 else "monthly"
            lines.append(f"    <changefreq>{freq}</changefreq>")

        if include_priority:
            priority = "1.0" if i == 0 else "0.8"
            lines.append(f"    <priority>{priority}</priority>")

        lines.append("  </url>")

    lines.append("</urlset>")
    return "\n".join(lines)


def build_html_page(
    title: str = "Test Page",
    description: Optional[str] = None,
    canonical: Optional[str] = None,
    noindex: bool = False,
    nofollow: bool = False,
    schema: Optional[dict[str, Any]] = None,
    has_viewport: bool = True,
    internal_links: Optional[list[str]] = None,
    h1: Optional[str] = None,
    body_content: Optional[str] = None,
) -> str:
    """
    Build an HTML page for testing.

    Args:
        title: Page title
        description: Meta description
        canonical: Canonical URL
        noindex: Include noindex meta
        nofollow: Include nofollow meta
        schema: JSON-LD schema data
        has_viewport: Include viewport meta
        internal_links: Internal links to include
        h1: Main heading
        body_content: Additional body content

    Returns:
        HTML content as string
    """
    meta_tags = []

    if description:
        meta_tags.append(f'<meta name="description" content="{description}">')

    if has_viewport:
        meta_tags.append('<meta name="viewport" content="width=device-width, initial-scale=1">')

    robots_content = []
    if noindex:
        robots_content.append("noindex")
    if nofollow:
        robots_content.append("nofollow")
    if robots_content:
        meta_tags.append(f'<meta name="robots" content="{", ".join(robots_content)}">')

    if canonical:
        meta_tags.append(f'<link rel="canonical" href="{canonical}">')

    schema_script = ""
    if schema:
        import json
        schema_script = f'''
<script type="application/ld+json">
{json.dumps(schema, indent=2)}
</script>'''

    links_html = ""
    if internal_links:
        links_html = "\n".join([
            f'<a href="{link}">Link to {link}</a>'
            for link in internal_links
        ])

    h1_content = h1 or title
    body = body_content or f"<p>This is test content for {title}.</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {chr(10).join(meta_tags)}
    {schema_script}
</head>
<body>
    <h1>{h1_content}</h1>
    {body}
    <nav>
        {links_html}
    </nav>
</body>
</html>"""


def get_mock_responses(fixture_name: str) -> dict[str, MockResponse]:
    """
    Get pre-built mock responses for a fixture site.

    Args:
        fixture_name: Name of the fixture site

    Returns:
        Dictionary of URL -> MockResponse
    """
    from .sites import FIXTURE_SITES

    fixture = FIXTURE_SITES.get(fixture_name)
    if not fixture:
        return {}

    builder = MockResponseBuilder()

    for path, config in fixture.mock_responses.items():
        if path.startswith("_"):
            continue

        url = f"{fixture.url.rstrip('/')}{path}" if not path.startswith("http") else path

        status = config.get("status", 200)

        if "redirect_to" in config:
            builder.add_redirect(url, config["redirect_to"], status)
        elif status >= 400:
            builder.add_error(url, status, config.get("content", "Error"))
        elif "html_template" in config:
            template = config["html_template"]
            builder.responses[url] = _build_from_template(
                template, fixture.url, fixture.company_name
            )
        else:
            builder.responses[url] = MockResponse(
                status_code=status,
                content=config.get("content", ""),
                content_type=config.get("content_type", "text/plain"),
            )

    return builder.build()


def _build_from_template(
    template_name: str,
    base_url: str,
    company_name: str,
) -> MockResponse:
    """Build a MockResponse from a template name."""

    if template_name == "healthy":
        schema = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": company_name,
            "url": base_url,
            "telephone": "+1-555-123-4567",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "123 Main St",
                "addressLocality": "Anytown",
                "addressRegion": "CA",
                "postalCode": "90210",
            },
        }
        content = build_html_page(
            title=f"{company_name} | Professional Services",
            description=f"{company_name} provides professional services in your area. Contact us today!",
            canonical=base_url,
            schema=schema,
            has_viewport=True,
            internal_links=[f"{base_url}/services", f"{base_url}/contact", f"{base_url}/about"],
        )

    elif template_name == "basic":
        content = build_html_page(
            title=f"{company_name}",
            description=f"Welcome to {company_name}",
            canonical=base_url,
            has_viewport=True,
        )

    elif template_name == "no_schema":
        content = build_html_page(
            title=f"{company_name}",
            description=f"Welcome to {company_name}",
            canonical=base_url,
            has_viewport=True,
            schema=None,
        )

    elif template_name == "blocked":
        content = build_html_page(
            title=f"{company_name}",
            noindex=True,
            nofollow=True,
        )

    elif template_name == "slow":
        content = build_html_page(
            title=f"{company_name}",
            description=f"Welcome to {company_name}",
            canonical=base_url,
            has_viewport=True,
            body_content="<p>Page with slow loading resources...</p>" * 100,
        )

    elif template_name == "missing_meta":
        content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{company_name}</title>
</head>
<body>
    <h1>{company_name}</h1>
    <p>This page is missing meta tags.</p>
</body>
</html>"""

    elif template_name == "insecure":
        content = build_html_page(
            title=f"{company_name}",
            description=f"Welcome to {company_name}",
            has_viewport=True,
            body_content='<img src="http://insecure.test/image.jpg">',
        )

    elif template_name == "noindex":
        content = build_html_page(
            title=f"{company_name}",
            description=f"Welcome to {company_name}",
            canonical=base_url,
            has_viewport=True,
            noindex=True,
        )

    elif template_name == "broken_links":
        content = build_html_page(
            title=f"{company_name}",
            description=f"Welcome to {company_name}",
            canonical=base_url,
            has_viewport=True,
            internal_links=[
                f"{base_url}/services",
                f"{base_url}/about",
                f"{base_url}/nonexistent-page",
            ],
        )

    else:
        content = build_html_page(title=f"{company_name}")

    return MockResponse(
        status_code=200,
        content=content,
        content_type="text/html",
    )


__all__ = [
    "MockResponse",
    "MockResponseBuilder",
    "get_mock_responses",
    "build_robots_txt",
    "build_sitemap_xml",
    "build_html_page",
]
