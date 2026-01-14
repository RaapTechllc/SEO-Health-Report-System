# Recommended Code Improvements

## 1. Replace Bare Exception Handlers

### File: `multi-tier-reports/tier_classifier.py`

**Lines 146, 159, 174 - Replace bare except:**

```python
# BEFORE (Line 146)
try:
    return len(pages)
except:
    return 500  # Default

# AFTER
try:
    return len(pages)
except (AttributeError, TypeError, ValueError) as e:
    logger.warning(f"Failed to count pages: {e}")
    return 500  # Default
```

```python
# BEFORE (Line 159)
try:
    domain_hash = int(hashlib.md5(domain.encode()).hexdigest()[:8], 16)
    return (domain_hash % 80) + 10
except:
    return 40  # Default

# AFTER
try:
    domain_hash = int(hashlib.md5(domain.encode()).hexdigest()[:8], 16)
    return (domain_hash % 80) + 10
except (ValueError, AttributeError) as e:
    logger.warning(f"Failed to estimate DA for {domain}: {e}")
    return 40  # Default
```

---

## 2. Add Exponential Backoff for API Calls

### File: `ai-visibility-audit/scripts/query_ai_systems.py`

**Add retry logic with exponential backoff:**

```python
async def query_with_backoff(
    query_func,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> Any:
    """
    Execute query with exponential backoff on failure.
    
    Args:
        query_func: Async function to execute
        max_retries: Maximum retry attempts
        base_delay: Base delay in seconds (doubles each retry)
    
    Returns:
        Query result
    
    Raises:
        Exception: If all retries exhausted
    """
    for attempt in range(max_retries):
        try:
            return await query_func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            delay = base_delay * (2 ** attempt)
            logger.warning(
                f"Query failed (attempt {attempt + 1}/{max_retries}): {e}. "
                f"Retrying in {delay}s..."
            )
            await asyncio.sleep(delay)
```

**Usage:**
```python
# In query_all_systems()
async def _query():
    return await query_claude(query, brand_name)

response = await query_with_backoff(_query)
```

---

## 3. Consolidate Requirements Files

### Create: `requirements.txt` (root)

```ini
# Core dependencies
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
aiohttp>=3.9.0
python-dotenv>=1.0.0

# HTML/Text processing
textstat>=0.7.3
nltk>=3.8.1

# PDF generation
reportlab>=4.0.0
matplotlib>=3.7.0
Pillow>=10.0.0

# API clients
anthropic>=0.7.0
openai>=1.0.0
google-generativeai>=0.3.0

# Testing (optional)
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
hypothesis>=6.92.0

# Development (optional)
black>=23.0.0
mypy>=1.7.0
```

**Then update each module's requirements.txt:**
```ini
# seo-technical-audit/requirements.txt
-r ../requirements.txt
# Module-specific dependencies only
```

---

## 4. Add Comprehensive Caching Decorator

### File: `seo-health-report/scripts/cache.py`

**Add decorator for easy caching:**

```python
import functools
import hashlib
import json
from typing import Any, Callable

def cache_result(ttl: int = 3600):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
    
    Usage:
        @cache_result(ttl=3600)
        async def fetch_data(url: str):
            return await expensive_api_call(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            cache_key = hashlib.md5(
                json.dumps(key_data, sort_keys=True).encode()
            ).hexdigest()
            
            # Check cache
            cached = get_cached(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            set_cached(cache_key, result, ttl=ttl)
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Same logic for sync functions
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            cache_key = hashlib.md5(
                json.dumps(key_data, sort_keys=True).encode()
            ).hexdigest()
            
            cached = get_cached(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached
            
            result = func(*args, **kwargs)
            set_cached(cache_key, result, ttl=ttl)
            return result
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
```

**Usage:**
```python
# In analyze_speed.py
@cache_result(ttl=3600)
async def get_pagespeed_insights(url: str, strategy: str):
    # Expensive API call
    return await fetch_psi_data(url, strategy)
```

---

## 5. Improve URL Validation

### File: `seo-health-report/scripts/validators.py` (new file)

