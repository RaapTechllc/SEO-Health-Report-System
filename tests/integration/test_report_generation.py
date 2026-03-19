"""
End-to-end tests for report generation.

Tests the complete report generation flow including:
- Markdown report generation
- DOCX report generation (with python-docx if available)
- PDF report generation (with reportlab if available)
"""

import os
import sys
from datetime import datetime

import pytest

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture
def sample_audit_data():
    """Complete sample audit data for report generation."""
    return {
        "url": "https://example.com",
        "company_name": "Example Corp",
        "timestamp": datetime.now().isoformat(),
        "audits": {
            "technical": {
                "score": 78,
                "grade": "C",
                "components": {
                    "crawlability": {
                        "score": 18,
                        "max": 20,
                        "findings": ["Robots.txt accessible", "Sitemap found"],
                        "issues": [],
                    },
                    "speed": {
                        "score": 20,
                        "max": 25,
                        "psi_score": 75,
                        "findings": ["LCP: 2.8s", "CLS: 0.08"],
                        "issues": [
                            {
                                "severity": "medium",
                                "description": "LCP above 2.5s threshold",
                            }
                        ],
                    },
                    "security": {
                        "score": 10,
                        "max": 10,
                        "findings": ["HTTPS enabled", "HSTS present"],
                        "issues": [],
                    },
                    "mobile": {
                        "score": 12,
                        "max": 15,
                        "findings": ["Viewport configured", "Touch targets adequate"],
                        "issues": [],
                    },
                    "structured_data": {
                        "score": 10,
                        "max": 15,
                        "findings": ["Organization schema found"],
                        "issues": [
                            {
                                "severity": "low",
                                "description": "Missing breadcrumb schema",
                            }
                        ],
                    },
                },
                "critical_issues": [],
                "recommendations": [
                    {
                        "priority": "high",
                        "action": "Optimize LCP",
                        "details": "Reduce image sizes",
                        "impact": "high",
                        "effort": "medium",
                    },
                    {
                        "priority": "medium",
                        "action": "Add breadcrumb schema",
                        "details": "Improve navigation clarity",
                        "impact": "medium",
                        "effort": "low",
                    },
                ],
                "findings": [
                    "Technical foundation is solid",
                    "Speed needs minor optimization",
                ],
            },
            "content": {
                "score": 72,
                "grade": "C",
                "components": {
                    "content_quality": {
                        "score": 20,
                        "max": 25,
                        "findings": [
                            "Average word count: 1200",
                            "3 thin content pages",
                        ],
                        "issues": [],
                    },
                    "eeat": {
                        "score": 16,
                        "max": 20,
                        "has_authors": True,
                        "has_about_page": True,
                        "findings": [
                            "Author pages present",
                            "About page comprehensive",
                        ],
                        "issues": [],
                    },
                },
                "content_gaps": [
                    {
                        "topic": "Widget comparison guide",
                        "priority": "high",
                        "recommendation": "Create comprehensive comparison",
                    }
                ],
                "recommendations": [
                    {
                        "priority": "high",
                        "action": "Expand thin content",
                        "details": "3 pages need expansion",
                        "impact": "high",
                        "effort": "medium",
                    }
                ],
                "findings": ["E-E-A-T signals present", "Content depth varies"],
            },
            "ai_visibility": {
                "score": 65,
                "grade": "D",
                "components": {
                    "ai_presence": {
                        "score": 15,
                        "max": 25,
                        "findings": ["Mentioned in 40% of test queries"],
                    },
                    "accuracy": {
                        "score": 18,
                        "max": 20,
                        "findings": ["Founding year accurate", "Product info current"],
                    },
                    "parseability": {
                        "score": 12,
                        "max": 15,
                        "findings": ["Semantic HTML used", "Clean structure"],
                    },
                    "knowledge_graph": {
                        "score": 8,
                        "max": 15,
                        "sources": {
                            "wikidata": {"found": True},
                            "wikipedia": {"found": False},
                        },
                        "findings": ["Present in Wikidata", "No Wikipedia entry"],
                    },
                    "citation_likelihood": {
                        "score": 7,
                        "max": 15,
                        "findings": ["Limited original research"],
                    },
                    "sentiment": {
                        "score": 8,
                        "max": 10,
                        "findings": ["Generally positive mentions"],
                    },
                },
                "ai_responses": [
                    {
                        "query": "What is Example Corp?",
                        "system": "claude",
                        "response": "Example Corp is a widget provider...",
                        "brand_mentioned": True,
                        "sentiment": "positive",
                    }
                ],
                "accuracy_issues": [],
                "recommendations": [
                    {
                        "priority": "high",
                        "action": "Work toward Wikipedia presence",
                        "details": "Build notability",
                        "impact": "high",
                        "effort": "high",
                    },
                    {
                        "priority": "medium",
                        "action": "Create original research",
                        "details": "Publish studies",
                        "impact": "high",
                        "effort": "high",
                    },
                ],
                "findings": ["AI awareness moderate", "Accuracy good when mentioned"],
            },
        },
        "warnings": [],
        "errors": [],
    }


