"""
Tests for orchestrate module.
"""

import pytest
from seo_health_report.scripts.orchestrate import (
    handle_audit_failure,
    extract_domain,
    collect_all_issues,
    collect_all_recommendations,
    identify_quick_wins,
    identify_critical_issues,
)


class TestHandleAuditFailure:
    """Test audit failure handling."""

    def test_failure_result_structure(self):
        """Test failure result has correct structure."""
        result = handle_audit_failure("technical", "Test error")
        assert "score" in result
        assert "grade" in result
        assert "components" in result
        assert "issues" in result
        assert "findings" in result
        assert "recommendations" in result
        assert "status" in result

    def test_failure_score_none(self):
        """Test failure result has None score."""
        result = handle_audit_failure("technical", "Test error")
        assert result["score"] is None

    def test_failure_grade_na(self):
        """Test failure result has N/A grade."""
        result = handle_audit_failure("content", "Test error")
        assert result["grade"] == "N/A"

    def test_failure_empty_components(self):
        """Test failure result has empty components."""
        result = handle_audit_failure("ai_visibility", "Test error")
        assert result["components"] == {}

    def test_failure_empty_issues(self):
        """Test failure result has empty issues."""
        result = handle_audit_failure("technical", "Test error")
        assert result["issues"] == []

    def test_failure_has_findings(self):
        """Test failure result has findings."""
        result = handle_audit_failure("content", "Test error")
        assert len(result["findings"]) > 0
        assert any("could not be completed" in f for f in result["findings"])

    def test_failure_has_recommendations(self):
        """Test failure result has recommendations."""
        result = handle_audit_failure("ai_visibility", "Test error")
        assert len(result["recommendations"]) > 0

    def test_failure_status_unavailable(self):
        """Test failure is marked as unavailable."""
        result = handle_audit_failure("technical", "Test error")
        assert result["status"] == "unavailable"


class TestExtractDomain:
    """Test domain extraction from URLs."""

    def test_extract_domain_simple(self):
        """Test extracting domain from simple URL."""
        domain = extract_domain("https://example.com/path")
        assert domain == "example.com"

    def test_extract_domain_with_www(self):
        """Test extracting domain removes www prefix."""
        domain = extract_domain("https://www.example.com/path")
        assert domain == "example.com"

    def test_extract_domain_http(self):
        """Test extracting domain from http URL."""
        domain = extract_domain("http://test.org/page")
        assert domain == "test.org"

    def test_extract_domain_with_subdomain(self):
        """Test extracting domain with subdomain."""
        domain = extract_domain("https://blog.example.com/article")
        assert domain == "blog.example.com"

    def test_extract_domain_with_port(self):
        """Test extracting domain with port."""
        domain = extract_domain("https://example.com:8080/path")
        assert domain == "example.com"

    def test_extract_domain_no_path(self):
        """Test extracting domain with no path."""
        domain = extract_domain("https://example.com")
        assert domain == "example.com"

    def test_extract_domain_with_query(self):
        """Test extracting domain with query parameters."""
        domain = extract_domain("https://example.com?param=value")
        assert domain == "example.com"

    def test_extract_domain_with_fragment(self):
        """Test extracting domain with fragment."""
        domain = extract_domain("https://example.com#section")
        assert domain == "example.com"


class TestCollectAllIssues:
    """Test collecting issues from all audits."""

    def test_collect_from_empty_audits(self):
        """Test collecting issues from empty audits."""
        audit_results = {"audits": {}}
        issues = collect_all_issues(audit_results)
        assert issues == []

    def test_collect_from_none_audits(self):
        """Test collecting issues from None audits."""
        audit_results = {"audits": None}
        issues = collect_all_issues(audit_results)
        assert issues == []

    def test_collect_main_issues(self, sample_issues):
        """Test collecting main issues from audits."""
        audit_results = {
            "audits": {"technical": {"score": 85, "issues": [sample_issues[0]]}}
        }
        issues = collect_all_issues(audit_results)
        assert len(issues) == 1
        assert issues[0]["source"] == "technical"

    def test_collect_component_issues(self):
        """Test collecting issues from components."""
        audit_results = {
            "audits": {
                "technical": {
                    "score": 85,
                    "components": {
                        "speed": {
                            "issues": [
                                {"severity": "high", "description": "Slow load time"}
                            ]
                        }
                    },
                }
            }
        }
        issues = collect_all_issues(audit_results)
        assert len(issues) == 1
        assert issues[0]["source"] == "technical/speed"

    def test_collect_multiple_audits(self):
        """Test collecting issues from multiple audits."""
        audit_results = {
            "audits": {
                "technical": {
                    "issues": [{"severity": "high", "description": "Issue 1"}]
                },
                "content": {
                    "issues": [{"severity": "medium", "description": "Issue 2"}]
                },
            }
        }
        issues = collect_all_issues(audit_results)
        assert len(issues) == 2

    def test_collect_issues_deduplication(self):
        """Test issues are collected from all sources."""
        audit_results = {
            "audits": {
                "technical": {
                    "issues": [
                        {"severity": "critical", "description": "Duplicate issue"}
                    ]
                },
                "content": {
                    "issues": [
                        {"severity": "critical", "description": "Duplicate issue"}
                    ]
                },
            }
        }
        issues = collect_all_issues(audit_results)
        # Should not deduplicate - each source has its own copy
        assert len(issues) == 2

    def test_sort_issues_by_severity(self):
        """Test issues are sorted by severity."""
        audit_results = {
            "audits": {
                "technical": {
                    "issues": [
                        {"severity": "low", "description": "Low"},
                        {"severity": "critical", "description": "Critical"},
                        {"severity": "high", "description": "High"},
                        {"severity": "medium", "description": "Medium"},
                    ]
                }
            }
        }
        issues = collect_all_issues(audit_results)
        assert issues[0]["severity"] == "critical"
        assert issues[1]["severity"] == "high"
        assert issues[2]["severity"] == "medium"
        assert issues[3]["severity"] == "low"

    def test_issues_without_source_field(self):
        """Test issues without severity field are handled."""
        audit_results = {
            "audits": {
                "technical": {"issues": [{"description": "Issue without severity"}]}
            }
        }
        issues = collect_all_issues(audit_results)
        assert len(issues) == 1


