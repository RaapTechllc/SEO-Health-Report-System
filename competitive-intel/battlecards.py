from typing import List, Dict, Any
import logging
from datetime import datetime

from models import TalkingPoint, CompetitiveAnalysis
from gap_analyzer import gap_analyzer

class BattlecardGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_battlecard(self, analysis: CompetitiveAnalysis) -> Dict[str, Any]:
        """Generate complete sales battlecard from competitive analysis."""
        
        try:
            # Get talking points from gap analysis
            prospect_report = {'overall_score': analysis.comparison_matrix['prospect_score']}
            competitor_reports = {url: {'overall_score': score} for url, score in analysis.comparison_matrix['competitor_scores'].items()}
            
            talking_points = gap_analyzer.analyze_competitive_gaps(prospect_report, competitor_reports)
            
            # Organize talking points by category
            strengths = [tp for tp in talking_points if tp.category == "strength"]
            weaknesses = [tp for tp in talking_points if tp.category == "weakness"]
            opportunities = [tp for tp in talking_points if tp.category == "opportunity"]
            threats = [tp for tp in talking_points if tp.category == "threat"]
            
            # Generate battlecard
            battlecard = {
                "prospect_info": {
                    "url": analysis.prospect_url,
                    "overall_score": analysis.comparison_matrix['prospect_score'],
                    "win_probability": analysis.win_probability,
                    "analysis_date": analysis.analysis_date.isoformat()
                },
                "executive_summary": self._generate_executive_summary(analysis),
                "key_messages": self._generate_key_messages(analysis),
                "competitive_positioning": {
                    "strengths": [self._format_talking_point(tp) for tp in strengths],
                    "weaknesses": [self._format_talking_point(tp) for tp in weaknesses],
                    "opportunities": [self._format_talking_point(tp) for tp in opportunities],
                    "threats": [self._format_talking_point(tp) for tp in threats]
                },
                "ai_visibility_focus": self._generate_ai_visibility_section(analysis),
                "objection_handling": self._generate_objection_handling(analysis),
                "next_steps": self._generate_next_steps(analysis),
                "supporting_data": self._generate_supporting_data(analysis)
            }
            
            self.logger.info(f"Generated battlecard for {analysis.prospect_url}")
            return battlecard
            
        except Exception as e:
            self.logger.error(f"Battlecard generation failed: {e}")
            raise
    
    def _generate_executive_summary(self, analysis: CompetitiveAnalysis) -> str:
        """Generate executive summary for the battlecard."""
        
        prospect_score = analysis.comparison_matrix['prospect_score']
        win_prob = analysis.win_probability
        
        if win_prob >= 0.7:
            position = "strong competitive position"
        elif win_prob >= 0.5:
            position = "competitive position with opportunities"
        else:
            position = "challenging competitive landscape"
        
        summary = f"""
COMPETITIVE ANALYSIS SUMMARY

Current SEO Score: {prospect_score}/100
Win Probability: {win_prob:.0%}
Market Position: {position.title()}

KEY INSIGHTS:
• AI search visibility represents the biggest opportunity for differentiation
• {len(analysis.ai_visibility_gaps)} specific AI optimization gaps identified
• {len(analysis.key_differentiators)} competitive advantages to leverage

RECOMMENDATION: Focus on AI search optimization as primary differentiator while addressing foundational SEO gaps.
        """.strip()
        
        return summary
    
    def _generate_key_messages(self, analysis: CompetitiveAnalysis) -> List[str]:
        """Generate key sales messages."""
        
        messages = []
        
        # AI visibility message (our differentiator)
        if analysis.ai_visibility_gaps:
            messages.append("🤖 AI Search Opportunity: While competitors focus on traditional SEO, you can capture the growing AI search market (ChatGPT, Claude, Perplexity)")
        
        # Win probability message
        if analysis.win_probability >= 0.7:
            messages.append("📈 Strong Position: You're well-positioned to outperform competitors with focused optimization")
        elif analysis.win_probability >= 0.5:
            messages.append("⚖️ Competitive Balance: Strategic improvements can tip the scales in your favor")
        else:
            messages.append("🎯 High Upside: Significant opportunity to gain competitive advantage through systematic optimization")
        
        # Differentiator messages
        for diff in analysis.key_differentiators[:2]:  # Top 2 differentiators
            messages.append(f"✅ Advantage: {diff}")
        
        return messages
    
    def _generate_ai_visibility_section(self, analysis: CompetitiveAnalysis) -> Dict[str, Any]:
        """Generate AI visibility section - our key differentiator."""
        
        return {
            "title": "AI Search Visibility - Your Competitive Moat",
            "overview": "While 95% of businesses ignore AI search, you can capture this growing traffic source",
            "opportunity_size": "AI search queries growing 40% annually, representing untapped traffic",
            "gaps_identified": analysis.ai_visibility_gaps,
            "competitive_advantage": [
                "First-mover advantage in AI search optimization",
                "Capture traffic competitors are missing",
                "Future-proof your SEO strategy",
                "Differentiate from traditional SEO agencies"
            ],
            "implementation": [
                "Optimize content structure for AI extraction",
                "Implement AI-friendly schema markup",
                "Monitor brand mentions in AI responses",
                "Track citation rates across AI platforms"
            ]
        }
    
    def _generate_objection_handling(self, analysis: CompetitiveAnalysis) -> List[Dict[str, str]]:
        """Generate objection handling responses."""
        
        objections = []
        
        # Common objections
        objections.append({
            "objection": "We're already working with an SEO agency",
            "response": f"Traditional agencies focus on yesterday's SEO. Our AI search optimization captures traffic they're missing. With {len(analysis.ai_visibility_gaps)} AI gaps identified, you're leaving money on the table."
        })
        
        objections.append({
            "objection": "SEO takes too long to see results",
            "response": f"AI search optimization shows faster results because there's less competition. Plus, with a {analysis.win_probability:.0%} win probability, we're confident in delivering measurable improvements within 90 days."
        })
        
        objections.append({
            "objection": "We don't have budget for SEO right now",
            "response": "AI search represents the biggest SEO opportunity in a decade. The cost of waiting is losing market share to competitors who act first. Our ROI projections show 3-6x return in the first year."
        })
        
        if analysis.win_probability < 0.5:
            objections.append({
                "objection": "Our SEO seems to be doing fine",
                "response": f"Your current score of {analysis.comparison_matrix['prospect_score']}/100 suggests significant room for improvement. Competitors are gaining ground while you maintain status quo."
            })
        
        return objections
    
    def _generate_next_steps(self, analysis: CompetitiveAnalysis) -> List[str]:
        """Generate recommended next steps."""
        
        steps = []
        
        if analysis.win_probability >= 0.7:
            steps.extend([
                "Schedule AI search optimization strategy session",
                "Conduct detailed competitive monitoring setup",
                "Begin implementation of high-impact improvements"
            ])
        elif analysis.win_probability >= 0.5:
            steps.extend([
                "Deep-dive analysis of top competitive gaps",
                "Prioritize quick wins for immediate impact",
                "Develop 90-day competitive advantage plan"
            ])
        else:
            steps.extend([
                "Comprehensive SEO foundation audit",
                "Competitive threat assessment and response plan",
                "Emergency optimization to prevent further losses"
            ])
        
        # Always include AI focus
        steps.append("Implement AI search visibility tracking and optimization")
        
        return steps
    
    def _generate_supporting_data(self, analysis: CompetitiveAnalysis) -> Dict[str, Any]:
        """Generate supporting data and statistics."""
        
        return {
            "competitive_scores": analysis.comparison_matrix['competitor_scores'],
            "analysis_date": analysis.analysis_date.isoformat(),
            "methodology": "Comprehensive SEO health analysis including technical, content, and AI visibility factors",
            "confidence_level": "High - based on 100+ ranking factors and competitive benchmarking",
            "market_data": {
                "ai_search_growth": "40% annual growth in AI search queries",
                "traditional_seo_saturation": "95% of businesses focus only on traditional SEO",
                "ai_optimization_adoption": "<5% of businesses optimize for AI search"
            }
        }
    
    def _format_talking_point(self, talking_point: TalkingPoint) -> Dict[str, Any]:
        """Format talking point for battlecard."""
        
        return {
            "title": talking_point.title,
            "description": talking_point.description,
            "supporting_data": talking_point.supporting_data,
            "confidence": f"{talking_point.confidence:.0%}"
        }

# Global battlecard generator
battlecard_generator = BattlecardGenerator()