@pytest.fixture
def sample_scores():
    """Sample composite scores."""
    return {
        "overall_score": 72,
        "grade": "C",
        "component_scores": {
            "technical": {"score": 78, "weight": 0.30, "weighted_score": 23.4},
            "content": {"score": 72, "weight": 0.35, "weighted_score": 25.2},
            "ai_visibility": {"score": 65, "weight": 0.35, "weighted_score": 22.75},
        },
    }


@pytest.fixture
def sample_executive_summary():
    """Sample executive summary."""
    return {
        "headline": "SEO Health Needs Attention",
        "score_display": {
            "overall": 72,
            "grade": "C",
            "grade_description": "Average - Room for improvement",
        },
        "component_summary": [
            {
                "name": "Technical Health",
                "score": 78,
                "status": "fair",
                "status_icon": "yellow",
            },
            {
                "name": "Content & Authority",
                "score": 72,
                "status": "fair",
                "status_icon": "yellow",
            },
            {
                "name": "AI Visibility",
                "score": 65,
                "status": "poor",
                "status_icon": "red",
            },
        ],
        "what_this_means": "Example Corp's website has notable SEO gaps that may be limiting search visibility.",
        "top_actions": [
            {"type": "critical", "action": "Optimize LCP below 2.5s", "impact": "high"},
            {
                "type": "quick_win",
                "action": "Expand thin content pages",
                "impact": "high",
            },
        ],
        "key_strengths": ["Technical Health"],
        "key_weaknesses": ["AI Visibility"],
    }