class TestCollectAllRecommendations:
    """Test collecting recommendations from all audits."""

    def test_collect_from_empty_audits(self):
        """Test collecting recommendations from empty audits."""
        audit_results = {"audits": {}}
        recommendations = collect_all_recommendations(audit_results)
        assert recommendations == []

    def test_collect_recommendations(self):
        """Test collecting recommendations."""
        audit_results = {
            "audits": {
                "technical": {
                    "recommendations": [
                        {"priority": "high", "action": "Fix robots.txt"}
                    ]
                },
                "content": {
                    "recommendations": [{"priority": "medium", "action": "Add content"}]
                },
            }
        }
        recommendations = collect_all_recommendations(audit_results)
        assert len(recommendations) == 2

    def test_recommendations_have_source(self):
        """Test recommendations include source."""
        audit_results = {
            "audits": {
                "technical": {
                    "recommendations": [{"priority": "high", "action": "Action"}]
                }
            }
        }
        recommendations = collect_all_recommendations(audit_results)
        assert recommendations[0]["source"] == "technical"

    def test_sort_recommendations_by_priority(self):
        """Test recommendations sorted by priority."""
        audit_results = {
            "audits": {
                "technical": {
                    "recommendations": [
                        {"priority": "low", "action": "Low"},
                        {"priority": "high", "action": "High"},
                        {"priority": "medium", "action": "Medium"},
                    ]
                }
            }
        }
        recommendations = collect_all_recommendations(audit_results)
        assert recommendations[0]["priority"] == "high"
        assert recommendations[1]["priority"] == "medium"
        assert recommendations[2]["priority"] == "low"


class TestIdentifyQuickWins:
    """Test identifying quick wins."""

    def test_quick_wins_high_impact_low_effort(self, sample_recommendations):
        """Test quick wins have high impact and low effort."""
        quick_wins = identify_quick_wins(sample_recommendations)
        for win in quick_wins:
            assert win["impact"] in ["high", "medium"]
            assert win["effort"] == "low"

    def test_quick_wins_limit_to_10(self):
        """Test quick wins limited to top 10."""
        recommendations = [
            {
                "priority": "high",
                "impact": "high",
                "effort": "low",
                "action": f"Action {i}",
            }
            for i in range(15)
        ]
        quick_wins = identify_quick_wins(recommendations)
        assert len(quick_wins) <= 10

    def test_quick_wins_empty_list(self):
        """Test quick wins from empty recommendations."""
        quick_wins = identify_quick_wins([])
        assert quick_wins == []

    def test_quick_wins_filters_high_effort(self):
        """Test quick wins exclude high effort items."""
        recommendations = [
            {"impact": "high", "effort": "high", "action": "High effort"},
            {"impact": "high", "effort": "low", "action": "Low effort"},
        ]
        quick_wins = identify_quick_wins(recommendations)
        assert len(quick_wins) == 1
        assert quick_wins[0]["effort"] == "low"

    def test_quick_wins_filters_low_impact(self):
        """Test quick wins exclude low impact items."""
        recommendations = [
            {"impact": "low", "effort": "low", "action": "Low impact"},
            {"impact": "high", "effort": "low", "action": "High impact"},
        ]
        quick_wins = identify_quick_wins(recommendations)
        assert len(quick_wins) == 1
        assert quick_wins[0]["impact"] == "high"


class TestIdentifyCriticalIssues:
    """Test identifying critical issues."""

    def test_critical_issues_severity(self, sample_issues):
        """Test critical issues have critical or high severity."""
        critical = identify_critical_issues(sample_issues)
        for issue in critical:
            assert issue["severity"] in ["critical", "high"]

    def test_critical_issues_limit_to_10(self):
        """Test critical issues limited to top 10."""
        issues = [
            {"severity": "critical", "description": f"Critical {i}"} for i in range(15)
        ]
        critical = identify_critical_issues(issues)
        assert len(critical) <= 10

    def test_critical_issues_empty_list(self):
        """Test critical issues from empty list."""
        critical = identify_critical_issues([])
        assert critical == []

    def test_critical_filters_medium(self, sample_issues):
        """Test critical issues filter medium severity."""
        critical = identify_critical_issues(sample_issues)
        assert not any(i["severity"] == "medium" for i in critical)

    def test_critical_filters_low(self, sample_issues):
        """Test critical issues filter low severity."""
        critical = identify_critical_issues(sample_issues)
        assert not any(i["severity"] == "low" for i in critical)

    def test_critical_issues_includes_critical(self):
        """Test critical issues include critical severity."""
        issues = [
            {"severity": "critical", "description": "Critical issue"},
            {"severity": "high", "description": "High issue"},
            {"severity": "medium", "description": "Medium issue"},
        ]
        critical = identify_critical_issues(issues)
        assert any(i["severity"] == "critical" for i in critical)

    def test_critical_issues_includes_high(self):
        """Test critical issues include high severity."""
        issues = [
            {"severity": "critical", "description": "Critical issue"},
            {"severity": "high", "description": "High issue"},
            {"severity": "medium", "description": "Medium issue"},
        ]
        critical = identify_critical_issues(issues)
        assert any(i["severity"] == "high" for i in critical)
