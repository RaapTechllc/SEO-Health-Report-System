from typing import Dict, Any, List
import logging
from datetime import datetime

class PricingIntelligence:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Market pricing data (would be updated from real market research)
        self.market_rates = {
            "traditional_seo_agency": {
                "monthly_retainer": {"min": 3000, "max": 15000, "avg": 8000},
                "one_time_audit": {"min": 2000, "max": 10000, "avg": 5000},
                "hourly_rate": {"min": 150, "max": 400, "avg": 250}
            },
            "ai_seo_specialist": {
                "monthly_retainer": {"min": 2000, "max": 8000, "avg": 4500},
                "one_time_audit": {"min": 1500, "max": 5000, "avg": 2500},
                "hourly_rate": {"min": 200, "max": 500, "avg": 350}
            },
            "enterprise_platform": {
                "monthly_subscription": {"min": 500, "max": 5000, "avg": 2000},
                "setup_fee": {"min": 1000, "max": 10000, "avg": 3000}
            }
        }
    
    def analyze_pricing_opportunity(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pricing opportunity based on competitive analysis."""
        
        try:
            prospect_score = analysis_data.get('comparison_matrix', {}).get('prospect_score', 0)
            win_probability = analysis_data.get('win_probability', 0.5)
            ai_gaps = analysis_data.get('ai_visibility_gaps', [])
            
            # Determine pricing tier based on analysis
            pricing_tier = self._determine_pricing_tier(prospect_score, win_probability, ai_gaps)
            
            # Calculate value proposition
            value_prop = self._calculate_value_proposition(prospect_score, ai_gaps)
            
            # Generate pricing recommendations
            pricing_recommendations = self._generate_pricing_recommendations(pricing_tier, value_prop)
            
            # ROI projections
            roi_projections = self._calculate_roi_projections(prospect_score, ai_gaps)
            
            return {
                "pricing_tier": pricing_tier,
                "value_proposition": value_prop,
                "pricing_recommendations": pricing_recommendations,
                "roi_projections": roi_projections,
                "competitive_positioning": self._get_competitive_positioning(),
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Pricing analysis failed: {e}")
            raise
    
    def _determine_pricing_tier(self, prospect_score: int, win_probability: float, ai_gaps: List[str]) -> str:
        """Determine appropriate pricing tier."""
        
        # High-value prospects (strong position, high win probability)
        if prospect_score >= 80 and win_probability >= 0.7:
            return "premium"
        
        # Medium-value prospects (competitive position)
        elif prospect_score >= 60 and win_probability >= 0.5:
            return "standard"
        
        # High-opportunity prospects (low score but high upside)
        elif prospect_score < 60 and len(ai_gaps) >= 3:
            return "opportunity"
        
        # Standard prospects
        else:
            return "standard"
    
    def _calculate_value_proposition(self, prospect_score: int, ai_gaps: List[str]) -> Dict[str, Any]:
        """Calculate value proposition metrics."""
        
        # Potential score improvement
        if prospect_score < 60:
            potential_improvement = 40  # High upside
        elif prospect_score < 80:
            potential_improvement = 25  # Medium upside
        else:
            potential_improvement = 15  # Optimization upside
        
        # AI opportunity value
        ai_opportunity_value = len(ai_gaps) * 5000  # $5K per gap addressed
        
        # Traditional agency comparison
        agency_cost_annual = self.market_rates["traditional_seo_agency"]["monthly_retainer"]["avg"] * 12
        our_cost_annual = 2000 * 12  # Our platform cost
        cost_savings = agency_cost_annual - our_cost_annual
        
        return {
            "potential_score_improvement": potential_improvement,
            "ai_opportunity_value": ai_opportunity_value,
            "annual_cost_savings": cost_savings,
            "total_value": ai_opportunity_value + cost_savings,
            "payback_period_months": 3  # Typical payback period
        }
    
    def _generate_pricing_recommendations(self, tier: str, value_prop: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pricing recommendations by tier."""
        
        base_pricing = {
            "premium": {
                "setup_fee": 5000,
                "monthly_fee": 3000,
                "description": "Premium AI SEO optimization with dedicated support"
            },
            "standard": {
                "setup_fee": 2500,
                "monthly_fee": 1500,
                "description": "Comprehensive AI SEO platform with standard support"
            },
            "opportunity": {
                "setup_fee": 1500,
                "monthly_fee": 1000,
                "description": "High-opportunity optimization with growth pricing"
            }
        }
        
        pricing = base_pricing.get(tier, base_pricing["standard"])
        
        # Add value-based adjustments
        if value_prop["ai_opportunity_value"] > 20000:
            pricing["monthly_fee"] = int(pricing["monthly_fee"] * 1.2)
            pricing["value_justification"] = "High AI opportunity value warrants premium pricing"
        
        # Calculate annual totals
        pricing["annual_total"] = pricing["setup_fee"] + (pricing["monthly_fee"] * 12)
        pricing["roi_multiple"] = value_prop["total_value"] / pricing["annual_total"]
        
        return pricing
    
    def _calculate_roi_projections(self, prospect_score: int, ai_gaps: List[str]) -> Dict[str, Any]:
        """Calculate ROI projections."""
        
        # Traffic improvement estimates
        if prospect_score < 60:
            traffic_improvement = 0.5  # 50% improvement
        elif prospect_score < 80:
            traffic_improvement = 0.3  # 30% improvement
        else:
            traffic_improvement = 0.2  # 20% improvement
        
        # AI traffic opportunity (new traffic source)
        ai_traffic_opportunity = len(ai_gaps) * 0.1  # 10% per gap
        
        # Revenue projections (assuming $100 average order value, 2% conversion)
        monthly_visitors = 10000  # Assumed baseline
        current_revenue = monthly_visitors * 0.02 * 100 * 12  # Annual
        
        improved_revenue = (monthly_visitors * (1 + traffic_improvement + ai_traffic_opportunity)) * 0.02 * 100 * 12
        revenue_increase = improved_revenue - current_revenue
        
        return {
            "traffic_improvement_percent": traffic_improvement * 100,
            "ai_traffic_opportunity_percent": ai_traffic_opportunity * 100,
            "current_annual_revenue": current_revenue,
            "projected_annual_revenue": improved_revenue,
            "annual_revenue_increase": revenue_increase,
            "roi_timeline": {
                "3_months": revenue_increase * 0.25,
                "6_months": revenue_increase * 0.5,
                "12_months": revenue_increase
            }
        }
    
    def _get_competitive_positioning(self) -> Dict[str, Any]:
        """Get competitive positioning vs alternatives."""
        
        return {
            "vs_traditional_agency": {
                "cost_comparison": "60-75% less expensive than traditional agencies",
                "speed_advantage": "Real-time monitoring vs quarterly reports",
                "ai_advantage": "AI search optimization not offered by traditional agencies"
            },
            "vs_diy_tools": {
                "expertise_advantage": "Expert analysis vs raw data",
                "time_savings": "Automated insights vs manual analysis",
                "comprehensive_coverage": "All-in-one platform vs multiple tools"
            },
            "vs_enterprise_platforms": {
                "cost_advantage": "Fraction of enterprise platform costs",
                "ai_focus": "Specialized AI search optimization",
                "personalized_service": "Dedicated support vs self-service"
            }
        }

# Global pricing intelligence
pricing_intel = PricingIntelligence()