class TestMarkdownReportGeneration:
    """Test Markdown report generation."""

    @pytest.mark.integration
    def test_markdown_report_generates_successfully(
        self, sample_audit_data, sample_scores, sample_executive_summary, tmp_path
    ):
        """Test that markdown report generates without errors."""
        from seo_health_report.scripts.build_report import (
            build_report_document,
        )

        str(tmp_path / "test-report.md")

        result = build_report_document(
            audit_results=sample_audit_data,
            scores=sample_scores,
            executive_summary=sample_executive_summary,
            company_name="Example Corp",
            logo_file=None,
            brand_colors=None,
            output_format="md",
            output_dir=str(tmp_path),
        )

        assert result["success"] is True
        assert result["output_path"] is not None
        assert os.path.exists(result["output_path"])

    @pytest.mark.integration
    def test_markdown_contains_required_sections(
        self, sample_audit_data, sample_scores, sample_executive_summary, tmp_path
    ):
        """Test that markdown report contains all required sections."""
        from seo_health_report.scripts.build_report import build_report_document

        result = build_report_document(
            audit_results=sample_audit_data,
            scores=sample_scores,
            executive_summary=sample_executive_summary,
            company_name="Example Corp",
            output_format="md",
            output_dir=str(tmp_path),
        )

        assert result["success"] is True

        # Read generated file
        with open(result["output_path"], encoding="utf-8") as f:
            content = f.read()

        # Check for required sections
        assert "# SEO Health Report" in content
        assert "Example Corp" in content
        assert "Executive Summary" in content
        assert "Technical Health" in content
        assert "Content & Authority" in content
        assert "AI Visibility" in content
        assert "Action Plan" in content

    @pytest.mark.integration
    def test_markdown_includes_scores(
        self, sample_audit_data, sample_scores, sample_executive_summary, tmp_path
    ):
        """Test that markdown includes scores."""
        from seo_health_report.scripts.build_report import build_report_document

        result = build_report_document(
            audit_results=sample_audit_data,
            scores=sample_scores,
            executive_summary=sample_executive_summary,
            company_name="Example Corp",
            output_format="md",
            output_dir=str(tmp_path),
        )

        with open(result["output_path"], encoding="utf-8") as f:
            content = f.read()

        # Check for scores
        assert "72/100" in content or "Score: 72" in content
        assert "Grade: C" in content or "(C)" in content


class TestDocxReportGeneration:
    """Test DOCX report generation."""

    @pytest.mark.integration
    def test_docx_generation_or_fallback(
        self, sample_audit_data, sample_scores, sample_executive_summary, tmp_path
    ):
        """Test DOCX generation or graceful fallback to markdown."""
        from seo_health_report.scripts.build_report import build_report_document

        result = build_report_document(
            audit_results=sample_audit_data,
            scores=sample_scores,
            executive_summary=sample_executive_summary,
            company_name="Example Corp",
            output_format="docx",
            output_dir=str(tmp_path),
        )

        # Should succeed (either DOCX or fallback to MD)
        assert result["success"] is True
        assert result["output_path"] is not None
        assert os.path.exists(result["output_path"])

    @pytest.mark.integration
    def test_docx_file_created_with_python_docx(
        self, sample_audit_data, sample_scores, sample_executive_summary, tmp_path
    ):
        """Test that actual DOCX is created when python-docx is available."""
        try:
            import docx

            has_docx = True
        except ImportError:
            has_docx = False

        from seo_health_report.scripts.build_report import build_report_document

        result = build_report_document(
            audit_results=sample_audit_data,
            scores=sample_scores,
            executive_summary=sample_executive_summary,
            company_name="Example Corp",
            output_format="docx",
            output_dir=str(tmp_path),
        )

        if has_docx:
            # Should be actual DOCX
            assert result["output_path"].endswith(".docx")
            # Verify it's a valid DOCX
            doc = docx.Document(result["output_path"])
            assert len(doc.paragraphs) > 0
        else:
            # Should fall back to MD
            assert result["output_path"].endswith(".md")


