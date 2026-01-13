# Technical Steering: SEO Health Report

## Package Structure

This project uses **hyphenated folder names** for packages:
- `seo-health-report/`
- `seo-technical-audit/`
- `seo-content-authority/`
- `ai-visibility-audit/`

### Import Pattern for Hyphenated Packages

Python doesn't natively support hyphens in package names. Use this pattern:

```python
import importlib.util
import sys
import os

def register_module_alias(alias_name: str, folder_name: str):
    """Register a hyphenated folder as a Python module."""
    folder_path = os.path.join(project_root, folder_name)
    init_path = os.path.join(folder_path, "__init__.py")
    if os.path.exists(init_path):
        spec = importlib.util.spec_from_file_location(
            alias_name, 
            init_path,
            submodule_search_locations=[folder_path]
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[alias_name] = module
        spec.loader.exec_module(module)

def register_scripts_submodule(parent_alias: str, folder_name: str):
    """Register the scripts submodule for a hyphenated folder."""
    folder_path = os.path.join(project_root, folder_name, 'scripts')
    init_path = os.path.join(folder_path, "__init__.py")
    submodule_name = f'{parent_alias}.scripts'
    if os.path.exists(init_path):
        spec = importlib.util.spec_from_file_location(
            submodule_name, 
            init_path,
            submodule_search_locations=[folder_path]
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[submodule_name] = module
        spec.loader.exec_module(module)

# Registration order matters - dependencies first
register_module_alias("seo_health_report", "seo-health-report")
register_scripts_submodule("seo_health_report", "seo-health-report")

register_module_alias("seo_technical_audit", "seo-technical-audit")
register_scripts_submodule("seo_technical_audit", "seo-technical-audit")
# ... etc
```

Then use normal imports:
```python
from seo_technical_audit.scripts.crawl_site import analyze_crawlability
from ai_visibility_audit.scripts.query_ai_systems import generate_test_queries
```

**Anti-pattern** (do not use):
```python
# BAD: Reading source and exec()ing it loses import context
def load_ai_module(name):
    with open(filepath, 'r') as f:
        source = f.read()
    source = source.replace('from .', 'from ')  # This breaks things
    exec(compile(source, filepath, 'exec'), module.__dict__)
```

## Async/Sync Patterns

Many functions in this codebase are async. When calling from sync context:

```python
import asyncio

# Correct: Use asyncio.run() for top-level async calls
result = asyncio.run(async_function())

# The _sync wrapper pattern (if needed)
def get_data_sync(...):
    """Sync wrapper for backwards compatibility."""
    return asyncio.run(get_data_async(...))
```

## Null Safety

When using `dict.get()`, remember that it returns `None` if the key exists with `None` value:

```python
# BAD: Returns None if score key exists but is None
score = data.get("score", 0)
if score >= 90:  # TypeError: '>=' not supported between NoneType and int

# GOOD: Explicitly handle None
score = data.get("score") or 0
if score >= 90:  # Works correctly
```

## Console Output (Windows)

Windows terminal uses cp1252 encoding which doesn't support Unicode emojis.

```python
# BAD: Causes UnicodeEncodeError on Windows
print("Successfully generated report!")

# GOOD: Use ASCII text
print("[SUCCESS] Report generated")
print("[WARNING] Premium template failed")
print("[ERROR] Something went wrong")
```

## Error Handling

Never silently swallow errors in production code:

```python
# BAD: Hides real problems
except Exception:
    pass

# GOOD: Log and/or return meaningful defaults
except Exception as e:
    logger.error(f"Failed to fetch {url}: {e}")
    return {"score": 0, "error": str(e)}
```

## Dependencies Between Modules

Module loading order matters:

1. `seo_health_report` - Core config, logger, cache (no dependencies)
2. `seo_technical_audit` - Depends on seo_health_report.config
3. `seo_content_authority` - Depends on seo_health_report.config
4. `ai_visibility_audit` - Depends on seo_health_report.config

Always register `seo_health_report` first when setting up module aliases.

## API Key Configuration

Use fallback chains for API keys to support both generic and specific env vars:

```python
# GOOD: Fallback chain - specific key first, then generic
api_key = api_key or os.environ.get("PAGESPEED_API_KEY") or os.environ.get("GOOGLE_API_KEY")
api_key = api_key or os.environ.get("GOOGLE_KG_API_KEY") or os.environ.get("GOOGLE_API_KEY")

# BAD: Only one env var name supported
api_key = api_key or os.environ.get("PAGESPEED_API_KEY")  # Fails if user has GOOGLE_API_KEY
```

**Current API key environment variables:**

| Service | Primary Env Var | Fallback Env Var |
|---------|-----------------|------------------|
| PageSpeed Insights | `PAGESPEED_API_KEY` | `GOOGLE_API_KEY` |
| Google Knowledge Graph | `GOOGLE_KG_API_KEY` | `GOOGLE_API_KEY` |
| Claude (Anthropic) | `ANTHROPIC_API_KEY` | - |
| OpenAI (ChatGPT) | `OPENAI_API_KEY` | - |
| Perplexity | `PERPLEXITY_API_KEY` | - |
| xAI (Grok) | `XAI_API_KEY` | - |
| Google Gemini | `GOOGLE_GEMINI_API_KEY` | `GOOGLE_API_KEY` |

## Multi-Model Architecture

The system uses different AI models for different tasks:

| Task | Model | Reason |
|------|-------|--------|
| Analysis & Writing | Anthropic Claude | Best reasoning, nuanced writing |
| Visual Generation | Google Gemini/Imagen | Image gen, emoji formatting |
| AI Visibility Queries | Multiple (Claude, GPT, etc.) | Coverage across AI systems |

**Gemini Integration** (`gemini_integration.py`):
- `gemini-2.0-flash` - Fast text generation, formatting
- `gemini-1.5-pro` - Complex visual descriptions
- `imagen-3.0-generate-002` - Image/infographic generation

```python
from seo_health_report.scripts.gemini_integration import (
    GeminiClient,
    generate_report_visuals,
    enhance_executive_summary,
)

# Async usage
async with GeminiClient() as client:
    if client.available:
        formatted = await client.format_with_emojis(text)
        image_bytes = await client.generate_image(prompt)

# Sync wrappers available
assets = generate_report_visuals_sync(audit_data, output_dir)
```

## AI System Integrations

The `query_all_systems()` function queries these AI systems by default:
- `claude` - Anthropic Claude (implemented)
- `chatgpt` - OpenAI ChatGPT (stubbed)
- `perplexity` - Perplexity AI (stubbed)
- `grok` - xAI Grok (implemented)

**xAI/Grok API format** (OpenAI-compatible):
```python
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
data = {"model": "grok-beta", "messages": [{"role": "user", "content": query}]}
response = await client.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data)
```
