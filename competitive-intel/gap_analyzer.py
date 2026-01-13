from typing import Dict, List, Any
import logging

from models import TalkingPoint

class GapAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_competitive_gaps(self, prospect_report: Dict[str, Any], 
                                competitor_reports: Dict[str, Dict[str, Any]]) -> List[TalkingPoint]:
        """Analyze gaps between prospect and competitors."""
        
        talking_points = []
        
        # AI Visibility Gaps (Primary Focus)
        ai_points = self._analyze_ai_visibility_gaps(prospect_report, competitor_reports)
        talking_points.extend(ai_points)
        
        # Technical Gaps
        tech_points = self._analyze_technical_gaps(prospect_report, competitor_reports)
        talking_points.extend(tech_points)
        
        # Content Gaps
        content_points = self._analyze_content_gaps(prospect_report, competitor_reports)
        talking_points.extend(content_points)
        
        # Overall Performance Gaps
        overall_points = self._analyze_overall_gaps(prospect_report, competitor_reports)
        talking_points.extend(overall_points)
        
        return talking_points
    
    def _analyze_ai_visibility_gaps(self, prospect_report: Dict, competitor_reports: Dict) -> List[TalkingPoint]:
        """Analyze AI visibility gaps - our key differentiator."""
        points = []
        
        prospect_ai = prospect_report.get('ai_visibility', {}).get('score', 0)
        competitor_ai_scores = [
            report.get('ai_visibility', {}).get('score', 0)
            for report in competitor_reports.values()
        ]
        
        if not competitor_ai_scores:
            return points
        
        avg_competitor_ai = sum(competitor_ai_scores) / len(competitor_ai_scores)
        max_competitor_ai = max(competitor_ai_scores)
        
        # Gap analysis
        if prospect_ai < avg_competitor_ai:
            gap = avg_competitor_ai - prospect_ai
            points.append(TalkingPoint(
                category="weakness",
                title="AI Search Visibility Gap",
                description=f"Your AI visibility score is {gap:.0f} points below competitor average",
                supporting_data=f"Your score: {prospect_ai}/100, Competitor average: {avg_competitor_ai:.0f}/100",
                confidence=0.9
            ))
        
        if prospect_ai > max_competitor_ai:
            advantage = prospect_ai - max_competitor_ai
            points.append(TalkingPoint(
                category="strength",
                title="AI Search Leadership",
                description=f"You lead competitors in AI visibility by {advantage:.0f} points",
                supporting_data=f"Your score: {prospect_ai}/100, Best competitor: {max_competitor_ai}/100",
                confidence=0.95
            ))
        
        # Specific AI opportunities
        if prospect_ai < 60:
            points.append(TalkingPoint(
                category="opportunity",
                title="Untapped AI Search Traffic",
                description="Significant opportunity to capture traffic from ChatGPT, Claude, and Perplexity searches",
                supporting_data="AI search queries growing 40% annually, most brands unprepared",
                confidence=0.85
            ))
        
        return points
    
    def _analyze_technical_gaps(self, prospect_report: Dict, competitor_reports: Dict) -> List[TalkingPoint]:
        """Analyze technical SEO gaps."""
        points = []
        
        prospect_tech = prospect_report.get('technical', {}).get('score', 0)
        competitor_tech_scores = [
            report.get('technical', {}).get('score', 0)
            for report in competitor_reports.values()
        ]
        
        if not competitor_tech_scores:
            return points
        
        avg_competitor_tech = sum(competitor_tech_scores) / len(competitor_tech_scores)
        
        if prospect_tech < avg_competitor_tech:
            gap = avg_competitor_tech - prospect_tech
            points.append(TalkingPoint(
                category="weakness",
                title="Technical SEO Foundation Gap",
                description=f"Technical implementation lags competitors by {gap:.0f} points",
                supporting_data=f"Areas likely affected: page speed, crawlability, mobile optimization",
                confidence=0.8
            ))
        elif prospect_tech > avg_competitor_tech:
            advantage = prospect_tech - avg_competitor_tech
            points.append(TalkingPoint(
                category="strength",
                title="Strong Technical Foundation",
                description=f"Technical SEO outperforms competitors by {advantage:.0f} points",
                supporting_data="Solid foundation for advanced optimization strategies",
                confidence=0.85
            ))
        
        return points
    
    def _analyze_content_gaps(self, prospect_report: Dict, competitor_reports: Dict) -> List[TalkingPoint]:
        """Analyze content and authority gaps."""
        points = []
        
        prospect_content = prospect_report.get('content', {}).get('score', 0)
        competitor_content_scores = [
            report.get('content', {}).get('score', 0)
            for report in competitor_reports.values()
        ]
        
        if not competitor_content_scores:
            return points
        
        avg_competitor_content = sum(competitor_content_scores) / len(competitor_content_scores)
        
        if prospect_content < avg_competitor_content:
            gap = avg_competitor_content - prospect_content
            points.append(TalkingPoint(
                category="weakness",
                title="Content Authority Gap",
                description=f"Content quality and authority trails competitors by {gap:.0f} points",
                supporting_data="May indicate thin content, weak E-E-A-T signals, or poor topical coverage",
                confidence=0.8
            ))
        elif prospect_content > avg_competitor_content:
            advantage = prospect_content - avg_competitor_content
            points.append(TalkingPoint(
                category="strength",
                title="Content Leadership",
                description=f"Content quality exceeds competitors by {advantage:.0f} points",
                supporting_data="Strong foundation for thought leadership and AI optimization",
                confidence=0.85
            ))
        
        return points
    
    def _analyze_overall_gaps(self, prospect_report: Dict, competitor_reports: Dict) -> List[TalkingPoint]:
        """Analyze overall performance gaps."""
        points = []
        
        prospect_score = prospect_report.get('overall_score', 0)
        competitor_scores = [
            report.get('overall_score', 0)
            for report in competitor_reports.values()
        ]
        
        if not competitor_scores:
            return points
        
        avg_competitor_score = sum(competitor_scores) / len(competitor_scores)
        max_competitor_score = max(competitor_scores)
        
        # Market position analysis
        if prospect_score > max_competitor_score:
            points.append(TalkingPoint(
                category="strength",
                title="Market Leadership Position",
                description=f"You lead the competitive landscape with {prospect_score}/100",
                supporting_data=f"Ahead of best competitor by {prospect_score - max_competitor_score:.0f} points",
                confidence=0.95
            ))
        elif prospect_score < avg_competitor_score:
            gap = avg_competitor_score - prospect_score
            points.append(TalkingPoint(
                category="threat",
                title="Competitive Disadvantage",
                description=f"Overall SEO performance trails market by {gap:.0f} points",
                supporting_data="Risk of losing market share to better-optimized competitors",
                confidence=0.9
            ))
        
        # Grade-based insights
        prospect_grade = prospect_report.get('grade', 'F')
        if prospect_grade in ['D', 'F']:
            points.append(TalkingPoint(
                category="opportunity",
                title="High-Impact Improvement Potential",
                description=f"Current grade ({prospect_grade}) indicates significant upside opportunity",
                supporting_data="Quick wins available across technical, content, and AI optimization",
                confidence=0.9
            ))
        
        return points

# Global gap analyzer
gap_analyzer = GapAnalyzer()
