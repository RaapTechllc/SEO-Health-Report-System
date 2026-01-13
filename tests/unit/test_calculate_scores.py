"""
Tests for calculate_scores module.
"""

import pytest
from seo_health_report.scripts.calculate_scores import (
    WEIGHTS,
    calculate_composite_score,
    determine_grade,
    get_grade_description,
    get_component_status,
    compare_scores,
    calculate_benchmark_comparison,
)


class TestWeights:
    """Test scoring weights."""

    def test_weights_exist(self):
        """Test weights dictionary exists."""
        assert "technical" in WEIGHTS
        assert "content" in WEIGHTS
        assert "ai_visibility" in WEIGHTS

    def test_weights_sum_to_one(self):
        """Test weights sum to 1.0."""
        total = sum(WEIGHTS.values())
        assert abs(total - 1.0) < 0.01

    def test_weights_positive(self):
        """Test all weights are positive."""
        for weight in WEIGHTS.values():
            assert weight > 0

    def test_technical_weight(self):
        """Test technical weight is 0.30."""
        assert WEIGHTS["technical"] == 0.30

    def test_content_weight(self):
        """Test content weight is 0.35."""
        assert WEIGHTS["content"] == 0.35

    def test_ai_visibility_weight(self):
        """Test AI visibility weight is 0.35."""
        assert WEIGHTS["ai_visibility"] == 0.35


class TestCalculateCompositeScore:
    """Test composite score calculation."""

    def test_calculate_all_perfect_scores(self, sample_audit_results):
        """Test calculation with perfect scores."""
        sample_audit_results["audits"]["technical"]["score"] = 100
        sample_audit_results["audits"]["content"]["score"] = 100
        sample_audit_results["audits"]["ai_visibility"]["score"] = 100

        result = calculate_composite_score(sample_audit_results)
        assert result["overall_score"] == 100
        assert result["grade"] == "A"

    def test_calculate_all_zero_scores(self, sample_audit_results):
        """Test calculation with zero scores."""
        sample_audit_results["audits"]["technical"]["score"] = 0
        sample_audit_results["audits"]["content"]["score"] = 0
        sample_audit_results["audits"]["ai_visibility"]["score"] = 0

        result = calculate_composite_score(sample_audit_results)
        assert result["overall_score"] == 0
        assert result["grade"] == "F"

    def test_calculate_mixed_scores(self, sample_audit_results):
        """Test calculation with mixed scores."""
        sample_audit_results["audits"]["technical"]["score"] = 80
        sample_audit_results["audits"]["content"]["score"] = 70
        sample_audit_results["audits"]["ai_visibility"]["score"] = 90

        result = calculate_composite_score(sample_audit_results)
        # Weighted: 80*0.30 + 70*0.35 + 90*0.35 = 24 + 24.5 + 31.5 = 80
        assert result["overall_score"] == 80

    def test_calculate_custom_weights(self, sample_audit_results):
        """Test calculation with custom weights."""
        custom_weights = {"technical": 0.50, "content": 0.30, "ai_visibility": 0.20}
        sample_audit_results["audits"]["technical"]["score"] = 80
        sample_audit_results["audits"]["content"]["score"] = 80
        sample_audit_results["audits"]["ai_visibility"]["score"] = 80

        result = calculate_composite_score(sample_audit_results, weights=custom_weights)
        assert result["overall_score"] == 80

    def test_calculate_component_scores(self, sample_audit_results):
        """Test component scores are calculated."""
        result = calculate_composite_score(sample_audit_results)
        assert "component_scores" in result
        assert "technical" in result["component_scores"]
        assert "content" in result["component_scores"]
        assert "ai_visibility" in result["component_scores"]

    def test_calculate_weights_used(self, sample_audit_results):
        """Test weights used are recorded."""
        result = calculate_composite_score(sample_audit_results)
        assert "weights_used" in result
        assert result["weights_used"] == WEIGHTS

    def test_calculate_missing_audit(self, sample_audit_results):
        """Test calculation with missing audit."""
        sample_audit_results["audits"]["content"] = None

        result = calculate_composite_score(sample_audit_results)
        # Should still work but weight for content won't be applied
        assert "overall_score" in result

    def test_calculate_score_normalization(self, sample_audit_results):
        """Test scores are normalized to 100-point scale."""
        sample_audit_results["audits"]["technical"]["score"] = 50
        sample_audit_results["audits"]["technical"]["max"] = 50

        result = calculate_composite_score(sample_audit_results)
        technical_score = result["component_scores"]["technical"]["score"]
        assert technical_score == 100  # Normalized from 50/50 to 100

    def test_calculate_score_integer(self, sample_audit_results):
        """Test overall score is integer."""
        result = calculate_composite_score(sample_audit_results)
        assert isinstance(result["overall_score"], int)


