"""
Market Intelligence Module

Provides niche market analysis, competitor discovery, and industry benchmarking
for premium SEO reports. This is what separates a $500 report from a $5,000 one.
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from urllib.parse import urlparse

# Get model from environment (updated Jan 2026)
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

logger = logging.getLogger(__name__)


# =============================================================================
# INDUSTRY TAXONOMY
# =============================================================================

@dataclass
class IndustryClassification:
    """Hierarchical industry classification for precise niche targeting."""
    industry: str           # e.g., "Manufacturing"
    vertical: str           # e.g., "Metal Fabrication"
    niche: str              # e.g., "Custom Sheet Metal"
    sub_niche: str          # e.g., "Precision Sheet Metal - Midwest"
    geographic_scope: str   # "local", "regional", "national", "international"
    service_area: Optional[str] = None  # e.g., "Midwest USA", "California"
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0


INDUSTRY_TAXONOMY = {
    "Manufacturing": {
        "Metal Fabrication": {
            "niches": ["Custom Sheet Metal", "Precision Machining", "Welding Services", 
                      "Metal Stamping", "CNC Machining", "Laser Cutting"],
            "keywords": ["fabrication", "metal", "steel", "aluminum", "welding", "machining",
                        "sheet metal", "cnc", "laser", "stamping", "precision"]
        },
        "Industrial Equipment": {
            "niches": ["Heavy Machinery", "Industrial Automation", "Conveyor Systems",
                      "Material Handling", "Packaging Equipment"],
            "keywords": ["industrial", "equipment", "machinery", "automation", "conveyor"]
        },
        "Plastics & Composites": {
            "niches": ["Injection Molding", "Thermoforming", "Composite Manufacturing"],
            "keywords": ["plastic", "molding", "composite", "polymer", "injection"]
        }
    },
    "Professional Services": {
        "Legal": {
            "niches": ["Personal Injury", "Business Law", "Family Law", "Criminal Defense",
                      "Estate Planning", "Immigration", "Employment Law"],
            "keywords": ["attorney", "lawyer", "law firm", "legal", "litigation"]
        },
        "Accounting": {
            "niches": ["Tax Services", "Bookkeeping", "Audit", "CFO Services", "Payroll"],
            "keywords": ["cpa", "accountant", "tax", "bookkeeping", "audit", "financial"]
        },
        "Consulting": {
            "niches": ["Management Consulting", "IT Consulting", "HR Consulting", 
                      "Marketing Consulting", "Strategy Consulting"],
            "keywords": ["consulting", "consultant", "advisory", "strategy"]
        }
    },
    "Healthcare": {
        "Medical Practice": {
            "niches": ["Primary Care", "Specialty Care", "Urgent Care", "Telemedicine"],
            "keywords": ["doctor", "physician", "medical", "clinic", "healthcare", "patient"]
        },
        "Dental": {
            "niches": ["General Dentistry", "Cosmetic Dentistry", "Orthodontics", 
                      "Oral Surgery", "Pediatric Dentistry"],
            "keywords": ["dentist", "dental", "orthodontist", "teeth", "oral"]
        },
        "Mental Health": {
            "niches": ["Therapy", "Psychiatry", "Counseling", "Addiction Treatment"],
            "keywords": ["therapist", "counselor", "psychiatrist", "mental health", "therapy"]
        }
    },
    "Home Services": {
        "Construction": {
            "niches": ["General Contracting", "Remodeling", "New Construction", 
                      "Commercial Construction"],
            "keywords": ["contractor", "construction", "builder", "remodel", "renovation"]
        },
        "HVAC": {
            "niches": ["Residential HVAC", "Commercial HVAC", "HVAC Installation", 
                      "HVAC Repair"],
            "keywords": ["hvac", "heating", "cooling", "air conditioning", "furnace"]
        },
        "Plumbing": {
            "niches": ["Residential Plumbing", "Commercial Plumbing", "Emergency Plumbing",
                      "Drain Cleaning"],
            "keywords": ["plumber", "plumbing", "drain", "pipe", "water heater"]
        },
        "Electrical": {
            "niches": ["Residential Electrical", "Commercial Electrical", "Industrial Electrical"],
            "keywords": ["electrician", "electrical", "wiring", "panel", "lighting"]
        }
    },
    "Technology": {
        "Software Development": {
            "niches": ["Custom Software", "Web Development", "Mobile Apps", "SaaS",
                      "Enterprise Software"],
            "keywords": ["software", "developer", "programming", "app", "saas", "web"]
        },
        "IT Services": {
            "niches": ["Managed IT", "Cybersecurity", "Cloud Services", "IT Support"],
            "keywords": ["it services", "managed services", "cybersecurity", "cloud", "tech support"]
        },
        "Digital Marketing": {
            "niches": ["SEO Agency", "PPC Management", "Social Media Marketing", 
                      "Content Marketing"],
            "keywords": ["marketing", "seo", "ppc", "social media", "digital", "advertising"]
        }
    },
    "Real Estate": {
        "Residential": {
            "niches": ["Buyer's Agent", "Seller's Agent", "Luxury Real Estate", 
                      "First-Time Buyers"],
            "keywords": ["realtor", "real estate", "homes", "property", "housing"]
        },
        "Commercial": {
            "niches": ["Office Space", "Retail Space", "Industrial Real Estate", 
                      "Investment Properties"],
            "keywords": ["commercial real estate", "office", "retail", "industrial", "investment"]
        },
        "Property Management": {
            "niches": ["Residential Management", "Commercial Management", "HOA Management"],
            "keywords": ["property management", "landlord", "rental", "tenant"]
        }
    },
    "Food & Beverage": {
        "Restaurants": {
            "niches": ["Fine Dining", "Casual Dining", "Fast Casual", "QSR", "Catering"],
            "keywords": ["restaurant", "dining", "food", "chef", "cuisine", "catering"]
        },
        "Food Manufacturing": {
            "niches": ["Bakery", "Beverage Production", "Food Processing", "Specialty Foods"],
            "keywords": ["bakery", "food production", "beverage", "manufacturing"]
        }
    },
    "Financial Services": {
        "Banking": {
            "niches": ["Community Banking", "Credit Unions", "Commercial Banking"],
            "keywords": ["bank", "banking", "credit union", "loans", "deposits"]
        },
        "Insurance": {
            "niches": ["Life Insurance", "Health Insurance", "Property Insurance", 
                      "Commercial Insurance"],
            "keywords": ["insurance", "coverage", "policy", "claims", "underwriting"]
        },
        "Wealth Management": {
            "niches": ["Financial Planning", "Investment Management", "Retirement Planning"],
            "keywords": ["financial advisor", "wealth", "investment", "retirement", "portfolio"]
        }
    }
}


async def classify_industry(
    company_name: str,
    url: str,
    description: Optional[str] = None,
    products_services: Optional[List[str]] = None
) -> IndustryClassification:
    """
    Classify a company into the industry taxonomy using AI analysis.
    
    Returns detailed classification with industry, vertical, niche, and sub-niche.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Build context for classification
    context_parts = [f"Company: {company_name}", f"Website: {url}"]
    if description:
        context_parts.append(f"Description: {description}")
    if products_services:
        context_parts.append(f"Products/Services: {', '.join(products_services)}")
    
    context = "\n".join(context_parts)
    
    # Try AI classification first
    if api_key:
        try:
            classification = await _ai_classify_industry(context, company_name, url)
            if classification:
                return classification
        except Exception as e:
            logger.warning(f"AI classification failed: {e}")
    
    # Fallback to keyword-based classification
    return _keyword_classify_industry(company_name, url, description, products_services)


