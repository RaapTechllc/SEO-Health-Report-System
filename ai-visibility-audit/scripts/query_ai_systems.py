"""
Query AI Systems

Generate test queries and query multiple AI systems (Claude, ChatGPT, Perplexity)
to assess brand visibility.
"""

import os
import sys
import json
import time
import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent directory to path for config import
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

try:
    from seo_health_report.config import get_config
except ImportError:
    # Fallback for testing
    try:
        from mock_config import get_config
    except ImportError:
        def get_config():
            class MockConfig:
                anthropic_model = "claude-3-sonnet-20240229"
            return MockConfig()

# Cache imports with fallback
try:
    from seo_health_report.scripts.cache import cached, TTL_AI_RESPONSE

    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False

    def cached(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    TTL_AI_RESPONSE = 0

# Get config for model name
_config = get_config()
ANTHROPIC_MODEL = _config.anthropic_model


class QueryCategory(Enum):
    """Categories of test queries for comprehensive coverage."""

    BRAND = "brand"
    PRODUCT = "product"
    PROBLEM = "problem"
    COMPARISON = "comparison"
    REPUTATION = "reputation"


@dataclass
class TestQuery:
    """A test query to send to AI systems."""

    query: str
    category: QueryCategory
    expected_brand_mention: bool = True
    competitors_mentioned: List[str] = None

    def __post_init__(self):
        if self.competitors_mentioned is None:
            self.competitors_mentioned = []


@dataclass
class AIResponse:
    """Response from an AI system."""

    query: str
    system: str
    response: str
    brand_mentioned: bool
    mention_count: int
    position: Optional[str]  # "first", "middle", "last", None
    sentiment: Optional[str]  # "positive", "neutral", "negative"
    competitors_mentioned: List[str]
    response_time_ms: int
    error: Optional[str] = None


def generate_test_queries(
    brand_name: str,
    products_services: List[str],
    competitors: Optional[List[str]] = None,
    custom_queries: Optional[List[str]] = None,
) -> List[TestQuery]:
    """
    Generate a comprehensive set of test queries for AI visibility assessment.

    Args:
        brand_name: The brand/company name to test
        products_services: List of key products or services (5-10 recommended)
        competitors: Optional list of competitor names for comparison queries
        custom_queries: Optional list of additional custom queries

    Returns:
        List of TestQuery objects ready for testing
    """
    queries = []
    competitors = competitors or []

    # Brand queries - direct brand awareness
    brand_templates = [
        f"What is {brand_name}?",
        f"Tell me about {brand_name}",
        f"{brand_name} company overview",
        f"Who founded {brand_name}?",
        f"What does {brand_name} do?",
    ]

    for template in brand_templates:
        queries.append(
            TestQuery(
                query=template,
                category=QueryCategory.BRAND,
                expected_brand_mention=True,
            )
        )

    # Product/service queries - category presence
    for product in products_services[:5]:  # Limit to top 5
        product_templates = [
            f"Best {product} options",
            f"Top {product} providers",
            f"What is the best {product}?",
            f"{product} recommendations",
        ]
        for template in product_templates:
            queries.append(
                TestQuery(
                    query=template,
                    category=QueryCategory.PRODUCT,
                    expected_brand_mention=True,
                    competitors_mentioned=competitors,
                )
            )

    # Problem queries - solution awareness
    problem_templates = [
        f"How to choose a {products_services[0]} provider",
        f"What to look for in {products_services[0]}",
        f"Problems with {products_services[0]}",
    ]

    for template in problem_templates:
        queries.append(
            TestQuery(
                query=template,
                category=QueryCategory.PROBLEM,
                expected_brand_mention=True,
            )
        )

    # Comparison queries - competitive positioning
    for competitor in competitors[:3]:  # Limit to top 3
        comparison_templates = [
            f"{brand_name} vs {competitor}",
            f"Compare {brand_name} and {competitor}",
            f"Is {brand_name} better than {competitor}?",
        ]
        for template in comparison_templates:
            queries.append(
                TestQuery(
                    query=template,
                    category=QueryCategory.COMPARISON,
                    expected_brand_mention=True,
                    competitors_mentioned=[competitor],
                )
            )

    # Reputation queries - sentiment assessment
    reputation_templates = [
        f"{brand_name} reviews",
        f"Is {brand_name} good?",
        f"{brand_name} complaints",
        f"{brand_name} customer experience",
    ]

    for template in reputation_templates:
        queries.append(
            TestQuery(
                query=template,
                category=QueryCategory.REPUTATION,
                expected_brand_mention=True,
            )
        )

    # Add custom queries if provided
    if custom_queries:
        for query in custom_queries:
            queries.append(
                TestQuery(
                    query=query,
                    category=QueryCategory.BRAND,
                    expected_brand_mention=True,
                )
            )

    return queries


@cached("ai_responses", TTL_AI_RESPONSE)
async def query_claude(
    query: str, brand_name: str, api_key: Optional[str] = None
) -> AIResponse:
    """
    Query Claude (Anthropic) API.

    Args:
        query: The query to send
        brand_name: Brand name to check for mentions
        api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)

    Returns:
        AIResponse with results
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return AIResponse(
            query=query,
            system="claude",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error="ANTHROPIC_API_KEY not set",
        )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        start_time = time.time()

        # Run blocking API call in thread pool
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": query}],
            ),
        )

        response_time = int((time.time() - start_time) * 1000)
        response_text = message.content[0].text

        # Analyze the response
        brand_lower = brand_name.lower()
        response_lower = response_text.lower()

        brand_mentioned = brand_lower in response_lower
        mention_count = response_lower.count(brand_lower)

        # Determine position of first mention
        position = None
        if brand_mentioned:
            first_mention = response_lower.find(brand_lower)
            response_len = len(response_text)
            if first_mention < response_len * 0.25:
                position = "first"
            elif first_mention < response_len * 0.75:
                position = "middle"
            else:
                position = "last"

        return AIResponse(
            query=query,
            system="claude",
            response=response_text,
            brand_mentioned=brand_mentioned,
            mention_count=mention_count,
            position=position,
            sentiment=None,  # Will be analyzed separately
            competitors_mentioned=[],  # Will be analyzed separately
            response_time_ms=response_time,
        )

    except ImportError:
        return AIResponse(
            query=query,
            system="claude",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error="anthropic package not installed. Run: pip install anthropic",
        )
    except Exception as e:
        return AIResponse(
            query=query,
            system="claude",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error=str(e),
        )


@cached("ai_responses", TTL_AI_RESPONSE)
async def query_openai(
    query: str, brand_name: str, api_key: Optional[str] = None
) -> AIResponse:
    """
    Query OpenAI (ChatGPT) API.

    Args:
        query: The query to send
        brand_name: Brand name to check for mentions
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)

    Returns:
        AIResponse with results
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return AIResponse(
            query=query,
            system="chatgpt",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error="OPENAI_API_KEY not set",
        )

    try:
        import httpx

        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": query}],
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
            )
            response.raise_for_status()
            result = response.json()

        response_time = int((time.time() - start_time) * 1000)
        response_text = result["choices"][0]["message"]["content"]

        # Analyze the response
        brand_lower = brand_name.lower()
        response_lower = response_text.lower()

        brand_mentioned = brand_lower in response_lower
        mention_count = response_lower.count(brand_lower)

        # Determine position of first mention
        position = None
        if brand_mentioned:
            first_mention = response_lower.find(brand_lower)
            response_len = len(response_text)
            if first_mention < response_len * 0.25:
                position = "first"
            elif first_mention < response_len * 0.75:
                position = "middle"
            else:
                position = "last"

        return AIResponse(
            query=query,
            system="chatgpt",
            response=response_text,
            brand_mentioned=brand_mentioned,
            mention_count=mention_count,
            position=position,
            sentiment=None,  # Will be analyzed separately
            competitors_mentioned=[],  # Will be analyzed separately
            response_time_ms=response_time,
        )

    except ImportError:
        return AIResponse(
            query=query,
            system="chatgpt",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error="httpx package not installed. Run: pip install httpx",
        )
    except Exception as e:
        return AIResponse(
            query=query,
            system="chatgpt",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error=str(e),
        )


