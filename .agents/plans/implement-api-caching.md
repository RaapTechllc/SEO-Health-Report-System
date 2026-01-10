# Feature: Implement API Response Caching

The following plan should be complete, but validate documentation and codebase patterns before implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files.

## Feature Description

Add disk-based caching for expensive API calls (PageSpeed Insights, AI system queries, HTTP fetches). This reduces API costs, speeds up re-runs, and enables offline development with cached data.

## User Story

As a **developer running audits**
I want to **cache API responses locally**
So that **repeated audits are faster and don't waste API quota**

## Problem Statement

Every audit run makes fresh API calls even for unchanged data:
- PageSpeed Insights: Rate limited, slow (~10s per call)
- Claude/AI queries: Expensive ($), slow
- HTTP fetches: Redundant for same URLs

## Solution Statement

Implement a centralized caching layer using `diskcache` with configurable TTL per data type. Wrap existing fetch functions with cache decorators. Support cache invalidation and bypass.

## Feature Metadata

**Feature Type**: Enhancement
**Estimated Complexity**: Medium
**Primary Systems Affected**: All audit modules
**Dependencies**: `diskcache>=5.6.0`

---

## CONTEXT REFERENCES

### Relevant Codebase Files - READ BEFORE IMPLEMENTING

- `seo-technical-audit/scripts/analyze_speed.py` (lines 30-90) - Why: `get_pagespeed_insights()` is prime caching target
- `ai-visibility-audit/scripts/query_ai_systems.py` (lines 130-200) - Why: `query_claude()` expensive API calls
- `seo-technical-audit/scripts/crawl_site.py` (lines 20-45) - Why: `fetch_url()` pattern to wrap
- `seo-content-authority/scripts/analyze_content.py` (lines 20-30) - Why: `fetch_page()` duplicate pattern

### New Files to Create

- `seo-health-report/scripts/cache.py` - Centralized caching utilities

### Files to Update

- `seo-technical-audit/scripts/analyze_speed.py` - Add caching to PSI calls
- `ai-visibility-audit/scripts/query_ai_systems.py` - Add caching to AI queries
- `seo-technical-audit/scripts/crawl_site.py` - Add caching to fetches
- `seo-health-report/requirements.txt` - Add diskcache dependency

### Relevant Documentation

