# Competitive Intelligence Package
# Automated competitive analysis and battlecard generation

try:
    from .market_intelligence import (
        # Data classes
        IndustryClassification,
        DiscoveredCompetitor,
        MarketLandscape,
        CompetitorBenchmark,
        MarketBenchmarkReport,
        
        # Taxonomy
        INDUSTRY_TAXONOMY,
        
        # Async functions
        classify_industry,
        discover_competitors,
        analyze_market_landscape,
        benchmark_against_competitors,
        generate_premium_executive_summary,
        
        # Sync wrappers
        classify_industry_sync,
        discover_competitors_sync,
        analyze_market_landscape_sync,
        benchmark_against_competitors_sync,
        generate_premium_executive_summary_sync,
    )
    HAS_MARKET_INTEL = True
except ImportError as e:
    print(f"Warning: Market intelligence module not available: {e}")
    HAS_MARKET_INTEL = False

from .analyzer import CompetitiveAnalyzer, analyzer
from .gap_analyzer import GapAnalyzer, gap_analyzer
from .models import CompetitiveAnalysis, ComparisonMatrix, TalkingPoint

__all__ = [
    # Existing exports
    'CompetitiveAnalyzer',
    'analyzer',
    'GapAnalyzer',
    'gap_analyzer',
    'CompetitiveAnalysis',
    'ComparisonMatrix',
    'TalkingPoint',
    'HAS_MARKET_INTEL',
]

# Add market intelligence exports if available
if HAS_MARKET_INTEL:
    __all__.extend([
        'IndustryClassification',
        'DiscoveredCompetitor',
        'MarketLandscape',
        'CompetitorBenchmark',
        'MarketBenchmarkReport',
        'INDUSTRY_TAXONOMY',
        'classify_industry',
        'discover_competitors',
        'analyze_market_landscape',
        'benchmark_against_competitors',
        'generate_premium_executive_summary',
        'classify_industry_sync',
        'discover_competitors_sync',
        'analyze_market_landscape_sync',
        'benchmark_against_competitors_sync',
        'generate_premium_executive_summary_sync',
    ])