async def _ai_classify_industry(context: str, company_name: str, url: str) -> Optional[IndustryClassification]:
    """Use Claude to classify the company into the taxonomy."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    
    taxonomy_summary = json.dumps({
        industry: list(verticals.keys()) 
        for industry, verticals in INDUSTRY_TAXONOMY.items()
    }, indent=2)
    
    prompt = f"""Analyze this company and classify it into the most specific industry category possible.

{context}

Available Industries and Verticals:
{taxonomy_summary}

Respond with a JSON object containing:
{{
    "industry": "Top-level industry from the list",
    "vertical": "Specific vertical within that industry",
    "niche": "Most specific niche description (be very specific)",
    "sub_niche": "Even more specific if possible, include geographic focus",
    "geographic_scope": "local|regional|national|international",
    "service_area": "Geographic area served if identifiable",
    "keywords": ["list", "of", "relevant", "keywords"],
    "confidence": 0.0-1.0
}}

Be as specific as possible. For example:
- Not just "Manufacturing" but "Custom Sheet Metal Fabrication - Midwest Industrial"
- Not just "Legal" but "Personal Injury Law - Chicago Metro"

Return ONLY the JSON object, no other text."""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Parse JSON response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        data = json.loads(response_text)
        
        return IndustryClassification(
            industry=data.get("industry", "Unknown"),
            vertical=data.get("vertical", "Unknown"),
            niche=data.get("niche", "Unknown"),
            sub_niche=data.get("sub_niche", ""),
            geographic_scope=data.get("geographic_scope", "regional"),
            service_area=data.get("service_area"),
            keywords=data.get("keywords", []),
            confidence=data.get("confidence", 0.8)
        )
        
    except Exception as e:
        logger.error(f"AI industry classification failed: {e}")
        return None


def _keyword_classify_industry(
    company_name: str,
    url: str,
    description: Optional[str],
    products_services: Optional[List[str]]
) -> IndustryClassification:
    """Fallback keyword-based classification."""
    text = f"{company_name} {url} {description or ''} {' '.join(products_services or [])}".lower()
    
    best_match = None
    best_score = 0
    
    for industry, verticals in INDUSTRY_TAXONOMY.items():
        for vertical, data in verticals.items():
            keywords = data.get("keywords", [])
            score = sum(1 for kw in keywords if kw in text)
            
            if score > best_score:
                best_score = score
                niches = data.get("niches", [])
                best_match = IndustryClassification(
                    industry=industry,
                    vertical=vertical,
                    niche=niches[0] if niches else vertical,
                    sub_niche="",
                    geographic_scope="regional",
                    keywords=[kw for kw in keywords if kw in text],
                    confidence=min(0.9, score * 0.15)
                )
    
    return best_match or IndustryClassification(
        industry="Business Services",
        vertical="General",
        niche="General Business",
        sub_niche="",
        geographic_scope="regional",
        keywords=[],
        confidence=0.3
    )


# =============================================================================
# COMPETITOR DISCOVERY
# =============================================================================

@dataclass
class DiscoveredCompetitor:
    """A competitor discovered through market analysis."""
    name: str
    url: str
    description: str
    why_competitor: str  # Why they're a competitor
    estimated_strength: str  # "leader", "strong", "moderate", "emerging"
    geographic_overlap: str  # "direct", "partial", "national"
    service_overlap: List[str]  # Which services overlap
    ai_visibility_estimate: Optional[int] = None  # 0-100 estimate


@dataclass
class MarketLandscape:
    """Complete market landscape analysis."""
    classification: IndustryClassification
    market_size_estimate: str
    growth_trend: str  # "growing", "stable", "declining"
    competitors: List[DiscoveredCompetitor]
    market_leaders: List[str]
    emerging_players: List[str]
    key_differentiators: List[str]  # What differentiates leaders
    ai_visibility_opportunity: str  # Assessment of AI visibility opportunity
    analysis_date: datetime = field(default_factory=datetime.now)


async def discover_competitors(
    company_name: str,
    url: str,
    classification: IndustryClassification,
    products_services: List[str],
    location: Optional[str] = None,
    max_competitors: int = 10
) -> List[DiscoveredCompetitor]:
    """
    Discover competitors in the same niche using AI analysis.
    
    This is the key to premium reports - finding who's doing it better
    and showing the client exactly what they need to do to compete.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY - using limited competitor discovery")
        return []
    
    # Build detailed prompt for competitor discovery
    location_context = f" in {location}" if location else ""
    if classification.service_area:
        location_context = f" in {classification.service_area}"
    
    prompt = f"""You are a competitive intelligence analyst. Find the top competitors for this company.

COMPANY BEING ANALYZED:
- Name: {company_name}
- Website: {url}
- Industry: {classification.industry}
- Vertical: {classification.vertical}
- Niche: {classification.niche}
- Sub-niche: {classification.sub_niche}
- Geographic Scope: {classification.geographic_scope}
- Service Area: {classification.service_area or 'Not specified'}
- Products/Services: {', '.join(products_services)}

TASK: Identify {max_competitors} real competitors{location_context} that:
1. Operate in the EXACT same niche (not just same industry)
2. Compete for the same customers
3. Include a mix of: market leaders, direct competitors, and emerging threats

For each competitor, provide:
- Their actual company name and website URL
- Why they're a competitor
- Their estimated market strength
- Geographic overlap with the target company
- Which specific services overlap

IMPORTANT: 
- Be SPECIFIC to the niche. For "Custom Sheet Metal Fabrication in Midwest", don't list generic manufacturing companies.
- Include REAL companies with REAL websites (verify they exist)
- Focus on companies that would appear in the same Google searches
- Include both local/regional competitors AND national players who compete in this space

Respond with a JSON array:
[
    {{
        "name": "Company Name",
        "url": "https://example.com",
        "description": "Brief description of what they do",
        "why_competitor": "Specific reason they compete with target",
        "estimated_strength": "leader|strong|moderate|emerging",
        "geographic_overlap": "direct|partial|national",
        "service_overlap": ["service1", "service2"]
    }}
]

Return ONLY the JSON array, no other text."""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Parse JSON response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        competitors_data = json.loads(response_text)
        
        competitors = []
        for comp in competitors_data[:max_competitors]:
            competitors.append(DiscoveredCompetitor(
                name=comp.get("name", "Unknown"),
                url=comp.get("url", ""),
                description=comp.get("description", ""),
                why_competitor=comp.get("why_competitor", ""),
                estimated_strength=comp.get("estimated_strength", "moderate"),
                geographic_overlap=comp.get("geographic_overlap", "partial"),
                service_overlap=comp.get("service_overlap", [])
            ))
        
        return competitors
        
    except Exception as e:
        logger.error(f"Competitor discovery failed: {e}")
        return []


