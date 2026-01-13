"""
End-to-end tests for the full audit pipeline.

These tests verify the complete audit flow from URL input to final report
with mocked external dependencies (HTTP, LLM APIs).
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture
def mock_http_responses():
    """Mock HTTP responses for various URLs."""
    return {
        "https://example.com": """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Example Corp - Leading Widget Provider</title>
            <meta name="description" content="Example Corp provides enterprise widgets and solutions.">
            <link rel="canonical" href="https://example.com/">
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "Example Corp",
                "url": "https://example.com"
            }
            </script>
        </head>
        <body>
            <header>
                <nav>
                    <a href="/">Home</a>
                    <a href="/about">About</a>
                    <a href="/products">Products</a>
                    <a href="/contact">Contact</a>
                </nav>
            </header>
            <main>
                <article>
                    <h1>Welcome to Example Corp</h1>
                    <p>We are the leading provider of enterprise widgets and solutions.
                    Our team of experts has been serving customers since 2010.</p>
                    <section>
                        <h2>Our Products</h2>
                        <p>We offer a wide range of widgets including premium widgets,
                        basic widgets, and custom solutions for enterprise clients.</p>
                    </section>
                    <section>
                        <h2>Why Choose Us</h2>
                        <p>With over 10 years of experience and a dedicated support team,
                        we provide unmatched quality and service in the widget industry.</p>
                    </section>
                </article>
            </main>
            <footer>
                <p>Copyright 2024 Example Corp. All rights reserved.</p>
            </footer>
        </body>
        </html>
        """,
        "https://example.com/about": """
        <!DOCTYPE html>
        <html><head><title>About Us - Example Corp</title></head>
        <body>
            <h1>About Example Corp</h1>
            <p>Founded in 2010, Example Corp is a leading provider of widgets.</p>
            <h2>Our Team</h2>
            <p>Our expert team brings decades of combined experience.</p>
        </body>
        </html>
        """,
        "https://example.com/robots.txt": """
        User-agent: *
        Allow: /
        Sitemap: https://example.com/sitemap.xml
        """,
        "https://example.com/sitemap.xml": """
        <?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/</loc></url>
            <url><loc>https://example.com/about</loc></url>
            <url><loc>https://example.com/products</loc></url>
        </urlset>
        """,
    }


@pytest.fixture
def mock_pagespeed_response():
    """Mock PageSpeed Insights API response."""
    return {
        "lighthouseResult": {
            "categories": {"performance": {"score": 0.85}},
            "audits": {
                "largest-contentful-paint": {"numericValue": 2200},
                "first-input-delay": {"numericValue": 50},
                "cumulative-layout-shift": {"numericValue": 0.05},
                "first-contentful-paint": {"numericValue": 1500},
                "speed-index": {"numericValue": 3000},
                "time-to-interactive": {"numericValue": 4000},
            },
        }
    }


@pytest.fixture
def mock_ai_response():
    """Mock AI system response."""
    return MagicMock(
        response="Example Corp is a well-known widget provider founded in 2010. They offer premium widgets for enterprise customers.",
        brand_mentioned=True,
        position=1,
        sentiment="positive",
        error=None,
        query="What is Example Corp?",
        system="claude",
    )


class TestFullAuditPipeline:
    """Test the complete audit pipeline end-to-end."""

    @pytest.mark.integration
    def test_audit_returns_required_structure(self, mock_http_responses):
        """Test that full audit returns all required fields."""
        # Import here to use mocks
        from tests.conftest import seo_health_report_module
        from seo_health_report.scripts.orchestrate import (
            handle_audit_failure,
            collect_all_issues,
            collect_all_recommendations,
        )

        # Create mock audit results
        audit_results = {
            "url": "https://example.com",
            "company_name": "Example Corp",
            "timestamp": "2024-01-15T10:00:00",
            "audits": {
                "technical": {
                    "score": 75,
                    "grade": "C",
                    "components": {
                        "crawlability": {"score": 18, "max": 20, "issues": []},
                        "speed": {"score": 20, "max": 25, "issues": []},
                    },
                    "issues": [],
                    "recommendations": [
                        {
                            "priority": "high",
                            "action": "Fix speed issues",
                            "impact": "high",
                            "effort": "medium",
                        }
                    ],
                },
                "content": {
                    "score": 70,
                    "grade": "C",
                    "components": {},
                    "issues": [],
                    "recommendations": [],
                },
                "ai_visibility": {
                    "score": 65,
                    "grade": "D",
                    "components": {},
                    "issues": [],
                    "recommendations": [],
                },
            },
            "warnings": [],
            "errors": [],
        }

        # Test collect functions
        issues = collect_all_issues(audit_results)
        assert isinstance(issues, list)

        recs = collect_all_recommendations(audit_results)
        assert isinstance(recs, list)
        assert len(recs) >= 1

    @pytest.mark.integration
    def test_score_calculation_integration(self):
        """Test score calculation with audit results."""
        from seo_health_report.scripts.calculate_scores import (
            calculate_composite_score,
            determine_grade,
        )

        audit_results = {
            "audits": {
                "technical": {"score": 80},
                "content": {"score": 75},
                "ai_visibility": {"score": 70},
            }
        }

        scores = calculate_composite_score(audit_results)

        assert "overall_score" in scores
        assert "grade" in scores
        assert "component_scores" in scores
        assert 0 <= scores["overall_score"] <= 100
        assert scores["grade"] in ["A", "B", "C", "D", "F"]

    @pytest.mark.integration
    def test_executive_summary_generation(self):
        """Test executive summary generation."""
        from seo_health_report.scripts.generate_summary import (
            generate_executive_summary,
            generate_headline,
            format_component_name,
        )

        scores = {
            "overall_score": 75,
            "grade": "C",
            "component_scores": {
                "technical": {"score": 80, "weight": 0.30},
                "content": {"score": 75, "weight": 0.35},
                "ai_visibility": {"score": 70, "weight": 0.35},
            },
        }

        critical_issues = [{"description": "Missing HTTPS", "severity": "critical"}]

        quick_wins = [
            {"action": "Add meta descriptions", "impact": "medium", "effort": "low"}
        ]

        summary = generate_executive_summary(
            scores=scores,
            critical_issues=critical_issues,
            quick_wins=quick_wins,
            company_name="Example Corp",
        )

        assert "headline" in summary
        assert "score_display" in summary
        assert "what_this_means" in summary
        assert "component_summary" in summary
        assert "top_actions" in summary

        # Test headline generation
        assert generate_headline(75, "C") == "SEO Health Needs Attention"
        assert generate_headline(92, "A") == "Excellent SEO Health"

        # Test component name formatting
        assert format_component_name("ai_visibility") == "AI Visibility"
        assert format_component_name("technical") == "Technical Health"


class TestAuditComponentIntegration:
    """Test integration between audit components."""

    @pytest.mark.integration
    def test_placeholder_results_work_in_pipeline(self):
        """Test that placeholder results don't break the pipeline."""
        from seo_health_report.scripts.orchestrate import handle_audit_failure
        from seo_health_report.scripts.calculate_scores import calculate_composite_score

        # Simulate one audit failing with placeholder
        audit_results = {
            "audits": {
                "technical": handle_audit_failure("technical", "Test error"),
                "content": {"score": 75},
                "ai_visibility": {"score": 70},
            }
        }

        # Should not raise - technical has None score so only content/ai used
        scores = calculate_composite_score(audit_results)
        assert scores["overall_score"] >= 0

    @pytest.mark.integration
    def test_issues_collection_across_audits(self):
        """Test issue collection from all audit components."""
        from seo_health_report.scripts.orchestrate import (
            collect_all_issues,
            identify_critical_issues,
        )

        audit_results = {
            "audits": {
                "technical": {
                    "issues": [
                        {"severity": "critical", "description": "No HTTPS"},
                        {"severity": "medium", "description": "Slow pages"},
                    ],
                    "components": {
                        "security": {
                            "issues": [
                                {"severity": "high", "description": "Missing headers"}
                            ]
                        }
                    },
                },
                "content": {
                    "issues": [
                        {"severity": "high", "description": "Thin content"},
                    ]
                },
                "ai_visibility": {"issues": []},
            }
        }

        all_issues = collect_all_issues(audit_results)
        assert len(all_issues) == 4

        critical = identify_critical_issues(all_issues)
        assert len(critical) >= 2  # critical + high severity

    @pytest.mark.integration
    def test_recommendations_prioritization(self):
        """Test that recommendations are properly prioritized."""
        from seo_health_report.scripts.orchestrate import (
            collect_all_recommendations,
            identify_quick_wins,
        )

        audit_results = {
            "audits": {
                "technical": {
                    "recommendations": [
                        {
                            "priority": "high",
                            "action": "Fix HTTPS",
                            "impact": "high",
                            "effort": "medium",
                        },
                        {
                            "priority": "low",
                            "action": "Add schema",
                            "impact": "medium",
                            "effort": "low",
                        },
                    ]
                },
                "content": {
                    "recommendations": [
                        {
                            "priority": "medium",
                            "action": "Expand content",
                            "impact": "high",
                            "effort": "low",
                        },
                    ]
                },
                "ai_visibility": {"recommendations": []},
            }
        }

        all_recs = collect_all_recommendations(audit_results)
        assert len(all_recs) == 3

        # Verify sorting by priority
        priorities = [r.get("priority") for r in all_recs]
        expected_order = ["high", "medium", "low"]
        assert priorities == expected_order

        # Test quick wins (high/medium impact, low effort)
        quick_wins = identify_quick_wins(all_recs)
        assert len(quick_wins) == 2  # schema and expand content


