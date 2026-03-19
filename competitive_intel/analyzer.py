import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from .models import ComparisonMatrix, CompetitiveAnalysis


class CompetitiveAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_competitive_landscape(self, prospect_url: str, competitor_urls: list[str]) -> CompetitiveAnalysis:
        """Generate comprehensive competitive analysis."""
        try:
            self.logger.info(f"Analyzing {prospect_url} vs {len(competitor_urls)} competitors")

            # Run SEO health reports for all URLs
            prospect_report = self._run_seo_report(prospect_url)
            competitor_reports = {}

            for comp_url in competitor_urls:
                competitor_reports[comp_url] = self._run_seo_report(comp_url)

            # Build comparison matrix
            comparison_matrix = self._build_comparison_matrix(prospect_report, competitor_reports)

            # Identify AI visibility gaps (our differentiator)
            ai_gaps = self._identify_ai_visibility_gaps(prospect_report, competitor_reports)

            # Calculate win probability
            win_prob = self._calculate_win_probability(comparison_matrix)

            # Generate key differentiators
            differentiators = self._identify_key_differentiators(comparison_matrix)

            # Generate recommendations
            recommendations = self._generate_recommendations(comparison_matrix, ai_gaps)

            return CompetitiveAnalysis(
                prospect_url=prospect_url,
                competitor_urls=competitor_urls,
                analysis_date=datetime.now(),
                comparison_matrix=comparison_matrix.__dict__,
                ai_visibility_gaps=ai_gaps,
                win_probability=win_prob,
                key_differentiators=differentiators,
                recommendations=recommendations
            )

        except Exception as e:
            self.logger.error(f"Competitive analysis failed: {e}")
            raise

    def _run_seo_report(self, url: str) -> dict[str, Any]:
        """Run SEO health report for a URL."""
        try:
            # Validate URL format and security
            if not self._is_safe_url(url):
                self.logger.warning(f"Unsafe URL rejected: {url}")
                return self._generate_mock_report(url)

            # Try to import the SEO health report package directly
            try:
                from seo_health_report import generate_report

                result = generate_report(
                    target_url=url,
                    company_name="Competitive Analysis",
                    output_format="json"
                )
                return result
            except ImportError:
                self.logger.info("seo_health_report package not available")
                return self._generate_mock_report(url)

        except (ValueError, TypeError, OSError) as e:
            self.logger.warning(f"Using mock data for {url}: {e}")
            return self._generate_mock_report(url)

    def _is_safe_url(self, url: str) -> bool:
        """Validate URL is safe for processing."""
        try:
            parsed = urlparse(url)

            # Must be HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False

            # Must have valid hostname
            if not parsed.hostname:
                return False

            # Block private/internal networks (basic SSRF protection)
            hostname = parsed.hostname.lower()
            if hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
                return False

            # Block private IP ranges (simplified)
            if hostname.startswith(('192.168.', '10.', '172.')):
                return False

            return True

        except Exception:
            return False

    def _generate_mock_report(self, url: str) -> dict[str, Any]:
        """
        DEPRECATED: This used to generate fake random scores.
        Now returns a clear failure indicator instead of fake data.

        For real audits, use the orchestrate module directly.
        """
        self.logger.warning(f"Cannot generate real report for {url} - returning failure indicator")

        # Return a clearly marked failure - NOT fake data
        return {
            'overall_score': None,
            'grade': 'N/A',
            'data_source': 'audit_unavailable',
            'error': 'Real audit required but could not be performed',
            'technical': {'score': None},
            'content': {'score': None},
            'ai_visibility': {'score': None},
            'url': url
        }

    def _build_comparison_matrix(self, prospect_report: dict, competitor_reports: dict) -> ComparisonMatrix:
        """Build detailed comparison matrix."""

        # Extract scores
        prospect_score = prospect_report.get('overall_score', 0)
        competitor_scores = {url: report.get('overall_score', 0) for url, report in competitor_reports.items()}

        # Technical comparison
        technical_comparison = {
            prospect_report['url']: prospect_report.get('technical', {}).get('score', 0)
        }
        technical_comparison.update({
            url: report.get('technical', {}).get('score', 0)
            for url, report in competitor_reports.items()
        })

        # Content comparison
        content_comparison = {
            prospect_report['url']: prospect_report.get('content', {}).get('score', 0)
        }
        content_comparison.update({
            url: report.get('content', {}).get('score', 0)
            for url, report in competitor_reports.items()
        })

        # AI visibility comparison (our differentiator)
        ai_visibility_comparison = {
            prospect_report['url']: prospect_report.get('ai_visibility', {}).get('score', 0)
        }
        ai_visibility_comparison.update({
            url: report.get('ai_visibility', {}).get('score', 0)
            for url, report in competitor_reports.items()
        })

        # Grade comparison
        grade_comparison = {
            prospect_report['url']: prospect_report.get('grade', 'F')
        }
        grade_comparison.update({
            url: report.get('grade', 'F')
            for url, report in competitor_reports.items()
        })

        return ComparisonMatrix(
            prospect_score=prospect_score,
            competitor_scores=competitor_scores,
            technical_comparison=technical_comparison,
            content_comparison=content_comparison,
            ai_visibility_comparison=ai_visibility_comparison,
            grade_comparison=grade_comparison
        )

    def _identify_ai_visibility_gaps(self, prospect_report: dict, competitor_reports: dict) -> list[str]:
        """Identify AI visibility gaps - our key differentiator."""
        gaps = []

        prospect_ai_score = prospect_report.get('ai_visibility', {}).get('score', 0)

        # Compare against competitors
        competitor_ai_scores = [
            report.get('ai_visibility', {}).get('score', 0)
            for report in competitor_reports.values()
        ]

        if competitor_ai_scores:
            avg_competitor_ai = sum(competitor_ai_scores) / len(competitor_ai_scores)
            max_competitor_ai = max(competitor_ai_scores)

            if prospect_ai_score < avg_competitor_ai:
                gap = avg_competitor_ai - prospect_ai_score
                gaps.append(f"AI visibility {gap:.0f} points below competitor average")

            if prospect_ai_score < max_competitor_ai:
                gap = max_competitor_ai - prospect_ai_score
                gaps.append(f"AI visibility {gap:.0f} points behind market leader")

            # Specific AI visibility issues
            if prospect_ai_score < 60:
                gaps.append("Low AI search presence - missing from ChatGPT/Claude responses")
            if prospect_ai_score < 70:
                gaps.append("Poor content structure for AI extraction")
            if prospect_ai_score < 80:
                gaps.append("Limited schema markup for AI understanding")

        return gaps

    def _calculate_win_probability(self, matrix: ComparisonMatrix) -> float:
        """Calculate probability of winning against competitors."""

        # Base probability on overall score comparison
        prospect_score = matrix.prospect_score
        competitor_scores = list(matrix.competitor_scores.values())

        if not competitor_scores:
            return 0.5  # 50% if no competitors

        avg_competitor_score = sum(competitor_scores) / len(competitor_scores)

        # Calculate win probability based on score difference
        score_diff = prospect_score - avg_competitor_score

        # Convert score difference to probability (sigmoid-like function)
        if score_diff >= 20:
            return 0.9  # 90% chance if 20+ points ahead
        elif score_diff >= 10:
            return 0.75  # 75% chance if 10+ points ahead
        elif score_diff >= 0:
            return 0.6   # 60% chance if ahead
        elif score_diff >= -10:
            return 0.4   # 40% chance if slightly behind
        elif score_diff >= -20:
            return 0.25  # 25% chance if significantly behind
        else:
            return 0.1   # 10% chance if far behind

    def _identify_key_differentiators(self, matrix: ComparisonMatrix) -> list[str]:
        """Identify key competitive differentiators."""
        differentiators = []

        prospect_url = list(matrix.technical_comparison.keys())[0]  # First key is prospect

        # Technical differentiators
        prospect_tech = matrix.technical_comparison[prospect_url]
        competitor_tech_scores = [score for url, score in matrix.technical_comparison.items() if url != prospect_url]

        if competitor_tech_scores and prospect_tech > max(competitor_tech_scores):
            differentiators.append("Superior technical SEO implementation")

        # Content differentiators
        prospect_content = matrix.content_comparison[prospect_url]
        competitor_content_scores = [score for url, score in matrix.content_comparison.items() if url != prospect_url]

        if competitor_content_scores and prospect_content > max(competitor_content_scores):
            differentiators.append("Higher quality content and authority signals")

        # AI visibility differentiators (our specialty)
        prospect_ai = matrix.ai_visibility_comparison[prospect_url]
        competitor_ai_scores = [score for url, score in matrix.ai_visibility_comparison.items() if url != prospect_url]

        if competitor_ai_scores and prospect_ai > max(competitor_ai_scores):
            differentiators.append("Leading AI search visibility and optimization")
        elif competitor_ai_scores and prospect_ai < min(competitor_ai_scores):
            differentiators.append("Significant AI visibility improvement opportunity")

        return differentiators

    def _generate_recommendations(self, matrix: ComparisonMatrix, ai_gaps: list[str]) -> list[str]:
        """Generate strategic recommendations."""
        recommendations = []

        # AI visibility recommendations (our focus)
        if ai_gaps:
            recommendations.append("Implement AI search optimization strategy to capture ChatGPT/Claude traffic")
            recommendations.append("Optimize content structure for AI extraction and citation")
            recommendations.append("Add comprehensive schema markup for AI understanding")

        # Score-based recommendations
        if matrix.prospect_score < 70:
            recommendations.append("Address fundamental SEO issues before competitive positioning")
        elif matrix.prospect_score < 85:
            recommendations.append("Focus on high-impact improvements to gain competitive advantage")
        else:
            recommendations.append("Maintain leadership position while monitoring competitor movements")

        return recommendations

# Global analyzer instance
analyzer = CompetitiveAnalyzer()