async def analyze_market_landscape(
    company_name: str,
    url: str,
    products_services: List[str],
    location: Optional[str] = None
) -> MarketLandscape:
    """
    Complete market landscape analysis including classification and competitor discovery.
    
    This is the foundation for premium competitive intelligence reports.
    """
    # Step 1: Classify the company
    classification = await classify_industry(
        company_name=company_name,
        url=url,
        products_services=products_services
    )
    
    # Step 2: Discover competitors
    competitors = await discover_competitors(
        company_name=company_name,
        url=url,
        classification=classification,
        products_services=products_services,
        location=location
    )
    
    # Step 3: Analyze the landscape
    market_leaders = [c.name for c in competitors if c.estimated_strength == "leader"]
    emerging_players = [c.name for c in competitors if c.estimated_strength == "emerging"]
    
    # Determine AI visibility opportunity
    if classification.industry in ["Technology", "Professional Services"]:
        ai_opportunity = "High - Tech-savvy audience actively uses AI search"
    elif classification.industry in ["Healthcare", "Financial Services"]:
        ai_opportunity = "Very High - Trust-based decisions increasingly influenced by AI"
    elif classification.industry in ["Manufacturing", "Home Services"]:
        ai_opportunity = "Moderate-High - B2B buyers researching via AI, early mover advantage"
    else:
        ai_opportunity = "Moderate - Growing AI search adoption in this sector"
    
    return MarketLandscape(
        classification=classification,
        market_size_estimate="Analysis required",  # Could integrate market data APIs
        growth_trend="stable",
        competitors=competitors,
        market_leaders=market_leaders,
        emerging_players=emerging_players,
        key_differentiators=[],  # Will be populated by competitive analysis
        ai_visibility_opportunity=ai_opportunity
    )


