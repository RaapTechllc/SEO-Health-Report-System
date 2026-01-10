"""
Validate Structured Data

Extract and validate JSON-LD, Microdata, and RDFa structured data.
"""

import re
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class SchemaIssue:
    """A structured data issue found during validation."""
    severity: str
    category: str
    schema_type: str
    description: str
    property_name: Optional[str] = None
    recommendation: str = ""


# Required properties for common schema types
REQUIRED_PROPERTIES = {
    "Organization": ["name", "url"],
    "LocalBusiness": ["name", "address"],
    "Product": ["name"],
    "Article": ["headline", "author"],
    "BlogPosting": ["headline", "author"],
    "FAQPage": ["mainEntity"],
    "HowTo": ["name", "step"],
    "WebPage": ["name"],
    "BreadcrumbList": ["itemListElement"],
    "Person": ["name"],
    "Event": ["name", "startDate", "location"],
    "Review": ["itemReviewed", "reviewRating"],
    "AggregateRating": ["ratingValue", "reviewCount"]
}

# Recommended properties for better rich results
RECOMMENDED_PROPERTIES = {
    "Organization": ["logo", "description", "contactPoint", "sameAs"],
    "LocalBusiness": ["telephone", "openingHours", "priceRange", "geo"],
    "Product": ["description", "image", "offers", "aggregateRating"],
    "Article": ["datePublished", "image", "publisher"],
    "BlogPosting": ["datePublished", "image", "publisher"],
    "FAQPage": [],  # mainEntity covers it
    "HowTo": ["description", "image", "totalTime"],
    "Event": ["description", "image", "offers", "performer"],
    "Review": ["author", "datePublished"],
}