class TestDataFlow:
    """Test data flow through the pipeline."""

    @pytest.mark.integration
    def test_audit_data_flows_to_report(self):
        """Test that audit data properly flows to report building."""
        from seo_health_report.scripts.build_report import (
            build_technical_section,
            build_content_section,
            build_ai_visibility_section,
            build_action_plan,
        )

        # Mock audit data
        technical_data = {
            "score": 75,
            "findings": ["Good crawlability", "Speed needs work"],
            "components": {
                "speed": {"score": 15, "max": 25, "findings": ["LCP too high"]},
                "security": {"score": 10, "max": 10, "findings": ["HTTPS enabled"]},
            },
            "critical_issues": [{"description": "Missing CSP header"}],
            "recommendations": [{"action": "Add CSP header", "priority": "high"}],
        }

        section = build_technical_section(technical_data)
        assert "overview" in section
        assert "components" in section
        assert len(section["components"]) == 2

        # Test action plan building
        audit_results = {
            "audits": {
                "technical": {
                    "recommendations": [
                        {"action": "Fix speed", "impact": "high", "effort": "low"},
                        {"action": "Add headers", "impact": "medium", "effort": "high"},
                    ]
                }
            }
        }
        scores = {"overall_score": 75, "grade": "C"}

        plan = build_action_plan(audit_results, scores)
        assert "quick_wins" in plan
        assert "strategic_initiatives" in plan
        assert "prioritized_tasks" in plan
        assert len(plan["quick_wins"]) == 1  # high impact, low effort

    @pytest.mark.integration
    def test_empty_audit_data_handled_gracefully(self):
        """Test that empty audit data doesn't break report building."""
        from seo_health_report.scripts.build_report import (
            build_technical_section,
            build_content_section,
            build_ai_visibility_section,
        )

        # Empty data
        section = build_technical_section({})
        assert "overview" in section
        assert "Technical audit data not available." in section["overview"]

        section = build_content_section(None)
        assert "Content audit data not available." in section["overview"]

        section = build_ai_visibility_section({})
        assert "AI visibility audit data not available." in section["overview"]


class TestErrorHandling:
    """Test error handling in the pipeline."""

    @pytest.mark.integration
    def test_missing_audit_handled(self):
        """Test that missing audits are handled gracefully."""
        from seo_health_report.scripts.calculate_scores import calculate_composite_score

        # Only one audit present
        audit_results = {
            "audits": {
                "technical": {"score": 80},
                # content and ai_visibility missing
            }
        }

        scores = calculate_composite_score(audit_results)
        # Should use defaults for missing
        assert scores["overall_score"] >= 0

    @pytest.mark.integration
    def test_none_values_handled(self):
        """Test that None values don't crash the pipeline."""
        from seo_health_report.scripts.orchestrate import (
            collect_all_issues,
            collect_all_recommendations,
        )

        audit_results = {
            "audits": {
                "technical": None,
                "content": {
                    "issues": None,
                    "recommendations": [{"action": "Test"}],
                },
                "ai_visibility": {
                    "issues": [],
                    "recommendations": None,
                },
            }
        }

        # Should not raise
        issues = collect_all_issues(audit_results)
        assert isinstance(issues, list)

        recs = collect_all_recommendations(audit_results)
        assert isinstance(recs, list)