class TestDetermineGrade:
    """Test grade determination."""

    def test_grade_a_high_score(self):
        """Test score 95 gets grade A."""
        grade = determine_grade(95)
        assert grade == "A"

    def test_grade_a_threshold(self):
        """Test score at threshold gets grade A."""
        grade = determine_grade(90)
        assert grade == "A"

    def test_grade_b_score(self):
        """Test score 85 gets grade B."""
        grade = determine_grade(85)
        assert grade == "B"

    def test_grade_b_threshold(self):
        """Test score at threshold gets grade B."""
        grade = determine_grade(80)
        assert grade == "B"

    def test_grade_c_score(self):
        """Test score 75 gets grade C."""
        grade = determine_grade(75)
        assert grade == "C"

    def test_grade_c_threshold(self):
        """Test score at threshold gets grade C."""
        grade = determine_grade(70)
        assert grade == "C"

    def test_grade_d_score(self):
        """Test score 65 gets grade D."""
        grade = determine_grade(65)
        assert grade == "D"

    def test_grade_d_threshold(self):
        """Test score at threshold gets grade D."""
        grade = determine_grade(60)
        assert grade == "D"

    def test_grade_f_score(self):
        """Test score 40 gets grade F."""
        grade = determine_grade(40)
        assert grade == "F"

    def test_grade_f_zero(self):
        """Test score 0 gets grade F."""
        grade = determine_grade(0)
        assert grade == "F"

    def test_grade_boundary_a(self):
        """Test boundary between A and B."""
        grade_above = determine_grade(89)
        grade_at = determine_grade(90)
        assert grade_above == "B"
        assert grade_at == "A"

    def test_grade_boundary_b(self):
        """Test boundary between B and C."""
        grade_above = determine_grade(79)
        grade_at = determine_grade(80)
        assert grade_above == "C"
        assert grade_at == "B"

    def test_grade_boundary_c(self):
        """Test boundary between C and D."""
        grade_above = determine_grade(69)
        grade_at = determine_grade(70)
        assert grade_above == "D"
        assert grade_at == "C"

    def test_grade_boundary_d(self):
        """Test boundary between D and F."""
        grade_above = determine_grade(59)
        grade_at = determine_grade(60)
        assert grade_above == "F"
        assert grade_at == "D"


class TestGetGradeDescription:
    """Test grade descriptions."""

    def test_description_grade_a(self):
        """Test description for grade A."""
        desc = get_grade_description("A")
        assert "Excellent" in desc

    def test_description_grade_b(self):
        """Test description for grade B."""
        desc = get_grade_description("B")
        assert "Good" in desc

    def test_description_grade_c(self):
        """Test description for grade C."""
        desc = get_grade_description("C")
        assert "Needs Work" in desc

    def test_description_grade_d(self):
        """Test description for grade D."""
        desc = get_grade_description("D")
        assert "Poor" in desc

    def test_description_grade_f(self):
        """Test description for grade F."""
        desc = get_grade_description("F")
        assert "Critical" in desc

    def test_description_unknown_grade(self):
        """Test description for unknown grade."""
        desc = get_grade_description("X")
        assert "Unknown" in desc


class TestGetComponentStatus:
    """Test component status determination."""

    def test_status_good_high_score(self):
        """Test high score (80%) gets good status."""
        status = get_component_status(80, 100)
        assert status == "good"

    def test_status_good_threshold(self):
        """Test score at threshold gets good status."""
        status = get_component_status(80, 100)
        assert status == "good"

    def test_status_fair_medium_score(self):
        """Test medium score (50%) gets fair status."""
        status = get_component_status(50, 100)
        assert status == "fair"

    def test_status_fair_threshold(self):
        """Test score at threshold gets fair status."""
        status = get_component_status(50, 100)
        assert status == "fair"

    def test_status_poor_low_score(self):
        """Test low score (20%) gets poor status."""
        status = get_component_status(20, 100)
        assert status == "poor"

    def test_status_poor_zero(self):
        """Test score zero gets poor status."""
        status = get_component_status(0, 100)
        assert status == "poor"

    def test_status_different_max(self):
        """Test status with different max score."""
        status = get_component_status(40, 50)  # 80%
        assert status == "good"