@cached("ai_responses", TTL_AI_RESPONSE)
async def query_xai(
    query: str, brand_name: str, api_key: Optional[str] = None
) -> AIResponse:
    """
    Query xAI (Grok) API.

    xAI's Grok has access to real-time X/Twitter data, making it valuable for
    brand visibility analysis on social platforms.

    Args:
        query: The query to send
        brand_name: Brand name to check for mentions
        api_key: xAI API key (defaults to XAI_API_KEY env var)

    Returns:
        AIResponse with results
    """
    api_key = api_key or os.environ.get("XAI_API_KEY")

    if not api_key:
        return AIResponse(
            query=query,
            system="grok",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error="XAI_API_KEY not set",
        )

    try:
        import httpx

        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # xAI uses OpenAI-compatible API format
        data = {
            "model": "grok-beta",
            "messages": [{"role": "user", "content": query}],
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=data,
            )
            response.raise_for_status()
            result = response.json()

        response_time = int((time.time() - start_time) * 1000)
        response_text = result["choices"][0]["message"]["content"]

        # Analyze the response
        brand_lower = brand_name.lower()
        response_lower = response_text.lower()

        brand_mentioned = brand_lower in response_lower
        mention_count = response_lower.count(brand_lower)

        # Determine position of first mention
        position = None
        if brand_mentioned:
            first_mention = response_lower.find(brand_lower)
            response_len = len(response_text)
            if first_mention < response_len * 0.25:
                position = "first"
            elif first_mention < response_len * 0.75:
                position = "middle"
            else:
                position = "last"

        return AIResponse(
            query=query,
            system="grok",
            response=response_text,
            brand_mentioned=brand_mentioned,
            mention_count=mention_count,
            position=position,
            sentiment=None,  # Will be analyzed separately
            competitors_mentioned=[],  # Will be analyzed separately
            response_time_ms=response_time,
        )

    except ImportError:
        return AIResponse(
            query=query,
            system="grok",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error="httpx package not installed. Run: pip install httpx",
        )
    except Exception as e:
        return AIResponse(
            query=query,
            system="grok",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error=str(e),
        )


