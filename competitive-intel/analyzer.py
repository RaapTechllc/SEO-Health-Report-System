import sys
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory for SEO health report imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import CompetitiveAnalysis, ComparisonMatrix, TalkingPoint

class CompetitiveAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_competitive_landscape(self, prospect_url: str, competitor_urls: List[str]) -> CompetitiveAnalysis:
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
    
    def _run_seo_report(self, url: str) -> Dict[str, Any]:
        """Run SEO health report for a URL."""
        try:
            # Validate URL format and security
            if not self._is_safe_url(url):
                self.logger.warning(f"Unsafe URL rejected: {url}")
                return self._generate_mock_report(url)
            
            # Try to import and run the SEO health report system
            import importlib.util
            
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            seo_path = os.path.join(project_root, "seo-health-report", "__init__.py")
            
            if os.path.exists(seo_path):
                spec = importlib.util.spec_from_file_location("seo_health_report", seo_path)
                seo_module = importlib.util.module_from_spec(spec)
                sys.modules["seo_health_report"] = seo_module
                spec.loader.exec_module(seo_module)
                
                result = seo_module.generate_report(
                    target_url=url,
                    company_name="Competitive Analysis",
                    output_format="json"
                )
                return result
            else:
                return self._generate_mock_report(url)
                
        except Exception as e:
            self.logger.warning(f"Using mock data for {url}: {e}")
            return self._generate_mock_report(url)
    
    def _is_safe_url(self, url: str) -> bool:
        """Validate URL is safe for processing."""
        try:
            from urllib.parse import urlparse
            
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
    
    def _generate_mock_report(self, url: str) -> Dict[str, Any]:
        """Generate mock report for testing."""
        import random
        import hashlib
        
        # Use URL hash for consistent mock data
        url_hash = int(hashlib.md5(url.encode()).hexdigest()[:8], 16)
        random.seed(url_hash)
        
        technical_score = random.randint(60, 95)
        content_score = random.randint(55, 90)
        ai_visibility_score = random.randint(40, 85)
        
        overall_score = int((technical_score * 0.30) + (content_score * 0.35) + (ai_visibility_score * 0.35))
        
        grade = 'A' if overall_score >= 90 else 'B' if overall_score >= 80 else 'C' if overall_score >= 70 else 'D' if overall_score >= 60 else 'F'
        
        return {
            'overall_score': overall_score,
            'grade': grade,
            'technical': {'score': technical_score},
            'content': {'score': content_score},
            'ai_visibility': {'score': ai_visibility_score},
            'url': url
        }
    
    def _build_comparison_matrix(self, prospect_report: Dict, competitor_reports: Dict) -> ComparisonMatrix:
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
    
    def _identify_ai_visibility_gaps(self, prospect_report: Dict, competitor_reports: Dict) -> List[str]:
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
    
    def _identify_key_differentiators(self, matrix: ComparisonMatrix) -> List[str]:
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
    
    def _generate_recommendations(self, matrix: ComparisonMatrix, ai_gaps: List[str]) -> List[str]:
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
