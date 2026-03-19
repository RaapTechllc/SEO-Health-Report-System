"""
Action Classifier

Classifies raw audit issues and recommendations into DFY/DWY/DIY tiers.
Each issue gets concrete next steps based on what can be automated,
what needs guided implementation, and what requires strategic decisions.
"""

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Classification rules: maps issue categories to action tiers and templates.
# Key: (category, severity_or_pattern) → tier, effort_minutes, artifact_type
DFY_PATTERNS = {
    # Technical SEO — automatable fixes
    "robots_txt": {
        "tier": "dfy",
        "effort_minutes": 1,
        "artifact_type": "robots_txt",
        "title_template": "Generate optimized robots.txt",
        "validation": "Upload to site root and verify at /robots.txt",
    },
    "sitemap": {
        "tier": "dfy",
        "effort_minutes": 1,
        "artifact_type": "sitemap_xml",
        "title_template": "Generate XML sitemap",
        "validation": "Upload sitemap.xml and submit in Google Search Console",
    },
    "meta_tags": {
        "tier": "dfy",
        "effort_minutes": 2,
        "artifact_type": "meta_tags",
        "title_template": "Generate optimized meta tags",
        "validation": "View page source and verify meta tags are present",
    },
    "schema_markup": {
        "tier": "dfy",
        "effort_minutes": 2,
        "artifact_type": "schema_json",
        "title_template": "Generate JSON-LD structured data",
        "validation": "Test at https://search.google.com/test/rich-results",
    },
    "canonical": {
        "tier": "dfy",
        "effort_minutes": 1,
        "artifact_type": "canonical_tag",
        "title_template": "Generate canonical URL tags",
        "validation": "View page source and verify <link rel='canonical'> tag",
    },
    "redirect": {
        "tier": "dfy",
        "effort_minutes": 5,
        "artifact_type": "redirect_rules",
        "title_template": "Generate redirect rules for broken URLs",
        "validation": "Test redirect with curl -I or browser dev tools",
    },
}

DWY_PATTERNS = {
    # Issues that need human implementation but have exact instructions
    "viewport": {
        "tier": "dwy",
        "effort_minutes": 5,
        "title_template": "Add mobile viewport meta tag",
        "instructions": [
            "Open your HTML template or layout file",
            "Add this tag inside the <head> section:",
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "Save and deploy the file",
        ],
        "validation": "Inspect page source to confirm viewport tag is present",
    },
    "alt_text": {
        "tier": "dwy",
        "effort_minutes": 15,
        "title_template": "Add alt text to images",
        "instructions": [
            "Identify all images without alt attributes",
            "For each image, add descriptive alt text that describes the image content",
            'Example: <img src="photo.jpg" alt="Team meeting in conference room">',
            "Alt text should be concise (125 characters or less) and descriptive",
        ],
        "validation": "Run accessibility checker to verify all images have alt text",
    },
    "heading_structure": {
        "tier": "dwy",
        "effort_minutes": 20,
        "title_template": "Fix heading hierarchy",
        "instructions": [
            "Ensure each page has exactly one <h1> tag",
            "Use <h2> for main sections, <h3> for subsections",
            "Don't skip heading levels (e.g., h1 → h3 without h2)",
            "Include target keywords naturally in headings",
        ],
        "validation": "Use browser dev tools to inspect heading hierarchy",
    },
    "internal_links": {
        "tier": "dwy",
        "effort_minutes": 30,
        "title_template": "Improve internal linking structure",
        "instructions": [
            "Identify orphan pages (pages with no incoming internal links)",
            "Add contextual links from related content pages to orphan pages",
            "Ensure every important page is reachable within 3 clicks from homepage",
            "Use descriptive anchor text (not 'click here')",
        ],
        "validation": "Run a site crawl to verify all pages are reachable",
    },
    "eeat_authors": {
        "tier": "dwy",
        "effort_minutes": 45,
        "title_template": "Add author attribution for E-E-A-T",
        "instructions": [
            "Create author bio pages for each content creator",
            "Include credentials, experience, and relevant expertise",
            "Link from articles to author bio pages",
            "Add author schema markup (Person type) to author pages",
        ],
        "validation": "Verify author links appear on content pages and bio pages exist",
    },
    "security_headers": {
        "tier": "dwy",
        "effort_minutes": 15,
        "title_template": "Add security headers",
        "instructions": [
            "Add the following headers to your web server configuration:",
            "Strict-Transport-Security: max-age=31536000; includeSubDomains",
            "X-Content-Type-Options: nosniff",
            "X-Frame-Options: SAMEORIGIN",
            "Referrer-Policy: strict-origin-when-cross-origin",
        ],
        "validation": "Check headers at https://securityheaders.com",
    },
}