class TestCompareScores:
    """Test score comparison between audits."""

    def test_compare_improved(self):
        """Test comparison shows improvement."""
        current = {"overall_score": 85, "component_scores": {}}
        previous = {"overall_score": 70, "component_scores": {}}

        comparison = compare_scores(current, previous)
        assert comparison["overall_change"] == 15
        assert len(comparison["improved"]) == 0  # No component improvement

    def test_compare_declined(self):
        """Test comparison shows decline."""
        current = {"overall_score": 65, "component_scores": {}}
        previous = {"overall_score": 80, "component_scores": {}}

        comparison = compare_scores(current, previous)
        assert comparison["overall_change"] == -15
        assert len(comparison["declined"]) == 0  # No component decline

    def test_compare_unchanged(self):
        """Test comparison shows no change."""
        current = {"overall_score": 75, "component_scores": {}}
        previous = {"overall_score": 75, "component_scores": {}}

        comparison = compare_scores(current, previous)
        assert comparison["overall_change"] == 0

    def test_compare_component_changes(self):
        """Test comparison includes component changes."""
        current = {
            "overall_score": 75,
            "component_scores": {"technical": {"score": 80}, "content": {"score": 70}},
        }
        previous = {
            "overall_score": 70,
            "component_scores": {"technical": {"score": 70}, "content": {"score": 70}},
        }

        comparison = compare_scores(current, previous)
        assert "component_changes" in comparison
        assert "technical" in comparison["component_changes"]
        assert "content" in comparison["component_changes"]

    def test_compare_structure(self):
        """Test comparison has correct structure."""
        current = {"overall_score": 75, "component_scores": {}}
        previous = {"overall_score": 70, "component_scores": {}}

        comparison = compare_scores(current, previous)
        assert "overall_change" in comparison
        assert "component_changes" in comparison
        assert "improved" in comparison
        assert "declined" in comparison
        assert "unchanged" in comparison


class TestBenchmarkComparison:
    """Test comparison against benchmarks."""

    def test_benchmark_default_values(self):
        """Test default benchmarks are used."""
        scores = {"overall_score": 75, "component_scores": {}}

        comparison = calculate_benchmark_comparison(scores)
        assert "overall" in comparison
        assert "components" in comparison

    def test_benchmark_custom_values(self):
        """Test custom benchmarks are used."""
        custom_benchmarks = {
            "technical": 90,
            "content": 85,
            "ai_visibility": 80,
            "overall": 85,
        }
        scores = {"overall_score": 80, "component_scores": {}}

        comparison = calculate_benchmark_comparison(scores, custom_benchmarks)
        assert comparison["overall"]["benchmark"] == 85

    def test_benchmark_above_benchmark(self):
        """Test score above benchmark."""
        scores = {"overall_score": 85, "component_scores": {}}

        comparison = calculate_benchmark_comparison(scores)
        vs_benchmark = comparison["overall"]["vs_benchmark"]
        assert vs_benchmark > 0  # Above default 70

    def test_benchmark_below_benchmark(self):
        """Test score below benchmark."""
        scores = {"overall_score": 60, "component_scores": {}}

        comparison = calculate_benchmark_comparison(scores)
        vs_benchmark = comparison["overall"]["vs_benchmark"]
        assert vs_benchmark < 0  # Below default 70

    def test_benchmark_status_above(self):
        """Test status is above benchmark."""
        scores = {"overall_score": 85, "component_scores": {"technical": {"score": 80}}}

        comparison = calculate_benchmark_comparison(scores)
        assert comparison["components"]["technical"]["status"] == "above"

    def test_benchmark_status_below(self):
        """Test status is below benchmark."""
        scores = {"overall_score": 60, "component_scores": {"technical": {"score": 65}}}

        comparison = calculate_benchmark_comparison(scores)
        assert comparison["components"]["technical"]["status"] == "below"

    def test_benchmark_component_structure(self):
        """Test component comparison structure."""
        scores = {"overall_score": 75, "component_scores": {"technical": {"score": 80}}}

        comparison = calculate_benchmark_comparison(scores)
        tech_comp = comparison["components"]["technical"]
        assert "score" in tech_comp
        assert "benchmark" in tech_comp
        assert "vs_benchmark" in tech_comp
        assert "status" in tech_comp
