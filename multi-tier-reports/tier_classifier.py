import logging
import os
import sys
from typing import Optional
from urllib.parse import urlparse

# Add parent directories for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ReportTier, SiteComplexity, TierRecommendation


class TierClassifier:
    def __init__(self, audit_data: Optional[dict] = None):
        self.logger = logging.getLogger(__name__)
        self.audit_data = audit_data

        # Tier classification thresholds
        self.tier_thresholds = {
            ReportTier.BASIC: {
                "max_complexity": 30,
                "max_pages": 100,
                "max_da": 30,
                "report_time": 30,
                "price_range": (500, 1500)
            },
            ReportTier.PRO: {
                "max_complexity": 70,
                "max_pages": 1000,
                "max_da": 70,
                "report_time": 60,
                "price_range": (1500, 4000)
            },
            ReportTier.ENTERPRISE: {
                "max_complexity": 100,
                "max_pages": 10000,
                "max_da": 100,
                "report_time": 90,
                "price_range": (4000, 10000)
            }
        }

    def classify_site_tier(self, target_url: str, budget_range: Optional[str] = None, audit_data: Optional[dict] = None) -> TierRecommendation:
        """Classify site and recommend appropriate tier."""

        try:
            self.logger.info(f"Classifying tier for {target_url}")

            effective_audit_data = audit_data or self.audit_data

            # Analyze site complexity
            complexity = self._analyze_site_complexity(target_url, effective_audit_data)

            # Determine recommended tier
            recommended_tier = self._determine_tier(complexity, budget_range)

            # Calculate confidence
            confidence = self._calculate_confidence(complexity, recommended_tier)

            # Generate reasoning
            reasoning = self._generate_reasoning(complexity, recommended_tier)

            # Get pricing suggestion
            pricing = self._get_pricing_suggestion(recommended_tier, complexity)

            return TierRecommendation(
                recommended_tier=recommended_tier,
                confidence=confidence,
                reasoning=reasoning,
                site_complexity_score=complexity.complexity_score,
                estimated_report_time=self.tier_thresholds[recommended_tier]["report_time"],
                pricing_suggestion=pricing
            )

        except Exception as e:
            self.logger.error(f"Tier classification failed: {e}")
            # Return safe default
            return TierRecommendation(
                recommended_tier=ReportTier.PRO,
                confidence=0.5,
                reasoning=["Unable to analyze site complexity, recommending standard tier"],
                site_complexity_score=50,
                estimated_report_time=60,
                pricing_suggestion={"min": 1500, "max": 4000, "recommended": 2500}
            )

    def _analyze_site_complexity(self, target_url: str, audit_data: Optional[dict] = None) -> SiteComplexity:
        """Analyze site complexity factors."""

        try:
            # Basic site analysis
            domain = urlparse(target_url).netloc

            # Estimate pages (mock implementation)
            estimated_pages = self._estimate_page_count(target_url)

            # Estimate domain authority (mock implementation)
            domain_authority, da_source = self._estimate_domain_authority(domain, audit_data)

            # Run basic SEO health check to count issues
            technical_issues, ti_source = self._count_technical_issues(target_url, audit_data)

            # Determine content volume
            content_volume = self._assess_content_volume(estimated_pages)

            # Assess competitive landscape
            competitive_landscape = self._assess_competitive_landscape(domain_authority)

            # Calculate overall complexity score
            complexity_score = self._calculate_complexity_score(
                estimated_pages, domain_authority, technical_issues,
                content_volume, competitive_landscape
            )

            return SiteComplexity(
                estimated_pages=estimated_pages,
                domain_authority=domain_authority,
                technical_issues_count=technical_issues,
                content_volume=content_volume,
                competitive_landscape=competitive_landscape,
                complexity_score=complexity_score,
                domain_authority_source=da_source,
                technical_issues_source=ti_source,
            )

        except Exception as e:
            self.logger.warning(f"Site analysis failed, using defaults: {e}")
            return SiteComplexity(
                estimated_pages=500,
                domain_authority=40,
                technical_issues_count=10,
                content_volume="medium",
                competitive_landscape="medium",
                complexity_score=50
            )

    def _estimate_page_count(self, url: str) -> int:
        """Estimate number of pages on site."""
        try:
            # Mock implementation - would use sitemap analysis or crawling
            domain = urlparse(url).netloc

            # Simple heuristic based on domain characteristics
            if any(indicator in domain.lower() for indicator in ['blog', 'news', 'shop', 'store']):
                return 2000  # Content-heavy sites
            elif any(indicator in domain.lower() for indicator in ['corp', 'company', 'business']):
                return 500   # Corporate sites
            else:
                return 100   # Small sites

        except Exception:
            return 500  # Default

    def _estimate_domain_authority(self, domain: str, audit_data: Optional[dict] = None) -> tuple[int, str]:
        """
        Estimate domain authority. Returns (score, source) tuple.

        Priority: Moz API -> audit data -> fallback 40
        """
        # Try audit data first
        if audit_data:
            backlinks = audit_data.get("audits", {}).get("content", {}).get("components", {}).get("backlinks", {})
            if backlinks.get("domain_rating") is not None:
                return (backlinks["domain_rating"], "audit_data")

        self.logger.warning(f"Using baseline DA estimate for {domain} - integrate DA API for accuracy")
        return (40, "fallback")

    def _count_technical_issues(self, url: str, audit_data: Optional[dict] = None) -> tuple[int, str]:
        """
        Count technical SEO issues. Returns (count, source) tuple.

        Priority: audit data -> fallback 10
        """
        if audit_data:
            technical = audit_data.get("audits", {}).get("technical", {})
            components = technical.get("components", {})
            total_issues = 0
            for comp_data in components.values():
                issues = comp_data.get("issues", [])
                total_issues += len(issues)
            if total_issues > 0:
                return (total_issues, "audit_data")

        self.logger.warning(f"Using baseline issue estimate for {url} - run full audit for accuracy")
        return (10, "fallback")

    def _assess_content_volume(self, page_count: int) -> str:
        """Assess content volume level."""
        if page_count < 100:
            return "low"
        elif page_count < 1000:
            return "medium"
        else:
            return "high"

    def _assess_competitive_landscape(self, domain_authority: int) -> str:
        """Assess competitive landscape difficulty."""
        if domain_authority < 30:
            return "low"
        elif domain_authority < 60:
            return "medium"
        else:
            return "high"

    def _calculate_complexity_score(self, pages: int, da: int, issues: int,
                                   content: str, competition: str) -> int:
        """Calculate overall complexity score (0-100)."""

        # Page count factor (0-30 points)
        page_score = min(30, (pages / 1000) * 30)

        # Domain authority factor (0-25 points)
        da_score = (da / 100) * 25

        # Technical issues factor (0-20 points)
        issue_score = min(20, (issues / 25) * 20)

        # Content volume factor (0-15 points)
        content_scores = {"low": 5, "medium": 10, "high": 15}
        content_score = content_scores.get(content, 10)

        # Competition factor (0-10 points)
        comp_scores = {"low": 3, "medium": 7, "high": 10}
        comp_score = comp_scores.get(competition, 7)

        total_score = page_score + da_score + issue_score + content_score + comp_score
        return min(100, int(total_score))

    def _determine_tier(self, complexity: SiteComplexity, budget_range: Optional[str]) -> ReportTier:
        """Determine recommended tier based on complexity and budget."""

        score = complexity.complexity_score

        # Budget constraint check
        if budget_range:
            if "500" in budget_range or "1000" in budget_range:
                return ReportTier.BASIC
            elif "5000" in budget_range or "10000" in budget_range:
                return ReportTier.ENTERPRISE

        # Complexity-based recommendation
        if score <= 30:
            return ReportTier.BASIC
        elif score <= 70:
            return ReportTier.PRO
        else:
            return ReportTier.ENTERPRISE

    def _calculate_confidence(self, complexity: SiteComplexity, tier: ReportTier) -> float:
        """Calculate confidence in tier recommendation."""

        score = complexity.complexity_score
        self.tier_thresholds[tier]

        # High confidence if clearly in tier range
        if tier == ReportTier.BASIC and score <= 20:
            return 0.95
        elif tier == ReportTier.PRO and 40 <= score <= 60:
            return 0.9
        elif tier == ReportTier.ENTERPRISE and score >= 80:
            return 0.95
        # Medium confidence for borderline cases
        elif tier == ReportTier.BASIC and score <= 35:
            return 0.75
        elif tier == ReportTier.PRO and 30 <= score <= 75:
            return 0.8
        elif tier == ReportTier.ENTERPRISE and score >= 65:
            return 0.85
        else:
            return 0.6  # Lower confidence for edge cases

    def _generate_reasoning(self, complexity: SiteComplexity, tier: ReportTier) -> list[str]:
        """Generate reasoning for tier recommendation."""

        reasoning = []

        # Page count reasoning
        if complexity.estimated_pages < 100:
            reasoning.append("Small site with limited pages suitable for basic analysis")
        elif complexity.estimated_pages > 1000:
            reasoning.append("Large site requiring comprehensive analysis")

        # Domain authority reasoning
        if complexity.domain_authority < 30:
            reasoning.append("Low domain authority indicates newer or smaller site")
        elif complexity.domain_authority > 70:
            reasoning.append("High domain authority requires enterprise-level analysis")

        # Technical issues reasoning
        if complexity.technical_issues_count > 20:
            reasoning.append("High number of technical issues requires detailed audit")
        elif complexity.technical_issues_count < 10:
            reasoning.append("Few technical issues allow for streamlined analysis")

        # Competitive landscape reasoning
        if complexity.competitive_landscape == "high":
            reasoning.append("Highly competitive market requires advanced competitive analysis")
        elif complexity.competitive_landscape == "low":
            reasoning.append("Less competitive market suitable for basic positioning")

        # Tier-specific reasoning
        if tier == ReportTier.BASIC:
            reasoning.append("Basic tier provides essential SEO insights for smaller sites")
        elif tier == ReportTier.PRO:
            reasoning.append("Pro tier includes AI visibility analysis and competitive insights")
        else:
            reasoning.append("Enterprise tier provides comprehensive analysis with custom branding")

        return reasoning

    def _get_pricing_suggestion(self, tier: ReportTier, complexity: SiteComplexity) -> dict[str, int]:
        """Get pricing suggestion for the tier."""

        base_range = self.tier_thresholds[tier]["price_range"]

        # Adjust based on complexity
        complexity_multiplier = 1.0 + (complexity.complexity_score / 100) * 0.3

        min_price = int(base_range[0] * complexity_multiplier)
        max_price = int(base_range[1] * complexity_multiplier)
        recommended_price = int((min_price + max_price) / 2)

        return {
            "min": min_price,
            "max": max_price,
            "recommended": recommended_price
        }

# Global tier classifier (without audit data - pass audit_data when calling classify_site_tier)
tier_classifier = TierClassifier()