@cached("ai_responses", TTL_AI_RESPONSE)
async def query_perplexity(
    query: str, brand_name: str, api_key: Optional[str] = None
) -> AIResponse:
    """
    Query Perplexity API.

    Args:
        query: The query to send
        brand_name: Brand name to check for mentions
        api_key: Perplexity API key (defaults to PERPLEXITY_API_KEY env var)

    Returns:
        AIResponse with results
    """
    api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")

    if not api_key:
        return AIResponse(
            query=query,
            system="perplexity",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error="PERPLEXITY_API_KEY not set",
        )

    try:
        import httpx

        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [{"role": "user", "content": query}],
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=data,
            )
            response.raise_for_status()
            result = response.json()

        response_time = int((time.time() - start_time) * 1000)
        response_text = result["choices"][0]["message"]["content"]

        # Analyze the response
        brand_lower = brand_name.lower()
        response_lower = response_text.lower()

        brand_mentioned = brand_lower in response_lower
        mention_count = response_lower.count(brand_lower)

        # Determine position of first mention
        position = None
        if brand_mentioned:
            first_mention = response_lower.find(brand_lower)
            response_len = len(response_text)
            if first_mention < response_len * 0.25:
                position = "first"
            elif first_mention < response_len * 0.75:
                position = "middle"
            else:
                position = "last"

        return AIResponse(
            query=query,
            system="perplexity",
            response=response_text,
            brand_mentioned=brand_mentioned,
            mention_count=mention_count,
            position=position,
            sentiment=None,  # Will be analyzed separately
            competitors_mentioned=[],  # Will be analyzed separately
            response_time_ms=response_time,
        )

    except ImportError:
        return AIResponse(
            query=query,
            system="perplexity",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error="httpx package not installed. Run: pip install httpx",
        )
    except Exception as e:
        return AIResponse(
            query=query,
            system="perplexity",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error=str(e),
        )


