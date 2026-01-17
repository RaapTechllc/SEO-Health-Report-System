"""
Check Form Optimization

Analyze contact forms for field count, mobile-friendliness, and usability.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class FormField:
    """A form field found during analysis."""
    name: str
    type: str
    required: bool
    label: Optional[str]


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


def extract_forms(html: str) -> List[Dict[str, Any]]:
    """
    Extract all forms from HTML content.

    Args:
        html: HTML content

    Returns:
        List of form data dicts
    """
    forms = []

    # Find all form elements
    form_pattern = r'<form[^>]*>(.*?)</form>'
    form_matches = re.findall(form_pattern, html, re.IGNORECASE | re.DOTALL)

    for form_html in form_matches:
        form = {
            "fields": [],
            "has_submit": False,
            "field_count": 0,
        }

        # Find input fields
        input_pattern = r'<input[^>]*type=["\']([^"\']*)["\'][^>]*(?:name=["\']([^"\']*)["\'])?[^>]*>'
        input_matches = re.findall(input_pattern, form_html, re.IGNORECASE)

        for input_type, input_name in input_matches:
            input_type = input_type.lower()

            if input_type == 'submit':
                form["has_submit"] = True
                continue

            if input_type in ['hidden', 'button']:
                continue

            # Check if required
            required = 'required' in form_html.lower()

            form["fields"].append(FormField(
                name=input_name or f"unnamed_{input_type}",
                type=input_type,
                required=required,
                label=None
            ))

        # Find textarea fields
        textarea_pattern = r'<textarea[^>]*(?:name=["\']([^"\']*)["\'])?'
        textarea_matches = re.findall(textarea_pattern, form_html, re.IGNORECASE)
        for name in textarea_matches:
            form["fields"].append(FormField(
                name=name or "message",
                type="textarea",
                required=False,
                label=None
            ))

        # Find select fields
        select_pattern = r'<select[^>]*(?:name=["\']([^"\']*)["\'])?'
        select_matches = re.findall(select_pattern, form_html, re.IGNORECASE)
        for name in select_matches:
            form["fields"].append(FormField(
                name=name or "select",
                type="select",
                required=False,
                label=None
            ))

        form["field_count"] = len(form["fields"])
        forms.append(form)

    return forms


def check_form_field_count(forms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check form field counts for optimization.

    Args:
        forms: List of form data dicts

    Returns:
        Dict with field count analysis
    """
    result = {
        "forms_found": len(forms),
        "form_fields_count": 0,
        "optimal_field_count": True,
        "score": 0,
        "max": 2,
        "issues": [],
        "findings": [],
    }

    if not forms:
        result["issues"].append({
            "severity": "medium",
            "description": "No contact forms found on page",
            "recommendation": "Add a simple contact form with 3-5 fields",
            "impact_estimate": ""
        })
        return result

    # Find the main contact form (usually the one with most fields)
    main_form = max(forms, key=lambda f: f["field_count"])
    result["form_fields_count"] = main_form["field_count"]

    # Score based on field count
    # Optimal: 3-5 fields
    # Acceptable: 6-7 fields
    # Too many: 8+ fields

    if main_form["field_count"] <= 5:
        result["score"] = 2
        result["optimal_field_count"] = True
        result["findings"].append(f"Form has optimal field count ({main_form['field_count']} fields)")
    elif main_form["field_count"] <= 7:
        result["score"] = 1
        result["optimal_field_count"] = True
        result["findings"].append(f"Form has acceptable field count ({main_form['field_count']} fields)")
    else:
        result["score"] = 0
        result["optimal_field_count"] = False
        result["issues"].append({
            "severity": "high",
            "description": f"Form has too many fields ({main_form['field_count']} fields)",
            "recommendation": "Reduce form to 3-5 essential fields. Each additional field reduces conversions by ~4%",
            "impact_estimate": f"Reducing from {main_form['field_count']} to 5 fields could improve conversions by {(main_form['field_count'] - 5) * 4}%"
        })

    return result


def check_form_mobile_friendly(html: str) -> Dict[str, Any]:
    """
    Check form mobile-friendliness.

    Args:
        html: HTML content

    Returns:
        Dict with mobile-friendliness analysis
    """
    result = {
        "form_mobile_friendly": True,
        "has_input_types": True,
        "has_autocomplete": False,
        "score": 0,
        "max": 2,
        "issues": [],
        "findings": [],
    }

    # Check for proper input types (helps mobile keyboards)
    proper_types = {
        'email': r'type=["\']email["\']',
        'tel': r'type=["\']tel["\']',
        'number': r'type=["\']number["\']',
    }

    types_found = []
    for type_name, pattern in proper_types.items():
        if re.search(pattern, html, re.IGNORECASE):
            types_found.append(type_name)

    if types_found:
        result["has_input_types"] = True
        result["score"] += 1
        result["findings"].append(f"Proper input types used: {', '.join(types_found)}")
    else:
        result["has_input_types"] = False
        result["issues"].append({
            "severity": "low",
            "description": "Form doesn't use proper HTML5 input types",
            "recommendation": "Use type='email' for email, type='tel' for phone to show proper mobile keyboards",
            "impact_estimate": ""
        })

    # Check for autocomplete attributes
    if 'autocomplete' in html.lower():
        result["has_autocomplete"] = True
        result["score"] += 1
        result["findings"].append("Form uses autocomplete attributes")
    else:
        result["issues"].append({
            "severity": "low",
            "description": "Form doesn't use autocomplete attributes",
            "recommendation": "Add autocomplete='name', autocomplete='email', etc. for faster mobile form filling",
            "impact_estimate": ""
        })

    result["form_mobile_friendly"] = result["score"] >= 1

    return result