DIY_PATTERNS = {
    # Strategic items requiring human judgment
    "content_quality": {
        "tier": "diy",
        "effort_minutes": 240,
        "title_template": "Improve content quality and depth",
        "strategy": (
            "Audit thin content pages (under 500 words) and expand them with "
            "original research, data, expert quotes, and multimedia. Focus on "
            "pages that target your primary keywords. Aim for comprehensive "
            "coverage that answers all related questions a searcher might have."
        ),
    },
    "backlink_building": {
        "tier": "diy",
        "effort_minutes": 480,
        "title_template": "Build quality backlink profile",
        "strategy": (
            "Develop a link acquisition strategy: (1) Create linkable assets "
            "(original research, tools, comprehensive guides), (2) Reach out to "
            "industry publications for guest posts, (3) Reclaim unlinked brand "
            "mentions, (4) Participate in industry forums and communities. "
            "Focus on quality over quantity — one link from a DA60+ domain is "
            "worth more than 50 links from low-quality sites."
        ),
    },
    "ai_visibility": {
        "tier": "diy",
        "effort_minutes": 120,
        "title_template": "Optimize for AI search visibility",
        "strategy": (
            "Structure content to be easily parsed by AI systems: (1) Use clear "
            "question-and-answer formatting, (2) Include factual statements that "
            "AI can cite, (3) Add comprehensive schema markup, (4) Ensure brand "
            "information is consistent across Wikipedia, Wikidata, and LinkedIn, "
            "(5) Create authoritative content that AI systems will reference."
        ),
    },
    "topical_authority": {
        "tier": "diy",
        "effort_minutes": 480,
        "title_template": "Build topical authority with content clusters",
        "strategy": (
            "Map your core topics and create pillar-cluster content architecture: "
            "(1) Identify 3-5 pillar topics, (2) Create comprehensive pillar "
            "pages (3000+ words), (3) Write 5-10 supporting cluster articles "
            "for each pillar, (4) Interlink clusters to pillar pages. "
            "This establishes topical authority that both search engines and "
            "AI systems recognize."
        ),
    },
}