# =============================================================================
# COMPETITIVE BENCHMARKING
# =============================================================================

@dataclass
class CompetitorBenchmark:
    """Detailed benchmark comparison against a single competitor."""
    competitor_name: str
    competitor_url: str
    
    # Score comparisons
    overall_score_diff: int  # Positive = client ahead, negative = behind
    technical_score_diff: int
    content_score_diff: int
    ai_visibility_score_diff: int
    
    # Specific gaps
    strengths_vs_competitor: List[str]
    weaknesses_vs_competitor: List[str]
    
    # AI visibility specifics
    ai_mention_comparison: str  # "ahead", "behind", "tied"
    ai_sentiment_comparison: str
    
    # Actionable insights
    quick_wins: List[str]  # Things client can do immediately to gain ground
    strategic_investments: List[str]  # Longer-term improvements needed


@dataclass  
class MarketBenchmarkReport:
    """Complete market benchmark report for premium reports."""
    company_name: str
    classification: IndustryClassification
    
    # Market position
    market_position_rank: int  # 1 = leader
    market_position_percentile: int  # 0-100
    
    # Aggregate comparisons
    vs_market_leader: Optional[CompetitorBenchmark]
    vs_closest_competitor: Optional[CompetitorBenchmark]
    vs_market_average: Dict[str, int]  # score type -> difference
    
    # Individual benchmarks
    competitor_benchmarks: List[CompetitorBenchmark]
    
    # Strategic summary
    competitive_advantages: List[str]
    critical_gaps: List[str]
    market_opportunities: List[str]
    
    # AI-specific insights (our differentiator)
    ai_visibility_rank: int
    ai_visibility_gap_to_leader: int
    ai_optimization_priorities: List[str]