@cached("ai_responses", TTL_AI_RESPONSE)
async def query_gemini(
    query: str, brand_name: str, api_key: Optional[str] = None
) -> AIResponse:
    """
    Query Google Gemini API.

    Args:
        query: The query to send
        brand_name: Brand name to check for mentions
        api_key: Google API key (defaults to GOOGLE_API_KEY env var)

    Returns:
        AIResponse with results
    """
    api_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return AIResponse(
            query=query,
            system="gemini",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error="GOOGLE_API_KEY or GEMINI_API_KEY not set",
        )

    try:
        import httpx

        start_time = time.time()

        # Gemini REST API format
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        
        data = {
            "contents": [{
                "parts": [{"text": query}]
            }],
            "generationConfig": {
                "maxOutputTokens": 1024,
                "temperature": 0.7
            }
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            result = response.json()

        response_time = int((time.time() - start_time) * 1000)
        
        # Extract response text from Gemini format
        if "candidates" in result and result["candidates"]:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                response_text = candidate["content"]["parts"][0]["text"]
            else:
                response_text = ""
        else:
            response_text = ""

        # Analyze the response
        brand_lower = brand_name.lower()
        response_lower = response_text.lower()

        brand_mentioned = brand_lower in response_lower
        mention_count = response_lower.count(brand_lower)

        # Determine position of first mention
        position = None
        if brand_mentioned:
            first_mention = response_lower.find(brand_lower)
            response_len = len(response_text)
            if first_mention < response_len * 0.25:
                position = "first"
            elif first_mention < response_len * 0.75:
                position = "middle"
            else:
                position = "last"

        return AIResponse(
            query=query,
            system="gemini",
            response=response_text,
            brand_mentioned=brand_mentioned,
            mention_count=mention_count,
            position=position,
            sentiment=None,  # Will be analyzed separately
            competitors_mentioned=[],  # Will be analyzed separately
            response_time_ms=response_time,
        )

    except ImportError:
        return AIResponse(
            query=query,
            system="gemini",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error="httpx package not installed. Run: pip install httpx",
        )
    except Exception as e:
        return AIResponse(
            query=query,
            system="gemini",
            response="",
            brand_mentioned=False,
            mention_count=0,
            position=None,
            sentiment=None,
            competitors_mentioned=[],
            response_time_ms=0,
            error=str(e),
        )


async def query_all_systems(
    queries: List[TestQuery],
    brand_name: str,
    systems: Optional[List[str]] = None,
    rate_limit_ms: int = 1000,
) -> Dict[str, List[AIResponse]]:
    """
    Query multiple AI systems with a list of test queries.

    Args:
        queries: List of TestQuery objects
        brand_name: Brand name to check for mentions
        systems: Which systems to query (default: ["claude", "chatgpt", "perplexity"])
        rate_limit_ms: Milliseconds to wait between queries (default: 1000)

    Returns:
        Dict mapping system name to list of AIResponse objects
    """
    systems = systems or ["claude", "chatgpt", "perplexity", "gemini", "grok"]

    query_functions = {
        "claude": query_claude,
        "chatgpt": query_openai,
        "perplexity": query_perplexity,
        "gemini": query_gemini,
        "grok": query_xai,
    }

    results = {system: [] for system in systems}

    for query in queries:
        # Query all systems in parallel for each query
        tasks = []
        for system in systems:
            if system in query_functions:
                tasks.append(query_functions[system](query.query, brand_name))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Map responses back to systems
        for i, system in enumerate(systems):
            if i < len(responses):
                response = responses[i]
                if not isinstance(response, Exception):
                    results[system].append(response)

        # Rate limiting
        if rate_limit_ms > 0:
            await asyncio.sleep(rate_limit_ms / 1000)

    return results


def calculate_presence_score(responses: Dict[str, List[AIResponse]]) -> Dict[str, Any]:
    """
    Calculate AI presence score from responses.

    Args:
        responses: Dict of system -> list of AIResponse

    Returns:
        Dict with score (0-25), findings, and details
    """
    total_queries = 0
    brand_mentioned = 0
    prominent_mentions = 0  # First position mentions
    findings = []

    for system, system_responses in responses.items():
        system_mentioned = 0
        system_total = 0

        for response in system_responses:
            if response.error:
                continue

            system_total += 1
            total_queries += 1

            if response.brand_mentioned:
                brand_mentioned += 1
                system_mentioned += 1

                if response.position == "first":
                    prominent_mentions += 1

        if system_total > 0:
            mention_rate = system_mentioned / system_total
            findings.append(
                f"{system}: Brand mentioned in {system_mentioned}/{system_total} queries ({mention_rate:.0%})"
            )

    # Calculate score (0-25)
    if total_queries == 0:
        score = 0
        findings.append("No successful queries - check API keys")
    else:
        mention_rate = brand_mentioned / total_queries
        prominence_rate = prominent_mentions / total_queries

        # Base score from mention rate
        if mention_rate >= 0.8:
            score = 25
        elif mention_rate >= 0.6:
            score = 20
        elif mention_rate >= 0.4:
            score = 15
        elif mention_rate >= 0.2:
            score = 10
        elif mention_rate > 0:
            score = 5
        else:
            score = 0

        # Bonus for prominent mentions
        if prominence_rate >= 0.5:
            score = min(25, score + 2)

    return {
        "score": score,
        "max": 25,
        "findings": findings,
        "details": {
            "total_queries": total_queries,
            "brand_mentioned": brand_mentioned,
            "prominent_mentions": prominent_mentions,
            "mention_rate": brand_mentioned / total_queries if total_queries > 0 else 0,
        },
    }


def query_all_systems_sync(
    queries: List[TestQuery],
    brand_name: str,
    systems: Optional[List[str]] = None,
    rate_limit_ms: int = 1000,
) -> Dict[str, List[AIResponse]]:
    """
    Sync wrapper for query_all_systems for backwards compatibility.
    """
    return asyncio.run(
        query_all_systems(
            queries=queries,
            brand_name=brand_name,
            systems=systems,
            rate_limit_ms=rate_limit_ms,
        )
    )


# Export for use by other modules
__all__ = [
    "QueryCategory",
    "TestQuery",
    "AIResponse",
    "generate_test_queries",
    "query_claude",
    "query_openai",
    "query_perplexity",
    "query_gemini",
    "query_xai",
    "query_all_systems",
    "query_all_systems_sync",
    "calculate_presence_score",
]