- [DiskCache Documentation](https://grantjenks.com/docs/diskcache/)
  - Section: Cache and memoize decorators
  - Why: Core API for implementing caching
- [DiskCache Recipes](https://grantjenks.com/docs/diskcache/tutorial.html#cache)
  - Section: Expiration and eviction
  - Why: TTL configuration patterns

### Patterns to Follow

**Existing fetch pattern** (from `crawl_site.py`):
```python
def fetch_url(url: str, timeout: int = 30) -> Optional[str]:
    try:
        import requests
        response = requests.get(url, headers=headers, timeout=timeout)
        return response.text
    except Exception:
        return None
```

**Error handling pattern** (from `query_ai_systems.py`):
```python
if not api_key:
    return AIResponse(..., error="API_KEY not set")
```

---

## IMPLEMENTATION PLAN

### Prerequisites Gate

- [ ] `pip install diskcache>=5.6.0`
- [ ] Test import: `from diskcache import Cache`

### Phase 1: Foundation

Create centralized cache module with configurable TTL.

### Phase 2: Core Implementation

Add caching to high-value API calls.

### Phase 3: Integration

Wire cache into existing functions without breaking signatures.

### Phase 4: Testing

Verify cache hits/misses and TTL behavior.

---

## STEP-BY-STEP TASKS

### Task 1: UPDATE `seo-health-report/requirements.txt`

- **IMPLEMENT**: Add diskcache dependency
- **ADD**: `diskcache>=5.6.0` after requests line
- **VALIDATE**: `pip install -r seo-health-report/requirements.txt`

### Task 2: CREATE `seo-health-report/scripts/cache.py`

- **IMPLEMENT**: Centralized caching utilities
- **IMPORTS**:
  ```python
  import os
  import hashlib
  from typing import Any, Optional, Callable
  from functools import wraps
  ```
- **COMPONENTS**:
  ```python
  # Default cache directory
  CACHE_DIR = os.path.join(os.path.expanduser("~"), ".seo-health-cache")
  
  # TTL defaults (seconds)
  TTL_PAGESPEED = 86400      # 24 hours
  TTL_AI_RESPONSE = 604800   # 7 days
  TTL_HTTP_FETCH = 3600      # 1 hour
  
  def get_cache(namespace: str = "default"):
      """Get or create cache instance."""
      from diskcache import Cache
      cache_path = os.path.join(CACHE_DIR, namespace)
      return Cache(cache_path)
  
  def cache_key(*args, **kwargs) -> str:
      """Generate cache key from arguments."""
      key_data = str(args) + str(sorted(kwargs.items()))
      return hashlib.md5(key_data.encode()).hexdigest()
  
  def cached(namespace: str, ttl: int):
      """Decorator for caching function results."""
      def decorator(func: Callable):
          @wraps(func)
          def wrapper(*args, **kwargs):
              # Check for bypass flag
              if kwargs.pop('_bypass_cache', False):
                  return func(*args, **kwargs)
              
              cache = get_cache(namespace)
              key = cache_key(func.__name__, *args, **kwargs)
              
              result = cache.get(key)
              if result is not None:
                  return result
              
              result = func(*args, **kwargs)
              if result is not None:
                  cache.set(key, result, expire=ttl)
              return result
          return wrapper
      return decorator
  
  def clear_cache(namespace: str = None):
      """Clear cache (all or specific namespace)."""
      ...
  
  def get_cache_stats() -> dict:
      """Get cache statistics."""
      ...
  ```
- **GOTCHA**: Handle `ImportError` for diskcache gracefully (fallback to no-cache)
- **VALIDATE**: `python -c "from seo_health_report.scripts.cache import cached, get_cache"`

### Task 3: UPDATE `seo-technical-audit/scripts/analyze_speed.py`

- **IMPLEMENT**: Add caching to `get_pagespeed_insights()`
- **PATTERN**: Use decorator approach
- **CHANGES**:
  ```python
  # At top of file
  try:
      from seo_health_report.scripts.cache import cached, TTL_PAGESPEED
      HAS_CACHE = True
  except ImportError:
      HAS_CACHE = False
      def cached(*args, **kwargs):
          def decorator(func): return func
          return decorator
      TTL_PAGESPEED = 0
  
  # Wrap function
  @cached("pagespeed", TTL_PAGESPEED)
  def get_pagespeed_insights(url: str, strategy: str = "mobile", ...):
      ...
  ```
- **GOTCHA**: Cache key must include `strategy` parameter
- **VALIDATE**: Run PSI twice, second should be instant

### Task 4: UPDATE `ai-visibility-audit/scripts/query_ai_systems.py`

- **IMPLEMENT**: Add caching to `query_claude()`, `query_openai()`, `query_perplexity()`
- **PATTERN**: Same decorator approach
- **CHANGES**:
  ```python
  try:
      from seo_health_report.scripts.cache import cached, TTL_AI_RESPONSE
      HAS_CACHE = True
  except ImportError:
      HAS_CACHE = False
      # ... fallback
  
  @cached("ai_responses", TTL_AI_RESPONSE)
  def query_claude(query: str, brand_name: str, ...):
      ...
  ```
- **GOTCHA**: Don't cache error responses (check `response.error` before caching)
- **VALIDATE**: Run AI query twice, verify cache hit

### Task 5: UPDATE `seo-technical-audit/scripts/crawl_site.py`

- **IMPLEMENT**: Add caching to `fetch_url()`
- **PATTERN**: Same decorator approach with shorter TTL
- **VALIDATE**: `python -c "from seo_technical_audit.scripts.crawl_site import fetch_url"`

### Task 6: ADD cache management CLI

- **IMPLEMENT**: Add cache commands to main module
- **ADD** to `seo-health-report/__init__.py`:
  ```python
  def clear_all_caches():
      """Clear all cached data."""
      from .scripts.cache import clear_cache
      clear_cache()
  ```
- **VALIDATE**: `python -c "from seo_health_report import clear_all_caches"`

---

## TESTING STRATEGY

### Manual Validation

1. Run audit → note timing
2. Run same audit again → should be significantly faster
3. Check `~/.seo-health-cache/` directory exists with data
4. Clear cache → run again → should be slow again

### Cache Behavior Tests

1. Verify different URLs get different cache entries
2. Verify TTL expiration works (set short TTL, wait, verify refetch)
3. Verify `_bypass_cache=True` forces fresh fetch

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style

```bash
python -m py_compile seo-health-report/scripts/cache.py
```

### Level 2: Import Tests

```bash
python -c "from seo_health_report.scripts.cache import cached, get_cache, clear_cache"
python -c "from seo_technical_audit.scripts.analyze_speed import get_pagespeed_insights"
```

### Level 3: Cache Functionality

```bash
python -c "
from seo_health_report.scripts.cache import get_cache, cache_key
cache = get_cache('test')
cache.set('test_key', 'test_value', expire=60)
assert cache.get('test_key') == 'test_value'
print('Cache working!')
"
```

### Level 4: Integration Test

```bash
python -c "
import time
from seo_technical_audit.scripts.analyze_speed import get_pagespeed_insights

start = time.time()
result1 = get_pagespeed_insights('https://example.com')
time1 = time.time() - start

start = time.time()
result2 = get_pagespeed_insights('https://example.com')
time2 = time.time() - start

print(f'First call: {time1:.2f}s')
print(f'Second call (cached): {time2:.2f}s')
print(f'Speedup: {time1/time2:.1f}x')
"
```

---

## ACCEPTANCE CRITERIA

- [ ] Cache module created with `cached` decorator
- [ ] PageSpeed calls cached with 24h TTL
- [ ] AI queries cached with 7-day TTL
- [ ] HTTP fetches cached with 1h TTL
- [ ] Cache bypass flag (`_bypass_cache=True`) works
- [ ] `clear_cache()` function available
- [ ] Graceful fallback when diskcache not installed
- [ ] Second audit run is measurably faster

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each validation command passes
- [ ] Cache directory created on first use
- [ ] No breaking changes to existing function signatures
- [ ] Existing audits still work without cache installed

---

## NOTES

**Design Decision**: Using diskcache over redis/memcached for zero-config local operation.

**Trade-off**: Disk cache is slower than memory cache but persists across runs.

**TTL Rationale**:
- PageSpeed: 24h because site performance changes slowly
- AI responses: 7 days because AI knowledge is relatively stable
- HTTP fetches: 1h because content can change frequently

**Future Enhancement**: Add cache warming for known URLs before audit.