async def benchmark_against_competitors(
    client_audit: Dict[str, Any],
    competitor_audits: List[Dict[str, Any]],
    classification: IndustryClassification
) -> MarketBenchmarkReport:
    """
    Create comprehensive benchmark report comparing client to competitors.
    
    This is the premium analysis that justifies high-value reports.
    """
    company_name = client_audit.get("company_name", "Client")
    
    # Extract client scores
    client_overall = client_audit.get("overall_score", 0) or 0
    client_tech = client_audit.get("audits", {}).get("technical", {}).get("score", 0) or 0
    client_content = client_audit.get("audits", {}).get("content", {}).get("score", 0) or 0
    client_ai = client_audit.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0
    
    # Calculate market averages
    if competitor_audits:
        avg_overall = sum(c.get("overall_score", 0) or 0 for c in competitor_audits) / len(competitor_audits)
        avg_tech = sum((c.get("audits", {}).get("technical", {}).get("score", 0) or 0) for c in competitor_audits) / len(competitor_audits)
        avg_content = sum((c.get("audits", {}).get("content", {}).get("score", 0) or 0) for c in competitor_audits) / len(competitor_audits)
        avg_ai = sum((c.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0) for c in competitor_audits) / len(competitor_audits)
    else:
        avg_overall = avg_tech = avg_content = avg_ai = 50
    
    # Create individual benchmarks
    benchmarks = []
    for comp_audit in competitor_audits:
        comp_name = comp_audit.get("company_name", "Competitor")
        comp_url = comp_audit.get("url", "")
        
        comp_overall = comp_audit.get("overall_score", 0) or 0
        comp_tech = comp_audit.get("audits", {}).get("technical", {}).get("score", 0) or 0
        comp_content = comp_audit.get("audits", {}).get("content", {}).get("score", 0) or 0
        comp_ai = comp_audit.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0
        
        # Determine strengths and weaknesses
        strengths = []
        weaknesses = []
        quick_wins = []
        strategic = []
        
        if client_tech > comp_tech:
            strengths.append(f"Technical SEO ahead by {client_tech - comp_tech} points")
        elif client_tech < comp_tech:
            weaknesses.append(f"Technical SEO behind by {comp_tech - client_tech} points")
            if comp_tech - client_tech <= 10:
                quick_wins.append("Close technical gap with site speed and mobile optimization")
            else:
                strategic.append("Major technical overhaul needed - consider site rebuild")
        
        if client_content > comp_content:
            strengths.append(f"Content authority ahead by {client_content - comp_content} points")
        elif client_content < comp_content:
            weaknesses.append(f"Content authority behind by {comp_content - client_content} points")
            strategic.append("Develop comprehensive content strategy to build authority")
        
        if client_ai > comp_ai:
            strengths.append(f"AI visibility ahead by {client_ai - comp_ai} points")
        elif client_ai < comp_ai:
            weaknesses.append(f"AI visibility behind by {comp_ai - client_ai} points")
            quick_wins.append("Implement schema markup and structured data")
            quick_wins.append("Create AI-optimized FAQ content")
        
        # AI comparison
        ai_comparison = "ahead" if client_ai > comp_ai else "behind" if client_ai < comp_ai else "tied"
        
        benchmarks.append(CompetitorBenchmark(
            competitor_name=comp_name,
            competitor_url=comp_url,
            overall_score_diff=client_overall - comp_overall,
            technical_score_diff=client_tech - comp_tech,
            content_score_diff=client_content - comp_content,
            ai_visibility_score_diff=client_ai - comp_ai,
            strengths_vs_competitor=strengths,
            weaknesses_vs_competitor=weaknesses,
            ai_mention_comparison=ai_comparison,
            ai_sentiment_comparison="neutral",  # Would need deeper analysis
            quick_wins=quick_wins,
            strategic_investments=strategic
        ))
    
    # Sort to find leader and closest competitor
    all_scores = [(client_overall, "client")] + [
        (c.get("overall_score", 0) or 0, c.get("company_name", "Competitor"))
        for c in competitor_audits
    ]
    all_scores.sort(reverse=True)
    
    # Calculate rank
    rank = next(i + 1 for i, (score, name) in enumerate(all_scores) if name == "client")
    percentile = int(100 * (len(all_scores) - rank) / len(all_scores)) if all_scores else 50
    
    # Find leader and closest competitor benchmarks
    leader_benchmark = None
    closest_benchmark = None
    
    if benchmarks:
        # Leader is the one with highest overall score
        sorted_benchmarks = sorted(benchmarks, key=lambda b: -b.overall_score_diff)
        if sorted_benchmarks and sorted_benchmarks[-1].overall_score_diff < 0:
            leader_benchmark = sorted_benchmarks[-1]
        
        # Closest is smallest absolute difference
        closest_benchmark = min(benchmarks, key=lambda b: abs(b.overall_score_diff))
    
    # AI visibility rank
    ai_scores = [(client_ai, "client")] + [
        (c.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0, c.get("company_name", ""))
        for c in competitor_audits
    ]
    ai_scores.sort(reverse=True)
    ai_rank = next(i + 1 for i, (score, name) in enumerate(ai_scores) if name == "client")
    ai_gap_to_leader = ai_scores[0][0] - client_ai if ai_scores else 0
    
    # Generate strategic insights
    advantages = []
    gaps = []
    opportunities = []
    ai_priorities = []
    
    if client_overall > avg_overall:
        advantages.append(f"Overall SEO performance {client_overall - avg_overall:.0f} points above market average")
    else:
        gaps.append(f"Overall SEO performance {avg_overall - client_overall:.0f} points below market average")
    
    if client_ai < avg_ai:
        gaps.append(f"AI visibility {avg_ai - client_ai:.0f} points below competitors - critical gap")
        ai_priorities.append("Implement comprehensive AI optimization strategy")
        ai_priorities.append("Add structured data and schema markup")
        ai_priorities.append("Create content optimized for AI citation")
    elif client_ai > avg_ai:
        advantages.append(f"AI visibility {client_ai - avg_ai:.0f} points ahead of competitors")
    
    if ai_rank > 1:
        opportunities.append(f"Closing AI visibility gap could move from #{ai_rank} to market leader")
    
    return MarketBenchmarkReport(
        company_name=company_name,
        classification=classification,
        market_position_rank=rank,
        market_position_percentile=percentile,
        vs_market_leader=leader_benchmark,
        vs_closest_competitor=closest_benchmark,
        vs_market_average={
            "overall": int(client_overall - avg_overall),
            "technical": int(client_tech - avg_tech),
            "content": int(client_content - avg_content),
            "ai_visibility": int(client_ai - avg_ai)
        },
        competitor_benchmarks=benchmarks,
        competitive_advantages=advantages,
        critical_gaps=gaps,
        market_opportunities=opportunities,
        ai_visibility_rank=ai_rank,
        ai_visibility_gap_to_leader=int(ai_gap_to_leader),
        ai_optimization_priorities=ai_priorities
    )


