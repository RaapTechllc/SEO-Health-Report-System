"""
AEO Analysis Engine

Core engine implementing HubSpot's AEO (Answer Engine Optimization) methodology.
Orchestrates AI API queries, NLP analysis, competitive benchmarking, and scoring.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .query_ai_systems import (
    generate_test_queries, query_all_systems, AIResponse, TestQuery, QueryCategory
)
from .analyze_responses import (
    analyze_brand_presence, check_accuracy, analyze_sentiment, analyze_competitor_comparison
)


class AEOScore(Enum):
    """AEO score categories matching HubSpot methodology."""
    EXCELLENT = "A"  # 90-100
    GOOD = "B"       # 80-89
    FAIR = "C"       # 70-79
    POOR = "D"       # 60-69
    CRITICAL = "F"   # 0-59


@dataclass
class ShareOfVoice:
    """Share of voice metrics for competitive analysis."""
    brand_mentions: int
    total_mentions: int
    share_percentage: float
    rank: int
    competitors: Dict[str, int]


@dataclass
class AEOInsight:
    """Categorized insight from AEO analysis."""
    category: str  # "visibility", "accuracy", "sentiment", "competitive"
    priority: str  # "critical", "high", "medium", "low"
    title: str
    description: str
    recommendation: str
    impact: str  # Expected impact of fixing


@dataclass
class AEOResult:
    """Complete AEO analysis result."""
    overall_score: int
    grade: AEOScore
    component_scores: Dict[str, Dict[str, Any]]
    share_of_voice: ShareOfVoice
    insights: List[AEOInsight]
    query_performance: Dict[str, Any]
    execution_time_ms: int
    api_calls_made: int


class AEOEngine:
    """
    Core AEO analysis engine implementing HubSpot's methodology.
    
    Handles 100+ queries across multiple AI platforms, analyzes responses
    for brand positioning, calculates competitive metrics, and generates
    actionable recommendations.
    """
    
    def __init__(self, rate_limit_ms: int = 1000):
        """
        Initialize AEO engine.
        
        Args:
            rate_limit_ms: Milliseconds between API calls to avoid rate limits
        """
        self.rate_limit_ms = rate_limit_ms
        self.api_calls_made = 0
    
    async def analyze_brand(
        self,
        brand_name: str,
        products_services: List[str],
        competitors: Optional[List[str]] = None,
        ground_truth: Optional[Dict[str, Any]] = None,
        custom_queries: Optional[List[str]] = None,
        ai_systems: Optional[List[str]] = None
    ) -> AEOResult:
        """
        Run complete AEO analysis for a brand.
        
        Args:
            brand_name: Brand/company name to analyze
            products_services: List of key products/services (5-10 recommended)
            competitors: List of competitor names for benchmarking
            ground_truth: Known facts for accuracy checking
            custom_queries: Additional custom queries to test
            ai_systems: AI systems to query (default: all available)
            
        Returns:
            Complete AEOResult with scores, insights, and recommendations
        """
        start_time = time.time()
        competitors = competitors or []
        ground_truth = ground_truth or {}
        ai_systems = ai_systems or ["claude", "chatgpt", "perplexity", "gemini", "grok"]
        
        # Generate comprehensive test queries
        queries = generate_test_queries(
            brand_name=brand_name,
            products_services=products_services,
            competitors=competitors,
            custom_queries=custom_queries
        )
        
        # Query all AI systems
        responses = await query_all_systems(
            queries=queries,
            brand_name=brand_name,
            systems=ai_systems,
            rate_limit_ms=self.rate_limit_ms
        )
        
        # Count API calls made
        self.api_calls_made = sum(
            len([r for r in system_responses if not r.error])
            for system_responses in responses.values()
        )
        
        # Run component analyses
        presence_analysis = analyze_brand_presence(responses, brand_name, competitors)
        accuracy_analysis = check_accuracy(responses, ground_truth, brand_name)
        sentiment_analysis = analyze_sentiment(responses, brand_name)
        competitive_analysis = analyze_competitor_comparison(responses, brand_name, competitors)
        
        # Calculate share of voice
        share_of_voice = self._calculate_share_of_voice(
            responses, brand_name, competitors
        )
        
        # Generate component scores
        component_scores = {
            "ai_presence": presence_analysis,
            "response_accuracy": accuracy_analysis,
            "sentiment": sentiment_analysis,
            "competitive_position": {
                "score": self._calculate_competitive_score(competitive_analysis),
                "max": 15,
                "findings": competitive_analysis["findings"],
                "details": competitive_analysis["details"]
            }
        }
        
        # Calculate overall score (weighted)
        overall_score = self._calculate_overall_score(component_scores)
        grade = self._get_grade(overall_score)
        
        # Generate insights and recommendations
        insights = self._generate_insights(
            component_scores, share_of_voice, responses, brand_name, competitors
        )
        
        # Query performance metrics
        query_performance = self._analyze_query_performance(responses, queries)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return AEOResult(
            overall_score=overall_score,
            grade=grade,
            component_scores=component_scores,
            share_of_voice=share_of_voice,
            insights=insights,
            query_performance=query_performance,
            execution_time_ms=execution_time,
            api_calls_made=self.api_calls_made
        )
    
    def _calculate_share_of_voice(
        self, 
        responses: Dict[str, List[AIResponse]], 
        brand_name: str, 
        competitors: List[str]
    ) -> ShareOfVoice:
        """Calculate share of voice metrics."""
        mention_counts = {brand_name: 0}
        for competitor in competitors:
            mention_counts[competitor] = 0
        
        total_responses = 0
        
        for system_responses in responses.values():
            for response in system_responses:
                if response.error:
                    continue
                    
                total_responses += 1
                response_lower = response.response.lower()
                
                # Count brand mentions
                if brand_name.lower() in response_lower:
                    mention_counts[brand_name] += 1
                
                # Count competitor mentions
                for competitor in competitors:
                    if competitor.lower() in response_lower:
                        mention_counts[competitor] += 1
        
        # Calculate share and rank
        total_mentions = sum(mention_counts.values())
        brand_mentions = mention_counts[brand_name]
        
        share_percentage = (brand_mentions / total_mentions * 100) if total_mentions > 0 else 0
        
        # Rank by mentions (1 = most mentioned)
        sorted_counts = sorted(mention_counts.items(), key=lambda x: x[1], reverse=True)
        rank = next(
            (i + 1 for i, (name, _) in enumerate(sorted_counts) if name == brand_name),
            len(sorted_counts)
        )
        
        return ShareOfVoice(
            brand_mentions=brand_mentions,
            total_mentions=total_mentions,
            share_percentage=share_percentage,
            rank=rank,
            competitors={k: v for k, v in mention_counts.items() if k != brand_name}
        )
    
    def _calculate_competitive_score(self, competitive_analysis: Dict[str, Any]) -> int:
        """Calculate competitive positioning score (0-15)."""
        details = competitive_analysis["details"]
        rank = details["brand_rank"]
        total_competitors = len(details["mention_counts"])
        
        if rank == 1:
            return 15  # Leading position
        elif rank <= total_competitors * 0.25:
            return 12  # Top quartile
        elif rank <= total_competitors * 0.5:
            return 9   # Top half
        elif rank <= total_competitors * 0.75:
            return 6   # Third quartile
        else:
            return 3   # Bottom quartile
    
    def _calculate_overall_score(self, component_scores: Dict[str, Dict[str, Any]]) -> int:
        """Calculate weighted overall score matching HubSpot methodology."""
        # Weights based on HubSpot AEO importance
        weights = {
            "ai_presence": 0.35,      # Most important - visibility
            "response_accuracy": 0.25, # Critical for trust
            "sentiment": 0.20,        # Brand perception
            "competitive_position": 0.20  # Market position
        }
        
        weighted_score = 0
        total_weight = 0
        
        for component, weight in weights.items():
            if component in component_scores:
                score = component_scores[component]["score"]
                max_score = component_scores[component]["max"]
                normalized = (score / max_score) * 100 if max_score > 0 else 0
                weighted_score += normalized * weight
                total_weight += weight
        
        return int(weighted_score / total_weight) if total_weight > 0 else 0
    
    def _get_grade(self, score: int) -> AEOScore:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return AEOScore.EXCELLENT
        elif score >= 80:
            return AEOScore.GOOD
        elif score >= 70:
            return AEOScore.FAIR
        elif score >= 60:
            return AEOScore.POOR
        else:
            return AEOScore.CRITICAL
    
    def _generate_insights(
        self,
        component_scores: Dict[str, Dict[str, Any]],
        share_of_voice: ShareOfVoice,
        responses: Dict[str, List[AIResponse]],
        brand_name: str,
        competitors: List[str]
    ) -> List[AEOInsight]:
        """Generate prioritized insights and recommendations."""
        insights = []
        
        # AI Presence insights
        presence_score = component_scores["ai_presence"]["score"]
        if presence_score < 15:
            insights.append(AEOInsight(
                category="visibility",
                priority="critical" if presence_score < 10 else "high",
                title="Low AI Visibility",
                description=f"Brand mentioned in only {presence_score/25*100:.0f}% of AI responses",
                recommendation="Optimize content for AI consumption with structured data and clear brand mentions",
                impact="Increase brand visibility in AI-powered search results"
            ))
        
        # Accuracy insights
        accuracy_score = component_scores["response_accuracy"]["score"]
        accuracy_issues = component_scores["response_accuracy"].get("issues", [])
        if accuracy_issues:
            critical_issues = [i for i in accuracy_issues if i["severity"] == "critical"]
            if critical_issues:
                insights.append(AEOInsight(
                    category="accuracy",
                    priority="critical",
                    title="Critical Accuracy Issues",
                    description=f"AI systems spreading {len(critical_issues)} critical inaccuracies about your brand",
                    recommendation="Create authoritative content addressing these inaccuracies and submit corrections",
                    impact="Prevent misinformation from damaging brand reputation"
                ))
        
        # Sentiment insights
        sentiment_score = component_scores["sentiment"]["score"]
        if sentiment_score < 5:
            insights.append(AEOInsight(
                category="sentiment",
                priority="high",
                title="Negative Sentiment Detected",
                description="AI responses show predominantly negative sentiment about your brand",
                recommendation="Address negative issues and create positive content to improve brand perception",
                impact="Improve brand reputation in AI-generated responses"
            ))
        
        # Competitive insights
        if share_of_voice.rank > 3:
            top_competitor = max(share_of_voice.competitors.items(), key=lambda x: x[1])
            insights.append(AEOInsight(
                category="competitive",
                priority="medium",
                title="Low Competitive Visibility",
                description=f"Ranking #{share_of_voice.rank} in AI mentions. {top_competitor[0]} leads with {top_competitor[1]} mentions",
                recommendation="Increase content volume and optimize for competitor comparison queries",
                impact="Improve competitive positioning in AI responses"
            ))
        
        # Query performance insights
        failed_systems = []
        for system, system_responses in responses.items():
            error_rate = sum(1 for r in system_responses if r.error) / len(system_responses)
            if error_rate > 0.5:
                failed_systems.append(system)
        
        if failed_systems:
            insights.append(AEOInsight(
                category="technical",
                priority="medium",
                title="API Integration Issues",
                description=f"High error rates with {', '.join(failed_systems)} APIs",
                recommendation="Check API keys and rate limits for affected systems",
                impact="Ensure comprehensive AI visibility monitoring"
            ))
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        insights.sort(key=lambda x: priority_order[x.priority])
        
        return insights
    
    def _analyze_query_performance(
        self, 
        responses: Dict[str, List[AIResponse]], 
        queries: List[TestQuery]
    ) -> Dict[str, Any]:
        """Analyze query performance across systems and categories."""
        performance = {
            "total_queries": len(queries),
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_response_time_ms": 0,
            "system_performance": {},
            "category_performance": {}
        }
        
        total_time = 0
        successful_count = 0
        
        # System performance
        for system, system_responses in responses.items():
            successful = sum(1 for r in system_responses if not r.error)
            failed = sum(1 for r in system_responses if r.error)
            avg_time = sum(r.response_time_ms for r in system_responses if not r.error)
            avg_time = avg_time / successful if successful > 0 else 0
            
            performance["system_performance"][system] = {
                "successful": successful,
                "failed": failed,
                "success_rate": successful / (successful + failed) if (successful + failed) > 0 else 0,
                "avg_response_time_ms": int(avg_time)
            }
            
            total_time += sum(r.response_time_ms for r in system_responses if not r.error)
            successful_count += successful
        
        performance["successful_queries"] = successful_count
        performance["failed_queries"] = sum(
            len([r for r in responses if r.error]) for responses in responses.values()
        )
        performance["avg_response_time_ms"] = int(total_time / successful_count) if successful_count > 0 else 0
        
        # Category performance
        category_stats = {}
        for query in queries:
            cat = query.category.value
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "successful": 0}
            category_stats[cat]["total"] += len(responses)
            
            # Count successful responses for this query
            for system_responses in responses.values():
                matching_responses = [r for r in system_responses if r.query == query.query]
                category_stats[cat]["successful"] += sum(1 for r in matching_responses if not r.error)
        
        for cat, stats in category_stats.items():
            performance["category_performance"][cat] = {
                "success_rate": stats["successful"] / stats["total"] if stats["total"] > 0 else 0,
                "total_queries": stats["total"] // len(responses)  # Adjust for multiple systems
            }
        
        return performance


def run_aeo_analysis_sync(
    brand_name: str,
    products_services: List[str],
    competitors: Optional[List[str]] = None,
    ground_truth: Optional[Dict[str, Any]] = None,
    custom_queries: Optional[List[str]] = None,
    ai_systems: Optional[List[str]] = None,
    rate_limit_ms: int = 1000
) -> AEOResult:
    """
    Synchronous wrapper for AEO analysis.
    
    Args:
        brand_name: Brand/company name to analyze
        products_services: List of key products/services
        competitors: List of competitor names
        ground_truth: Known facts for accuracy checking
        custom_queries: Additional queries to test
        ai_systems: AI systems to query
        rate_limit_ms: Rate limiting between API calls
        
    Returns:
        Complete AEOResult
    """
    engine = AEOEngine(rate_limit_ms=rate_limit_ms)
    return asyncio.run(engine.analyze_brand(
        brand_name=brand_name,
        products_services=products_services,
        competitors=competitors,
        ground_truth=ground_truth,
        custom_queries=custom_queries,
        ai_systems=ai_systems
    ))


__all__ = [
    "AEOScore",
    "ShareOfVoice", 
    "AEOInsight",
    "AEOResult",
    "AEOEngine",
    "run_aeo_analysis_sync"
]