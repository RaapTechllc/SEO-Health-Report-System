"""
Unit Tests for Business Profiles and Blocker Detection

Tests the blocker-based score capping system and business profile configurations.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "seo-health-report"))

from business_profiles import (
    get_business_profile,
    list_available_profiles,
    get_profile_weights,
    get_profile_blockers,
    BUSINESS_PROFILES,
    BlockerConfig,
)
from scripts.calculate_scores import (
    calculate_composite_score,
    detect_blockers,
    determine_grade,
    generate_blocker_summary,
)


class TestBusinessProfiles:
    """Test business profile configuration."""

    def test_mechanical_trades_profile_exists(self):
        """Test that mechanical_trades profile is available."""
        profile = get_business_profile("mechanical_trades")
        assert profile.name == "mechanical_trades"
        assert profile.display_name == "Mechanical Trades & Construction"

    def test_generic_profile_exists(self):
        """Test that generic profile is available."""
        profile = get_business_profile("generic")
        assert profile.name == "generic"

    def test_unknown_profile_falls_back_to_generic(self):
        """Test that unknown profile names fall back to generic."""
        profile = get_business_profile("unknown_profile")
        assert profile.name == "generic"

    def test_mechanical_trades_weights(self):
        """Test mechanical trades profile has correct weights."""
        profile = get_business_profile("mechanical_trades")
        weights = profile.weights

        assert "local_gbp" in weights
        assert weights["local_gbp"] == 0.30  # 30% for local

        assert "content_eeat" in weights
        assert weights["content_eeat"] == 0.25

        assert "technical" in weights
        assert weights["technical"] == 0.20

        assert "lead_funnel" in weights
        assert weights["lead_funnel"] == 0.15

        assert "authority" in weights
        assert weights["authority"] == 0.10

        # Verify weights sum to 1.0
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01

    def test_mechanical_trades_has_blockers(self):
        """Test mechanical trades profile has blockers configured."""
        profile = get_business_profile("mechanical_trades")
        assert len(profile.blockers) > 0

        # Check for specific blockers
        blocker_ids = [b.id for b in profile.blockers]
        assert "server_response_3s" in blocker_ids
        assert "no_ssl" in blocker_ids
        assert "gbp_not_claimed" in blocker_ids
        assert "phone_not_clickable_mobile" in blocker_ids

    def test_list_available_profiles(self):
        """Test listing all available profiles."""
        profiles = list_available_profiles()
        assert len(profiles) >= 2  # At least generic and mechanical_trades

        profile_names = [p["name"] for p in profiles]
        assert "generic" in profile_names
        assert "mechanical_trades" in profile_names

    def test_get_profile_weights_function(self):
        """Test get_profile_weights helper function."""
        weights = get_profile_weights("mechanical_trades")
        assert "local_gbp" in weights
        assert "lead_funnel" in weights

    def test_get_profile_blockers_function(self):
        """Test get_profile_blockers helper function."""
        blockers = get_profile_blockers("mechanical_trades")
        assert len(blockers) > 0
        assert all(isinstance(b, BlockerConfig) for b in blockers)


class TestBlockerDetection:
    """Test blocker detection logic."""

    def test_detect_no_ssl_blocker(self):
        """Test detection of no SSL blocker."""
        audit_results = {
            "audits": {
                "technical": {
                    "has_ssl": False,
                    "score": 70,
                }
            }
        }

        profile = get_business_profile("mechanical_trades")
        active = detect_blockers(audit_results, profile.blockers)

        # Should detect no_ssl blocker
        blocker_ids = [b["id"] for b in active]
        assert "no_ssl" in blocker_ids

        # Check the cap value
        no_ssl_blocker = next(b for b in active if b["id"] == "no_ssl")
        assert no_ssl_blocker["cap"] == 40

    def test_detect_slow_server_blocker(self):
        """Test detection of slow server response blocker."""
        audit_results = {
            "audits": {
                "technical": {
                    "server_response_time": 4000,  # 4 seconds > 3s threshold
                    "score": 60,
                }
            }
        }

        profile = get_business_profile("mechanical_trades")
        active = detect_blockers(audit_results, profile.blockers)

        blocker_ids = [b["id"] for b in active]
        assert "server_response_3s" in blocker_ids

        slow_blocker = next(b for b in active if b["id"] == "server_response_3s")
        assert slow_blocker["cap"] == 50

    def test_no_blockers_when_healthy(self):
        """Test that no blockers are detected for healthy site."""
        audit_results = {
            "audits": {
                "technical": {
                    "has_ssl": True,
                    "server_response_time": 500,  # Fast
                    "mobile_usability_score": 95,
                    "core_web_vitals_passed": True,
                    "score": 90,
                }
            }
        }

        profile = get_business_profile("mechanical_trades")
        active = detect_blockers(audit_results, profile.blockers)

        # Should not detect technical blockers
        blocker_ids = [b["id"] for b in active]
        assert "no_ssl" not in blocker_ids
        assert "server_response_3s" not in blocker_ids


class TestScoreCapping:
    """Test blocker-based score capping."""

    def test_score_capped_by_blocker(self):
        """Test that score is capped when blocker is active."""
        audit_results = {
            "audits": {
                "technical": {
                    "has_ssl": False,  # This triggers no_ssl blocker (cap 40)
                    "score": 80,
                    "max": 100,
                },
                "content": {
                    "score": 75,
                    "max": 100,
                },
            }
        }

        scores = calculate_composite_score(
            audit_results,
            business_profile="mechanical_trades"
        )

        # Score should be capped at 40 due to no_ssl blocker
        assert scores["overall_score"] <= 40
        assert scores["capped_by"] is not None
        assert scores["capped_by"]["id"] == "no_ssl"
        assert "(Blocked)" in scores["grade"]

    def test_most_restrictive_blocker_wins(self):
        """Test that the most restrictive blocker caps the score."""
        audit_results = {
            "audits": {
                "technical": {
                    "has_ssl": False,  # Cap at 40
                    "server_response_time": 4000,  # Cap at 50
                    "score": 80,
                    "max": 100,
                }
            }
        }

        scores = calculate_composite_score(
            audit_results,
            business_profile="mechanical_trades"
        )

        # Should be capped by no_ssl (40) since it's more restrictive than slow server (50)
        assert scores["overall_score"] <= 40
        assert scores["capped_by"]["id"] == "no_ssl"

    def test_raw_score_preserved(self):
        """Test that raw score is preserved even when capped."""
        audit_results = {
            "audits": {
                "technical": {
                    "has_ssl": False,
                    "score": 80,
                    "max": 100,
                }
            }
        }

        scores = calculate_composite_score(
            audit_results,
            business_profile="mechanical_trades"
        )

        # Raw score should be the uncapped value
        assert scores["raw_score"] > scores["overall_score"]
        assert scores["overall_score"] <= 40

    def test_no_capping_without_blockers(self):
        """Test that score is not capped when no blockers active."""
        audit_results = {
            "audits": {
                "technical": {
                    "has_ssl": True,
                    "server_response_time": 500,
                    "mobile_usability_score": 95,
                    "core_web_vitals_passed": True,
                    "score": 85,
                    "max": 100,
                }
            }
        }

        scores = calculate_composite_score(
            audit_results,
            business_profile="mechanical_trades"
        )

        # Score should not be capped
        assert scores["capped_by"] is None
        assert "(Blocked)" not in scores["grade"]


class TestBlockerSummary:
    """Test blocker summary generation."""

    def test_generate_blocker_summary(self):
        """Test blocker summary generation."""
        audit_results = {
            "audits": {
                "technical": {
                    "has_ssl": False,
                    "score": 80,
                }
            }
        }

        scores = calculate_composite_score(
            audit_results,
            business_profile="mechanical_trades"
        )

        summary = generate_blocker_summary(scores)

        assert len(summary) > 0

        first_blocker = summary[0]
        assert "id" in first_blocker
        assert "title" in first_blocker
        assert "severity" in first_blocker
        assert "recommendations" in first_blocker
        assert "why_it_matters" in first_blocker

    def test_blocker_severity_classification(self):
        """Test that blockers are classified by severity correctly."""
        audit_results = {
            "audits": {
                "technical": {
                    "has_ssl": False,  # Cap at 40 - should be critical
                    "score": 80,
                }
            }
        }

        scores = calculate_composite_score(
            audit_results,
            business_profile="mechanical_trades"
        )

        summary = generate_blocker_summary(scores)

        # no_ssl caps at 40, which should be "critical"
        ssl_blocker = next(b for b in summary if b["id"] == "no_ssl")
        assert ssl_blocker["severity"] == "critical"


class TestGradeWithBlockers:
    """Test grade determination with blockers."""

    def test_blocked_grade_suffix(self):
        """Test that blocked grades have (Blocked) suffix."""
        audit_results = {
            "audits": {
                "technical": {
                    "has_ssl": False,
                    "score": 95,  # Would be A without blocker
                }
            }
        }

        scores = calculate_composite_score(
            audit_results,
            business_profile="mechanical_trades"
        )

        # Grade should have (Blocked) suffix
        assert "(Blocked)" in scores["grade"]

    def test_grade_reflects_capped_score(self):
        """Test that grade reflects the capped score, not raw score."""
        audit_results = {
            "audits": {
                "technical": {
                    "has_ssl": False,  # Caps at 40
                    "score": 95,
                }
            }
        }

        scores = calculate_composite_score(
            audit_results,
            business_profile="mechanical_trades"
        )

        # With score capped at 40, grade should be F (Blocked)
        base_grade = scores["grade"].split()[0]
        assert base_grade == "F"


class TestGenericVsMechanicalTrades:
    """Test differences between generic and mechanical_trades profiles."""

    def test_different_weights(self):
        """Test that profiles have different weights."""
        generic = get_business_profile("generic")
        trades = get_business_profile("mechanical_trades")

        # Generic has ai_visibility, trades doesn't
        assert "ai_visibility" in generic.weights
        assert "ai_visibility" not in trades.weights

        # Trades has local_gbp and lead_funnel, generic doesn't
        assert "local_gbp" in trades.weights
        assert "lead_funnel" in trades.weights

    def test_different_blockers(self):
        """Test that profiles have different blockers."""
        generic = get_business_profile("generic")
        trades = get_business_profile("mechanical_trades")

        generic_ids = {b.id for b in generic.blockers}
        trades_ids = {b.id for b in trades.blockers}

        # Trades should have phone-specific blockers
        assert "phone_not_clickable_mobile" in trades_ids

        # Trades should have GBP blocker
        assert "gbp_not_claimed" in trades_ids

    def test_trades_stricter_on_server_response(self):
        """Test that trades profile is stricter on server response time."""
        generic = get_business_profile("generic")
        trades = get_business_profile("mechanical_trades")

        # Find server response blocker in each
        generic_server = next(
            (b for b in generic.blockers if "server" in b.id.lower()),
            None
        )
        trades_server = next(
            (b for b in trades.blockers if "server" in b.id.lower()),
            None
        )

        # Trades should have stricter threshold (3s vs 5s)
        if generic_server and trades_server:
            assert trades_server.threshold <= generic_server.threshold
