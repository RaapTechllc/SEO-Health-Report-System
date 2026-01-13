"""
Integration tests for data contracts (schemas).
"""

import pytest
import sys
import os

# Setup module path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from seo_health_report.scripts.schemas import (
    Severity,
    Priority,
    Grade,
    AuditStatus,
    Issue,
    Recommendation,
    ComponentScore,
    AuditResult,
    FullAuditResult,
    calculate_grade,
    calculate_composite_score,
)


class TestSchemaContracts:
    """Test data contract serialization."""

    def test_issue_to_dict(self):
        """Test Issue serializes correctly."""
        issue = Issue(
            description="Missing meta description",
            severity=Severity.HIGH,
            source="technical",
        )
        d = issue.to_dict()
        assert d["description"] == "Missing meta description"
        assert d["severity"] == "high"
        assert d["source"] == "technical"

    def test_recommendation_to_dict(self):
        """Test Recommendation serializes correctly."""
        rec = Recommendation(
            action="Add meta descriptions",
            priority=Priority.HIGH,
            impact="high",
            effort="low",
        )
        d = rec.to_dict()
        assert d["action"] == "Add meta descriptions"
        assert d["priority"] == "high"
        assert d["effort"] == "low"

    def test_audit_result_to_dict(self):
        """Test AuditResult serializes correctly."""
        result = AuditResult(
            audit_type="technical",
            score=85,
            grade=Grade.B,
            status=AuditStatus.COMPLETED,
        )
        d = result.to_dict()
        assert d["audit_type"] == "technical"
        assert d["score"] == 85
        assert d["grade"] == "B"
        assert d["status"] == "completed"


class TestGradeCalculation:
    """Test grade calculation logic."""

    def test_grade_a(self):
        assert calculate_grade(95) == Grade.A
        assert calculate_grade(90) == Grade.A

    def test_grade_b(self):
        assert calculate_grade(85) == Grade.B
        assert calculate_grade(80) == Grade.B

    def test_grade_c(self):
        assert calculate_grade(75) == Grade.C
        assert calculate_grade(70) == Grade.C

    def test_grade_d(self):
        assert calculate_grade(65) == Grade.D
        assert calculate_grade(60) == Grade.D

    def test_grade_f(self):
        assert calculate_grade(55) == Grade.F
        assert calculate_grade(0) == Grade.F

    def test_grade_none(self):
        assert calculate_grade(None) == Grade.NA


class TestCompositeScore:
    """Test composite score calculation."""

    def test_all_scores_present(self):
        """Test with all three scores."""
        score = calculate_composite_score(80, 90, 70)
        # (80*0.30) + (90*0.35) + (70*0.35) = 24 + 31.5 + 24.5 = 80
        assert score == 80

    def test_missing_technical(self):
        """Test with missing technical score."""
        score = calculate_composite_score(None, 90, 70)
        # Normalized: (90*0.35 + 70*0.35) / 0.70 = 56/0.70 = 80
        assert score == 80

    def test_all_none(self):
        """Test with all None scores."""
        score = calculate_composite_score(None, None, None)
        assert score is None

    def test_custom_weights(self):
        """Test with custom weights."""
        weights = {"technical": 0.5, "content": 0.25, "ai_visibility": 0.25}
        score = calculate_composite_score(100, 80, 80, weights)
        # (100*0.5) + (80*0.25) + (80*0.25) = 50 + 20 + 20 = 90
        assert score == 90