def fetch_page(url: str, timeout: int = 30) -> Optional[str]:
    """Fetch HTML content from URL."""
    try:
        import requests
        headers = {'User-Agent': 'SEO-Health-Report-Bot/1.0'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception:
        return None


def extract_json_ld(html: str) -> List[Dict[str, Any]]:
    """
    Extract JSON-LD structured data from HTML.

    Args:
        html: HTML content

    Returns:
        List of parsed JSON-LD objects
    """
    results = []

    # Find all JSON-LD script tags
    pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

    for match in matches:
        try:
            data = json.loads(match.strip())

            # Handle single object or array
            if isinstance(data, list):
                results.extend(data)
            else:
                results.append(data)

        except json.JSONDecodeError:
            # Will be reported as an issue
            results.append({"_parse_error": True, "_raw": match[:200]})

    return results


def extract_microdata(html: str) -> List[Dict[str, Any]]:
    """
    Extract Microdata structured data from HTML.

    Args:
        html: HTML content

    Returns:
        List of microdata items found
    """
    results = []

    # Find itemscope elements
    itemscope_pattern = r'<[^>]+itemscope[^>]*itemtype=["\']([^"\']+)["\'][^>]*>'
    matches = re.findall(itemscope_pattern, html, re.IGNORECASE)

    for itemtype in matches:
        # Extract schema type from URL
        schema_type = itemtype.split("/")[-1]
        results.append({
            "@type": schema_type,
            "_format": "microdata",
            "_itemtype": itemtype
        })

    return results


def extract_rdfa(html: str) -> List[Dict[str, Any]]:
    """
    Extract RDFa structured data from HTML.

    Args:
        html: HTML content

    Returns:
        List of RDFa items found
    """
    results = []

    # Find typeof attributes
    typeof_pattern = r'typeof=["\']([^"\']+)["\']'
    matches = re.findall(typeof_pattern, html, re.IGNORECASE)

    for typeof in matches:
        results.append({
            "@type": typeof,
            "_format": "rdfa"
        })

    return results


def extract_structured_data(html: str) -> Dict[str, Any]:
    """
    Extract all structured data from HTML.

    Args:
        html: HTML content

    Returns:
        Dict with all structured data found
    """
    return {
        "json_ld": extract_json_ld(html),
        "microdata": extract_microdata(html),
        "rdfa": extract_rdfa(html)
    }


def validate_schema(schema_data: Dict[str, Any]) -> List[SchemaIssue]:
    """
    Validate a single schema object.

    Args:
        schema_data: Schema object to validate

    Returns:
        List of validation issues
    """
    issues = []

    # Check for parse errors
    if schema_data.get("_parse_error"):
        issues.append(SchemaIssue(
            severity="high",
            category="json_ld",
            schema_type="Unknown",
            description="JSON-LD parse error - invalid JSON syntax",
            recommendation="Fix JSON syntax in structured data"
        ))
        return issues

    # Get schema type
    schema_type = schema_data.get("@type")

    if not schema_type:
        issues.append(SchemaIssue(
            severity="medium",
            category="schema",
            schema_type="Unknown",
            description="Missing @type property in schema",
            recommendation="Add @type to specify the schema type"
        ))
        return issues

    # Handle array of types
    if isinstance(schema_type, list):
        schema_type = schema_type[0]

    # Check required properties
    required = REQUIRED_PROPERTIES.get(schema_type, [])
    for prop in required:
        if prop not in schema_data:
            issues.append(SchemaIssue(
                severity="high",
                category="required_property",
                schema_type=schema_type,
                property_name=prop,
                description=f"Missing required property '{prop}' for {schema_type}",
                recommendation=f"Add '{prop}' property to {schema_type} schema"
            ))

    # Check recommended properties
    recommended = RECOMMENDED_PROPERTIES.get(schema_type, [])
    for prop in recommended:
        if prop not in schema_data:
            issues.append(SchemaIssue(
                severity="low",
                category="recommended_property",
                schema_type=schema_type,
                property_name=prop,
                description=f"Missing recommended property '{prop}' for {schema_type}",
                recommendation=f"Consider adding '{prop}' for better rich results"
            ))

    # Validate nested schemas
    for key, value in schema_data.items():
        if isinstance(value, dict) and "@type" in value:
            nested_issues = validate_schema(value)
            issues.extend(nested_issues)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and "@type" in item:
                    nested_issues = validate_schema(item)
                    issues.extend(nested_issues)

    return issues


def check_rich_results_eligibility(schemas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check which rich results the schemas are eligible for.

    Args:
        schemas: List of schema objects

    Returns:
        Dict with rich results eligibility
    """
    eligibility = {
        "eligible": [],
        "potential": [],
        "findings": []
    }

    # Rich result types and their requirements
    rich_results = {
        "FAQ": {
            "types": ["FAQPage"],
            "required": ["mainEntity"]
        },
        "How-to": {
            "types": ["HowTo"],
            "required": ["name", "step"]
        },
        "Product": {
            "types": ["Product"],
            "required": ["name"],
            "recommended": ["offers", "aggregateRating", "review"]
        },
        "Article": {
            "types": ["Article", "NewsArticle", "BlogPosting"],
            "required": ["headline", "author", "datePublished"]
        },
        "Local Business": {
            "types": ["LocalBusiness", "Restaurant", "Store"],
            "required": ["name", "address"]
        },
        "Organization": {
            "types": ["Organization", "Corporation"],
            "required": ["name", "url", "logo"]
        },
        "Breadcrumb": {
            "types": ["BreadcrumbList"],
            "required": ["itemListElement"]
        },
        "Event": {
            "types": ["Event"],
            "required": ["name", "startDate", "location"]
        },
        "Review": {
            "types": ["Review", "AggregateRating"],
            "required": ["itemReviewed", "ratingValue"]
        }
    }

    schema_types = set()
    for schema in schemas:
        schema_type = schema.get("@type")
        if isinstance(schema_type, list):
            schema_types.update(schema_type)
        elif schema_type:
            schema_types.add(schema_type)

    for result_name, requirements in rich_results.items():
        matching_types = schema_types.intersection(set(requirements["types"]))

        if matching_types:
            # Check if required properties are present
            has_required = True
            for schema in schemas:
                if schema.get("@type") in matching_types:
                    for req in requirements.get("required", []):
                        if req not in schema:
                            has_required = False
                            break

            if has_required:
                eligibility["eligible"].append(result_name)
                eligibility["findings"].append(f"Eligible for {result_name} rich result")
            else:
                eligibility["potential"].append(result_name)
                eligibility["findings"].append(f"Potential {result_name} - add required properties")

    return eligibility


def validate_structured_data(url: str) -> Dict[str, Any]:
    """
    Complete structured data validation for a URL.

    Args:
        url: URL to validate

    Returns:
        Dict with complete validation results (0-15 score)
    """
    result = {
        "score": 0,
        "max": 15,
        "structured_data": {
            "json_ld": [],
            "microdata": [],
            "rdfa": []
        },
        "schema_types": [],
        "rich_results": {},
        "issues": [],
        "findings": []
    }

    # Fetch page
    html = fetch_page(url)

    if not html:
        result["issues"].append({
            "severity": "high",
            "category": "fetch",
            "description": f"Could not fetch {url}",
            "recommendation": "Verify URL is accessible"
        })
        result["score"] = 0
        return result

    # Extract structured data
    structured = extract_structured_data(html)
    result["structured_data"] = structured

    # Combine all schemas
    all_schemas = []
    all_schemas.extend(structured["json_ld"])
    all_schemas.extend(structured["microdata"])
    all_schemas.extend(structured["rdfa"])

    if not all_schemas:
        result["issues"].append({
            "severity": "medium",
            "category": "structured_data",
            "description": "No structured data found on page",
            "recommendation": "Add JSON-LD structured data for Organization, Product, or other relevant types"
        })
        result["findings"].append("No structured data found")
        result["score"] = 2  # Minimal score
        return result

    # Get schema types
    for schema in all_schemas:
        schema_type = schema.get("@type")
        if schema_type:
            if isinstance(schema_type, list):
                result["schema_types"].extend(schema_type)
            else:
                result["schema_types"].append(schema_type)

    result["schema_types"] = list(set(result["schema_types"]))
    result["findings"].append(f"Found {len(all_schemas)} schema(s): {', '.join(result['schema_types'])}")

    # Validate each schema
    for schema in structured["json_ld"]:
        issues = validate_schema(schema)
        for issue in issues:
            result["issues"].append({
                "severity": issue.severity,
                "category": issue.category,
                "schema_type": issue.schema_type,
                "property": issue.property_name,
                "description": issue.description,
                "recommendation": issue.recommendation
            })

    # Check rich results eligibility
    rich_results = check_rich_results_eligibility(all_schemas)
    result["rich_results"] = rich_results
    result["findings"].extend(rich_results.get("findings", []))

    # Calculate score
    score = 0

    # Base score for having structured data
    if structured["json_ld"]:
        score += 5  # JSON-LD is preferred
    elif structured["microdata"] or structured["rdfa"]:
        score += 3

    # Points for important schema types
    important_types = ["Organization", "LocalBusiness", "Product", "Article", "FAQPage", "HowTo"]
    found_important = [t for t in result["schema_types"] if t in important_types]
    score += min(5, len(found_important) * 2)

    # Points for rich result eligibility
    score += min(5, len(rich_results.get("eligible", [])) * 2)

    # Deduct for issues
    for issue in result["issues"]:
        if issue["severity"] == "high":
            score -= 2
        elif issue["severity"] == "medium":
            score -= 1

    result["score"] = max(0, min(15, score))

    return result


__all__ = [
    'SchemaIssue',
    'REQUIRED_PROPERTIES',
    'RECOMMENDED_PROPERTIES',
    'extract_json_ld',
    'extract_microdata',
    'extract_rdfa',
    'extract_structured_data',
    'validate_schema',
    'check_rich_results_eligibility',
    'validate_structured_data'
]