class TestPdfReportGeneration:
    """Test PDF report generation."""

    @pytest.mark.integration
    def test_pdf_generation_or_fallback(
        self, sample_audit_data, sample_scores, sample_executive_summary, tmp_path
    ):
        """Test PDF generation or graceful fallback to markdown."""
        from seo_health_report.scripts.build_report import build_report_document

        result = build_report_document(
            audit_results=sample_audit_data,
            scores=sample_scores,
            executive_summary=sample_executive_summary,
            company_name="Example Corp",
            output_format="pdf",
            output_dir=str(tmp_path),
        )

        # Should succeed (either PDF or fallback to MD)
        assert result["success"] is True
        assert result["output_path"] is not None
        # Either the PDF exists OR the fallback MD exists
        pdf_exists = os.path.exists(result["output_path"])
        md_path = result["output_path"].replace(".pdf", ".md")
        md_exists = os.path.exists(md_path)
        assert pdf_exists or md_exists, (
            f"Neither {result['output_path']} nor {md_path} exists"
        )

    @pytest.mark.integration
    def test_pdf_file_created_with_reportlab(
        self, sample_audit_data, sample_scores, sample_executive_summary, tmp_path
    ):
        """Test that actual PDF is created when reportlab is available."""
        try:
            import reportlab  # noqa: F401

            has_reportlab = True
        except ImportError:
            has_reportlab = False

        from seo_health_report.scripts.build_report import build_report_document

        result = build_report_document(
            audit_results=sample_audit_data,
            scores=sample_scores,
            executive_summary=sample_executive_summary,
            company_name="Example Corp",
            output_format="pdf",
            output_dir=str(tmp_path),
        )

        if has_reportlab:
            # Should be actual PDF
            assert result["output_path"].endswith(".pdf")
            # Verify file has content
            file_size = os.path.getsize(result["output_path"])
            assert file_size > 1000  # PDF should be at least 1KB
        else:
            # Falls back to MD - check either output_path is .md or .md file exists
            md_path = result["output_path"].replace(".pdf", ".md")
            assert os.path.exists(md_path), f"Expected MD fallback at {md_path}"


class TestReportBranding:
    """Test report branding functionality."""

    @pytest.mark.integration
    def test_brand_colors_applied(
        self, sample_audit_data, sample_scores, sample_executive_summary, tmp_path
    ):
        """Test that brand colors are accepted."""
        from seo_health_report.scripts.build_report import build_report_document

        brand_colors = {
            "primary": "#1a73e8",
            "secondary": "#34a853",
        }

        result = build_report_document(
            audit_results=sample_audit_data,
            scores=sample_scores,
            executive_summary=sample_executive_summary,
            company_name="Example Corp",
            brand_colors=brand_colors,
            output_format="md",
            output_dir=str(tmp_path),
        )

        assert result["success"] is True

    @pytest.mark.integration
    def test_company_name_in_filename(
        self, sample_audit_data, sample_scores, sample_executive_summary, tmp_path
    ):
        """Test that company name appears in filename."""
        from seo_health_report.scripts.build_report import build_report_document

        result = build_report_document(
            audit_results=sample_audit_data,
            scores=sample_scores,
            executive_summary=sample_executive_summary,
            company_name="Test Company Inc",
            output_format="md",
            output_dir=str(tmp_path),
        )

        filename = os.path.basename(result["output_path"])
        assert "Test-Company-Inc" in filename


class TestReportSections:
    """Test individual report section generation."""

    @pytest.mark.integration
    def test_technical_section_structure(self):
        """Test technical section has correct structure."""
        from seo_health_report.scripts.build_report import build_technical_section

        data = {
            "score": 75,
            "findings": ["Good crawlability", "Speed needs work"],
            "components": {
                "speed": {
                    "score": 20,
                    "max": 25,
                    "findings": ["LCP 2.8s"],
                    "issues": [],
                },
                "security": {
                    "score": 10,
                    "max": 10,
                    "findings": ["HTTPS OK"],
                    "issues": [],
                },
            },
            "critical_issues": [{"description": "Test issue"}],
            "recommendations": [{"action": "Fix speed"}],
        }

        section = build_technical_section(data)

        assert "overview" in section
        assert "components" in section
        assert "issues" in section
        assert "recommendations" in section
        assert len(section["components"]) == 2

    @pytest.mark.integration
    def test_action_plan_categorizes_correctly(self):
        """Test action plan categorizes items correctly."""
        from seo_health_report.scripts.build_report import build_action_plan

        audit_results = {
            "audits": {
                "technical": {
                    "recommendations": [
                        {
                            "action": "Quick fix",
                            "impact": "high",
                            "effort": "low",
                            "priority": "high",
                        },
                        {
                            "action": "Big project",
                            "impact": "high",
                            "effort": "high",
                            "priority": "high",
                        },
                        {
                            "action": "Nice to have",
                            "impact": "low",
                            "effort": "low",
                            "priority": "low",
                        },
                    ]
                }
            }
        }
        scores = {"overall_score": 70}

        plan = build_action_plan(audit_results, scores)

        # Quick wins should have high/medium impact and low effort
        assert len(plan["quick_wins"]) >= 1
        for win in plan["quick_wins"]:
            assert win["effort"] == "low"
            assert win["impact"] in ["high", "medium"]

        # Strategic initiatives should have high impact and medium/high effort
        assert len(plan["strategic_initiatives"]) >= 1

    @pytest.mark.integration
    def test_page_count_estimation(self):
        """Test page count estimation."""
        from seo_health_report.scripts.build_report import estimate_page_count

        sections = [
            {"type": "cover"},
            {"type": "executive_summary"},
            {"type": "technical"},
            {"type": "content"},
            {"type": "ai_visibility"},
            {"type": "action_plan"},
            {"type": "appendix"},
        ]

        pages = estimate_page_count(sections)

        # Should estimate reasonable page count
        assert pages >= 15  # Minimum expected
        assert pages <= 25  # Maximum reasonable