# =============================================================================
# PREMIUM EXECUTIVE SUMMARY GENERATION
# =============================================================================

async def generate_premium_executive_summary(
    client_audit: Dict[str, Any],
    benchmark_report: MarketBenchmarkReport,
    market_landscape: MarketLandscape
) -> str:
    """
    Generate a premium executive summary that justifies high-value reports.
    
    This is multi-paragraph strategic analysis, not a 3-sentence overview.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    company_name = client_audit.get("company_name", "Your Company")
    overall_score = client_audit.get("overall_score", 0) or 0
    grade = client_audit.get("grade", "N/A")
    
    # Build comprehensive context
    context = f"""
COMPANY: {company_name}
INDUSTRY: {market_landscape.classification.industry} > {market_landscape.classification.vertical} > {market_landscape.classification.niche}
SUB-NICHE: {market_landscape.classification.sub_niche}
GEOGRAPHIC SCOPE: {market_landscape.classification.geographic_scope}
SERVICE AREA: {market_landscape.classification.service_area or 'Not specified'}

SCORES:
- Overall: {overall_score}/100 (Grade: {grade})
- Technical SEO: {client_audit.get('audits', {}).get('technical', {}).get('score', 0)}/100
- Content Authority: {client_audit.get('audits', {}).get('content', {}).get('score', 0)}/100
- AI Visibility: {client_audit.get('audits', {}).get('ai_visibility', {}).get('score', 0)}/100