```python
"""Input validation utilities."""

import re
from urllib.parse import urlparse, urlunparse
from typing import Optional

class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_url(url: str, require_https: bool = False) -> str:
    """
    Validate and normalize URL.
    
    Args:
        url: URL to validate
        require_https: If True, reject non-HTTPS URLs
    
    Returns:
        Normalized URL
    
    Raises:
        ValidationError: If URL is invalid
    """
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}")
    
    # Validate components
    if not parsed.netloc:
        raise ValidationError(f"Invalid URL: missing domain")
    
    # Check for valid domain format
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    if not re.match(domain_pattern, parsed.netloc.split(':')[0]):
        raise ValidationError(f"Invalid domain format: {parsed.netloc}")
    
    # Enforce HTTPS if required
    if require_https and parsed.scheme != 'https':
        raise ValidationError(f"HTTPS required, got {parsed.scheme}")
    
    # Normalize and return
    return urlunparse(parsed)


def validate_keywords(keywords: list, min_count: int = 1, max_count: int = 20) -> list:
    """
    Validate keyword list.
    
    Args:
        keywords: List of keywords
        min_count: Minimum number of keywords
        max_count: Maximum number of keywords
    
    Returns:
        Validated keyword list
    
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(keywords, list):
        raise ValidationError("Keywords must be a list")
    
    if len(keywords) < min_count:
        raise ValidationError(f"At least {min_count} keyword(s) required")
    
    if len(keywords) > max_count:
        raise ValidationError(f"Maximum {max_count} keywords allowed")
    
    # Clean and validate each keyword
    cleaned = []
    for kw in keywords:
        if not isinstance(kw, str):
            raise ValidationError(f"Invalid keyword type: {type(kw)}")
        
        kw = kw.strip()
        if not kw:
            continue
        
        if len(kw) > 100:
            raise ValidationError(f"Keyword too long: {kw[:50]}...")
        
        cleaned.append(kw)
    
    if len(cleaned) < min_count:
        raise ValidationError(f"At least {min_count} non-empty keyword(s) required")
    
    return cleaned
```

**Usage:**
```python
# In generate_report()
from .scripts.validators import validate_url, validate_keywords, ValidationError

try:
    target_url = validate_url(target_url)
    primary_keywords = validate_keywords(primary_keywords, min_count=3)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    return {"error": str(e), "success": False}
```

---

## 6. Add Rate Limiter Class

### File: `seo-health-report/scripts/rate_limiter.py` (new file)

```python
"""Rate limiting utilities."""

import asyncio
import time
from collections import deque
from typing import Optional


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Usage:
        limiter = RateLimiter(calls_per_second=10)
        
        async with limiter:
            await make_api_call()
    """
    
    def __init__(
        self,
        calls_per_second: float = 10.0,
        burst_size: Optional[int] = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_second: Maximum calls per second
            burst_size: Maximum burst size (defaults to calls_per_second)
        """
        self.rate = calls_per_second
        self.burst_size = burst_size or int(calls_per_second)
        self.tokens = self.burst_size
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
    
    async def __aenter__(self):
        """Acquire rate limit token."""
        async with self.lock:
            # Refill tokens based on time elapsed
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            # Wait if no tokens available
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release (no-op for token bucket)."""
        pass


# Global rate limiters for different services
ANTHROPIC_LIMITER = RateLimiter(calls_per_second=5)
GOOGLE_LIMITER = RateLimiter(calls_per_second=10)
OPENAI_LIMITER = RateLimiter(calls_per_second=3)
```

**Usage:**
```python
# In query_ai_systems.py
from seo_health_report.scripts.rate_limiter import ANTHROPIC_LIMITER

async def query_claude(query: str, brand_name: str):
    async with ANTHROPIC_LIMITER:
        # Make API call
        return await anthropic_client.messages.create(...)
```

---

## 7. Add Structured Logging

### File: `seo-health-report/scripts/logger.py`

**Add structured logging support:**

```python
import json
from typing import Any, Dict

def log_structured(
    logger,
    level: str,
    message: str,
    **kwargs: Any
):
    """
    Log structured data as JSON.
    
    Args:
        logger: Logger instance
        level: Log level (info, warning, error)
        message: Human-readable message
        **kwargs: Additional structured data
    """
    log_data = {
        'message': message,
        'timestamp': datetime.now().isoformat(),
        **kwargs
    }
    
    log_func = getattr(logger, level.lower())
    log_func(json.dumps(log_data))


# Usage
log_structured(
    logger,
    'info',
    'Audit completed',
    url='https://example.com',
    score=85,
    duration_seconds=45.2
)
```

---

## Priority Implementation Order

1. **HIGH** - Replace bare exception handlers (15 min)
2. **HIGH** - Add URL validation (20 min)
3. **MEDIUM** - Add exponential backoff (30 min)
4. **MEDIUM** - Add rate limiter class (30 min)
5. **MEDIUM** - Add caching decorator (30 min)
6. **LOW** - Consolidate requirements (20 min)
7. **LOW** - Add structured logging (15 min)

**Total time: ~2.5 hours**

---

## Testing Each Improvement

```bash
# After each change, run:
python3 -m pytest tests/ -v -k "test_related_to_change"

# Full test suite:
python3 -m pytest tests/ -v --cov

# Smoke tests:
python3 -m pytest tests/smoke/ -v
```

---

## Expected Impact

| Improvement | Impact | Effort |
|-------------|--------|--------|
| Exception handlers | Better debugging | Low |
| URL validation | Fewer errors | Low |
| Exponential backoff | Better reliability | Medium |
| Rate limiter | Prevent API bans | Medium |
| Caching decorator | Faster audits | Medium |
| Requirements consolidation | Easier maintenance | Low |
| Structured logging | Better monitoring | Low |

**Overall: Significant quality improvement with minimal effort**