class TestEdgeCases:
    """Test edge cases in report generation."""

    @pytest.mark.integration
    def test_empty_recommendations_handled(
        self, sample_scores, sample_executive_summary, tmp_path
    ):
        """Test report generates with empty recommendations."""
        from seo_health_report.scripts.build_report import build_report_document

        audit_data = {
            "audits": {
                "technical": {
                    "score": 80,
                    "recommendations": [],
                    "issues": [],
                    "components": {},
                },
                "content": {
                    "score": 75,
                    "recommendations": [],
                    "issues": [],
                    "components": {},
                },
                "ai_visibility": {
                    "score": 70,
                    "recommendations": [],
                    "issues": [],
                    "components": {},
                },
            }
        }

        result = build_report_document(
            audit_results=audit_data,
            scores=sample_scores,
            executive_summary=sample_executive_summary,
            company_name="Test Corp",
            output_format="md",
            output_dir=str(tmp_path),
        )

        assert result["success"] is True

    @pytest.mark.integration
    def test_special_characters_in_company_name(
        self, sample_audit_data, sample_scores, sample_executive_summary, tmp_path
    ):
        """Test company names with special characters."""
        from seo_health_report.scripts.build_report import build_report_document

        result = build_report_document(
            audit_results=sample_audit_data,
            scores=sample_scores,
            executive_summary=sample_executive_summary,
            company_name="Test & Sons / LLC",
            output_format="md",
            output_dir=str(tmp_path),
        )

        assert result["success"] is True
        # Filename should handle special chars
        assert os.path.exists(result["output_path"])

    @pytest.mark.integration
    def test_long_content_truncated_appropriately(self, tmp_path):
        """Test that very long content is handled appropriately."""
        from seo_health_report.scripts.build_report import build_report_document

        # Create audit data with very long findings
        long_finding = "This is a very long finding that goes on and on. " * 50
        audit_data = {
            "audits": {
                "technical": {
                    "score": 80,
                    "findings": [long_finding],
                    "recommendations": [],
                    "components": {},
                },
                "content": {
                    "score": 75,
                    "findings": [],
                    "recommendations": [],
                    "components": {},
                },
                "ai_visibility": {
                    "score": 70,
                    "findings": [],
                    "recommendations": [],
                    "components": {},
                },
            }
        }

        scores = {"overall_score": 75, "grade": "C", "component_scores": {}}
        summary = {
            "headline": "Test",
            "score_display": {"overall": 75, "grade": "C"},
            "what_this_means": "Test",
            "component_summary": [],
            "top_actions": [],
        }

        result = build_report_document(
            audit_results=audit_data,
            scores=scores,
            executive_summary=summary,
            company_name="Test Corp",
            output_format="md",
            output_dir=str(tmp_path),
        )

        assert result["success"] is True