def check_form_validation(html: str) -> Dict[str, Any]:
    """
    Check form validation and error handling indicators.

    Args:
        html: HTML content

    Returns:
        Dict with validation analysis
    """
    result = {
        "has_client_validation": False,
        "has_required_fields": False,
        "has_error_messages": False,
        "score": 0,
        "max": 1,
        "issues": [],
        "findings": [],
    }

    html_lower = html.lower()

    # Check for required attribute
    if 'required' in html_lower:
        result["has_required_fields"] = True
        result["findings"].append("Form uses required field validation")

    # Check for pattern attribute (regex validation)
    if 'pattern=' in html_lower:
        result["has_client_validation"] = True
        result["findings"].append("Form uses pattern validation")

    # Check for error message elements
    error_patterns = [
        r'class=["\'][^"\']*error[^"\']*["\']',
        r'class=["\'][^"\']*invalid[^"\']*["\']',
        r'aria-invalid',
    ]
    for pattern in error_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            result["has_error_messages"] = True
            result["findings"].append("Form has error handling")
            break

    if result["has_required_fields"] or result["has_client_validation"]:
        result["score"] = 1

    return result


def analyze_form_optimization(url: str) -> Dict[str, Any]:
    """
    Complete form optimization analysis for a website.

    Args:
        url: Website URL to analyze

    Returns:
        Dict with complete form analysis (0-5 score)
    """
    result = {
        "score": 0,
        "max": 5,
        "form_fields_count": 0,
        "form_mobile_friendly": False,
        "forms_found": 0,
        "field_count": {},
        "mobile_friendly": {},
        "validation": {},
        "issues": [],
        "findings": [],
        "quick_wins": [],
    }

    # Fetch homepage
    html = fetch_page(url)
    if not html:
        result["issues"].append({
            "severity": "high",
            "description": "Could not fetch homepage for form analysis",
            "recommendation": "Ensure site is accessible",
            "impact_estimate": ""
        })
        return result

    # Also try common contact page URLs
    contact_urls = ["/contact", "/contact-us", "/get-a-quote"]
    for path in contact_urls:
        try:
            contact_html = fetch_page(url.rstrip('/') + path)
            if contact_html:
                html += contact_html
        except Exception:
            pass

    # Extract forms
    forms = extract_forms(html)
    result["forms_found"] = len(forms)

    # Check field count
    result["field_count"] = check_form_field_count(forms)
    result["form_fields_count"] = result["field_count"]["form_fields_count"]
    result["score"] += result["field_count"]["score"]
    result["issues"].extend(result["field_count"].get("issues", []))
    result["findings"].extend(result["field_count"].get("findings", []))

    # Check mobile-friendliness
    result["mobile_friendly"] = check_form_mobile_friendly(html)
    result["form_mobile_friendly"] = result["mobile_friendly"]["form_mobile_friendly"]
    result["score"] += result["mobile_friendly"]["score"]
    result["issues"].extend(result["mobile_friendly"].get("issues", []))
    result["findings"].extend(result["mobile_friendly"].get("findings", []))

    # Check validation
    result["validation"] = check_form_validation(html)
    result["score"] += result["validation"]["score"]
    result["issues"].extend(result["validation"].get("issues", []))
    result["findings"].extend(result["validation"].get("findings", []))

    # Generate quick wins
    if result["form_fields_count"] > 5:
        result["quick_wins"].append({
            "title": "Reduce form fields",
            "description": f"Your form has {result['form_fields_count']} fields. Reducing to 3-5 essential fields can significantly improve conversions.",
            "effort": "medium",
            "impact": "high",
            "implementation": "Keep only: Name, Email/Phone, and Message. Move other fields to follow-up.",
        })

    if not result["mobile_friendly"]["has_input_types"]:
        result["quick_wins"].append({
            "title": "Add proper input types",
            "description": "Help mobile users by using type='email' and type='tel' for proper keyboard display.",
            "effort": "low",
            "impact": "medium",
            "implementation": "Add type='email' to email fields, type='tel' to phone fields",
        })

    return result


__all__ = [
    'FormField',
    'extract_forms',
    'check_form_field_count',
    'check_form_mobile_friendly',
    'check_form_validation',
    'analyze_form_optimization',
]