MARKET POSITION:
- Rank: #{benchmark_report.market_position_rank} of {len(benchmark_report.competitor_benchmarks) + 1} analyzed
- Percentile: {benchmark_report.market_position_percentile}th
- AI Visibility Rank: #{benchmark_report.ai_visibility_rank}
- Gap to AI Leader: {benchmark_report.ai_visibility_gap_to_leader} points

VS MARKET AVERAGE:
- Overall: {benchmark_report.vs_market_average.get('overall', 0):+d} points
- Technical: {benchmark_report.vs_market_average.get('technical', 0):+d} points
- Content: {benchmark_report.vs_market_average.get('content', 0):+d} points
- AI Visibility: {benchmark_report.vs_market_average.get('ai_visibility', 0):+d} points

COMPETITIVE ADVANTAGES:
{chr(10).join('- ' + a for a in benchmark_report.competitive_advantages) or '- None identified'}

CRITICAL GAPS:
{chr(10).join('- ' + g for g in benchmark_report.critical_gaps) or '- None identified'}

MARKET OPPORTUNITIES:
{chr(10).join('- ' + o for o in benchmark_report.market_opportunities) or '- None identified'}

TOP COMPETITORS:
{chr(10).join('- ' + c.name + ' (' + c.estimated_strength + ')' for c in market_landscape.competitors[:5])}

AI VISIBILITY OPPORTUNITY: {market_landscape.ai_visibility_opportunity}
"""

    if not api_key:
        # Fallback to template-based summary
        return _generate_template_summary(client_audit, benchmark_report, market_landscape)
    
    prompt = f"""You are a senior SEO strategist writing an executive summary for a C-level audience.
This report will be used to justify a $2,000-$10,000 SEO engagement.

Write a comprehensive executive summary (4-6 paragraphs) that:

1. OPENING: State the company's current market position clearly and directly
2. COMPETITIVE CONTEXT: Compare to specific competitors and market leaders
3. KEY FINDINGS: Highlight the most important discoveries (good and bad)
4. AI VISIBILITY FOCUS: Emphasize AI search visibility as the emerging battleground
5. STRATEGIC RECOMMENDATIONS: Prioritized actions with expected impact
6. CLOSING: Clear call to action with urgency

CONTEXT:
{context}