def classify_actions(audit_results: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Classify all audit issues and recommendations into DFY/DWY/DIY action items.

    Args:
        audit_results: Full audit results from run_full_audit()

    Returns:
        List of action item dicts sorted by impact-to-effort ratio (highest ROI first)
    """
    actions = []
    seen_categories = set()

    audits = audit_results.get("audits", {})

    for audit_name, audit_data in audits.items():
        if not audit_data or not isinstance(audit_data, dict):
            continue

        # Process issues from main audit
        for issue in audit_data.get("issues", []):
            action = _classify_issue(issue, audit_name, seen_categories)
            if action:
                actions.append(action)

        # Process issues from components
        for _comp_name, comp_data in audit_data.get("components", {}).items():
            if isinstance(comp_data, dict):
                for issue in comp_data.get("issues", []):
                    action = _classify_issue(issue, audit_name, seen_categories)
                    if action:
                        actions.append(action)

        # Process recommendations
        for rec in audit_data.get("recommendations", []):
            action = _classify_recommendation(rec, audit_name, seen_categories)
            if action:
                actions.append(action)

    # Sort by ROI: impact / effort_minutes (highest first)
    impact_values = {"high": 3, "medium": 2, "low": 1}
    for action in actions:
        impact_score = impact_values.get(action.get("impact", "medium"), 2)
        effort = action.get("effort_minutes", 60) or 60
        action["roi_score"] = impact_score / (effort / 60)  # impact per hour

    actions.sort(key=lambda x: x.get("roi_score", 0), reverse=True)

    # Assign sequential IDs
    for i, action in enumerate(actions, 1):
        action["id"] = f"action-{i:03d}"

    return actions


def _classify_issue(
    issue: dict[str, Any],
    audit_name: str,
    seen: set
) -> dict[str, Any] | None:
    """Classify a single issue into an action item."""
    category = issue.get("category", "").lower()
    description = issue.get("description", "")
    severity = issue.get("severity", "medium")

    # Deduplicate by description
    desc_hash = hashlib.md5(description.encode()).hexdigest()[:8]
    if desc_hash in seen:
        return None
    seen.add(desc_hash)

    # Try DFY classification first
    for pattern_key, pattern in DFY_PATTERNS.items():
        if pattern_key in category or pattern_key in description.lower():
            return {
                "title": pattern["title_template"],
                "tier": "dfy",
                "pillar": _normalize_pillar(audit_name),
                "severity": severity,
                "effort_minutes": pattern["effort_minutes"],
                "impact": _severity_to_impact(severity),
                "description": description,
                "artifact_type": pattern.get("artifact_type"),
                "validation": pattern.get("validation"),
                "source_issue": description,
            }

    # Try DWY classification
    for pattern_key, pattern in DWY_PATTERNS.items():
        if pattern_key in category or pattern_key in description.lower():
            return {
                "title": pattern["title_template"],
                "tier": "dwy",
                "pillar": _normalize_pillar(audit_name),
                "severity": severity,
                "effort_minutes": pattern["effort_minutes"],
                "impact": _severity_to_impact(severity),
                "description": description,
                "instructions": pattern.get("instructions", []),
                "validation": pattern.get("validation"),
                "source_issue": description,
            }

    # Try DIY classification
    for pattern_key, pattern in DIY_PATTERNS.items():
        if pattern_key in category or pattern_key in description.lower():
            return {
                "title": pattern["title_template"],
                "tier": "diy",
                "pillar": _normalize_pillar(audit_name),
                "severity": severity,
                "effort_minutes": pattern["effort_minutes"],
                "impact": _severity_to_impact(severity),
                "description": description,
                "strategy": pattern.get("strategy"),
                "source_issue": description,
            }

    # Default: classify based on severity and whether it's automatable
    if _is_automatable(description):
        return {
            "title": _generate_title(description),
            "tier": "dwy",
            "pillar": _normalize_pillar(audit_name),
            "severity": severity,
            "effort_minutes": 30,
            "impact": _severity_to_impact(severity),
            "description": description,
            "instructions": [f"Review and fix: {description}"],
            "source_issue": description,
        }
    else:
        return {
            "title": _generate_title(description),
            "tier": "diy",
            "pillar": _normalize_pillar(audit_name),
            "severity": severity,
            "effort_minutes": 60,
            "impact": _severity_to_impact(severity),
            "description": description,
            "strategy": f"Evaluate and address: {description}",
            "source_issue": description,
        }


def _classify_recommendation(
    rec: dict[str, Any],
    audit_name: str,
    seen: set
) -> dict[str, Any] | None:
    """Classify a recommendation into an action item."""
    action_text = rec.get("action", "")
    category = rec.get("category", "").lower()
    priority = rec.get("priority", "medium")

    desc_hash = hashlib.md5(action_text.encode()).hexdigest()[:8]
    if desc_hash in seen:
        return None
    seen.add(desc_hash)

    # Check against all pattern dictionaries
    for pattern_key, pattern in DFY_PATTERNS.items():
        if pattern_key in category or pattern_key in action_text.lower():
            return {
                "title": pattern["title_template"],
                "tier": "dfy",
                "pillar": _normalize_pillar(audit_name),
                "severity": priority,
                "effort_minutes": pattern["effort_minutes"],
                "impact": rec.get("impact", "medium"),
                "description": action_text,
                "artifact_type": pattern.get("artifact_type"),
                "validation": pattern.get("validation"),
                "source_issue": action_text,
            }

    for pattern_key, pattern in DWY_PATTERNS.items():
        if pattern_key in category or pattern_key in action_text.lower():
            return {
                "title": pattern["title_template"],
                "tier": "dwy",
                "pillar": _normalize_pillar(audit_name),
                "severity": priority,
                "effort_minutes": pattern["effort_minutes"],
                "impact": rec.get("impact", "medium"),
                "description": action_text,
                "instructions": pattern.get("instructions", []),
                "validation": pattern.get("validation"),
                "source_issue": action_text,
            }

    for pattern_key, pattern in DIY_PATTERNS.items():
        if pattern_key in category or pattern_key in action_text.lower():
            return {
                "title": pattern["title_template"],
                "tier": "diy",
                "pillar": _normalize_pillar(audit_name),
                "severity": priority,
                "effort_minutes": pattern["effort_minutes"],
                "impact": rec.get("impact", "medium"),
                "description": action_text,
                "strategy": pattern.get("strategy"),
                "source_issue": action_text,
            }

    # Default classification for recommendations
    effort = rec.get("effort", "medium")
    effort_minutes = {"low": 15, "medium": 60, "high": 240}.get(effort, 60)

    return {
        "title": _generate_title(action_text),
        "tier": "dwy" if effort in ("low", "medium") else "diy",
        "pillar": _normalize_pillar(audit_name),
        "severity": priority,
        "effort_minutes": effort_minutes,
        "impact": rec.get("impact", "medium"),
        "description": action_text,
        "instructions": [f"Implement: {action_text}"] if effort != "high" else [],
        "strategy": action_text if effort == "high" else None,
        "source_issue": action_text,
    }


def _normalize_pillar(audit_name: str) -> str:
    """Normalize audit name to pillar identifier."""
    mapping = {
        "technical": "technical",
        "content": "content",
        "ai_visibility": "ai_visibility",
    }
    return mapping.get(audit_name, audit_name)


def _severity_to_impact(severity: str) -> str:
    """Map severity to impact level."""
    return {
        "critical": "high",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }.get(severity, "medium")


def _is_automatable(description: str) -> bool:
    """Check if an issue description suggests an automatable fix."""
    automatable_keywords = [
        "missing", "add", "tag", "meta", "header", "redirect",
        "robots", "sitemap", "canonical", "schema", "alt text",
        "viewport", "https", "ssl", "security header"
    ]
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in automatable_keywords)


def _generate_title(description: str) -> str:
    """Generate a concise title from a description."""
    # Truncate to reasonable title length
    if len(description) <= 60:
        return description
    return description[:57] + "..."


def get_action_summary(actions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Generate summary statistics for classified actions.

    Args:
        actions: List of classified action items

    Returns:
        Summary dict with tier counts, effort estimates, and quick starts
    """
    dfy_items = [a for a in actions if a.get("tier") == "dfy"]
    dwy_items = [a for a in actions if a.get("tier") == "dwy"]
    diy_items = [a for a in actions if a.get("tier") == "diy"]

    dfy_effort = sum(a.get("effort_minutes", 0) or 0 for a in dfy_items)
    dwy_effort = sum(a.get("effort_minutes", 0) or 0 for a in dwy_items)
    diy_effort = sum(a.get("effort_minutes", 0) or 0 for a in diy_items)

    return {
        "total_actions": len(actions),
        "dfy_count": len(dfy_items),
        "dwy_count": len(dwy_items),
        "diy_count": len(diy_items),
        "dfy_effort_minutes": dfy_effort,
        "dwy_effort_minutes": dwy_effort,
        "diy_effort_minutes": diy_effort,
        "total_effort_minutes": dfy_effort + dwy_effort + diy_effort,
        "automation_savings_minutes": dfy_effort * 10,  # Estimated manual time if done by hand
        "quick_starts": list(dfy_items[:3]),  # Top 3 DFY items to apply immediately
    }
