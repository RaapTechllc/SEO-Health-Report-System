"""
Schema Markup Generator

Generates JSON-LD structured data based on audit findings.
"""

import json
from typing import Any


def generate_schema_markup(
    audit_data: dict[str, Any],
    schema_type: str = "Organization"
) -> str:
    """
    Generate JSON-LD structured data for a website.

    Args:
        audit_data: Audit data including company name and URL
        schema_type: Type of schema to generate

    Returns:
        JSON-LD script tag as a string
    """
    url = audit_data.get("url", "")
    company_name = audit_data.get("company_name", "")

    generators = {
        "Organization": _generate_organization_schema,
        "WebSite": _generate_website_schema,
        "BreadcrumbList": _generate_breadcrumb_schema,
        "FAQ": _generate_faq_schema,
    }

    generator = generators.get(schema_type, _generate_organization_schema)
    schema_data = generator(url, company_name, audit_data)

    json_str = json.dumps(schema_data, indent=2)
    return f'<script type="application/ld+json">\n{json_str}\n</script>'


def generate_all_schemas(audit_data: dict[str, Any]) -> str:
    """Generate all applicable schema markup for a site."""
    schemas = []

    # Always generate Organization schema
    schemas.append(generate_schema_markup(audit_data, "Organization"))

    # Always generate WebSite schema
    schemas.append(generate_schema_markup(audit_data, "WebSite"))

    return "\n\n".join(schemas)


def _generate_organization_schema(
    url: str,
    company_name: str,
    audit_data: dict[str, Any]
) -> dict[str, Any]:
    """Generate Organization schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": company_name,
        "url": url,
    }

    # Add description if available from audit
    browser_data = audit_data.get("browser_data", {}) or {}
    if browser_data.get("meta_description"):
        schema["description"] = browser_data["meta_description"]

    # Add logo if detected
    if browser_data.get("og_image"):
        schema["logo"] = browser_data["og_image"]

    return schema


def _generate_website_schema(
    url: str,
    company_name: str,
    audit_data: dict[str, Any]
) -> dict[str, Any]:
    """Generate WebSite schema with search action."""
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": company_name,
        "url": url,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{url}search?q={{search_term_string}}"
            },
            "query-input": "required name=search_term_string"
        }
    }


def _generate_breadcrumb_schema(
    url: str,
    company_name: str,
    audit_data: dict[str, Any]
) -> dict[str, Any]:
    """Generate BreadcrumbList schema."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": url
            }
        ]
    }


def _generate_faq_schema(
    url: str,
    company_name: str,
    audit_data: dict[str, Any]
) -> dict[str, Any]:
    """Generate FAQ schema template."""
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"What does {company_name} do?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"[Replace with your answer about {company_name}]"
                }
            },
            {
                "@type": "Question",
                "name": f"How can I contact {company_name}?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "[Replace with your contact information]"
                }
            }
        ]
    }