REQUIREMENTS:
- Write for a CEO/CMO audience - strategic, not technical
- Be specific with numbers and competitor names
- Frame everything in terms of business impact (leads, revenue, market share)
- Emphasize AI visibility as the differentiator (most competitors aren't optimizing for this)
- Include 2-3 specific quick wins they can implement immediately
- End with a compelling reason to act now

Use professional but accessible language. No jargon without explanation.
Use bullet points sparingly - this should read as strategic narrative.

Write the executive summary now:"""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text.strip()
        
    except Exception as e:
        logger.error(f"Premium summary generation failed: {e}")
        return _generate_template_summary(client_audit, benchmark_report, market_landscape)


def _generate_template_summary(
    client_audit: Dict[str, Any],
    benchmark_report: MarketBenchmarkReport,
    market_landscape: MarketLandscape
) -> str:
    """Fallback template-based summary when AI is unavailable."""
    company_name = client_audit.get("company_name", "Your Company")
    overall_score = client_audit.get("overall_score", 0) or 0
    grade = client_audit.get("grade", "N/A")
    
    rank = benchmark_report.market_position_rank
    total = len(benchmark_report.competitor_benchmarks) + 1
    ai_score = client_audit.get('audits', {}).get('ai_visibility', {}).get('score', 0) or 0
    ai_gap = benchmark_report.ai_visibility_gap_to_leader
    
    position_text = "leading" if rank == 1 else "competitive" if rank <= 3 else "trailing"
    
    summary = f"""{company_name} currently holds a {position_text} position in the {market_landscape.classification.niche} market, ranking #{rank} out of {total} competitors analyzed. With an overall SEO health score of {overall_score}/100 (Grade: {grade}), there are clear opportunities for improvement.

The most significant finding is in AI visibility, where {company_name} scores {ai_score}/100. """
    
    if ai_gap > 0:
        summary += f"This represents a {ai_gap}-point gap to the market leader. As AI-powered search (ChatGPT, Claude, Perplexity) continues to grow, this gap translates directly to missed leads and revenue."
    else:
        summary += "This positions the company well for the growing AI search landscape, though maintaining this advantage requires ongoing optimization."
    
    summary += f"""

Key competitive advantages include: {', '.join(benchmark_report.competitive_advantages[:2]) if benchmark_report.competitive_advantages else 'technical foundation that can be built upon'}. However, critical gaps exist in: {', '.join(benchmark_report.critical_gaps[:2]) if benchmark_report.critical_gaps else 'content depth and AI optimization'}.

Recommended immediate actions:
1. Implement structured data markup to improve AI parseability
2. Create FAQ content targeting common industry questions
3. Optimize existing content for AI citation likelihood

The window for AI visibility optimization is now - competitors who move first will establish lasting advantages in this emerging channel."""
    
    return summary


# =============================================================================
# SYNC WRAPPERS
# =============================================================================

def classify_industry_sync(
    company_name: str,
    url: str,
    description: Optional[str] = None,
    products_services: Optional[List[str]] = None
) -> IndustryClassification:
    """Sync wrapper for classify_industry."""
    return asyncio.run(classify_industry(company_name, url, description, products_services))


def discover_competitors_sync(
    company_name: str,
    url: str,
    classification: IndustryClassification,
    products_services: List[str],
    location: Optional[str] = None,
    max_competitors: int = 10
) -> List[DiscoveredCompetitor]:
    """Sync wrapper for discover_competitors."""
    return asyncio.run(discover_competitors(
        company_name, url, classification, products_services, location, max_competitors
    ))


def analyze_market_landscape_sync(
    company_name: str,
    url: str,
    products_services: List[str],
    location: Optional[str] = None
) -> MarketLandscape:
    """Sync wrapper for analyze_market_landscape."""
    return asyncio.run(analyze_market_landscape(company_name, url, products_services, location))


def benchmark_against_competitors_sync(
    client_audit: Dict[str, Any],
    competitor_audits: List[Dict[str, Any]],
    classification: IndustryClassification
) -> MarketBenchmarkReport:
    """Sync wrapper for benchmark_against_competitors."""
    return asyncio.run(benchmark_against_competitors(client_audit, competitor_audits, classification))


def generate_premium_executive_summary_sync(
    client_audit: Dict[str, Any],
    benchmark_report: MarketBenchmarkReport,
    market_landscape: MarketLandscape
) -> str:
    """Sync wrapper for generate_premium_executive_summary."""
    return asyncio.run(generate_premium_executive_summary(client_audit, benchmark_report, market_landscape))


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Data classes
    'IndustryClassification',
    'DiscoveredCompetitor', 
    'MarketLandscape',
    'CompetitorBenchmark',
    'MarketBenchmarkReport',
    
    # Taxonomy
    'INDUSTRY_TAXONOMY',
    
    # Async functions
    'classify_industry',
    'discover_competitors',
    'analyze_market_landscape',
    'benchmark_against_competitors',
    'generate_premium_executive_summary',
    
    # Sync wrappers
    'classify_industry_sync',
    'discover_competitors_sync',
    'analyze_market_landscape_sync',
    'benchmark_against_competitors_sync',
    'generate_premium_executive_summary_sync',
]
