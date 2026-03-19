import asyncio
import os
import sys

from dotenv import load_dotenv

# Add parent dir
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Handle dashed module name import
import importlib.util

ai_vis_path = os.path.join(project_root, "ai-visibility-audit")
if ai_vis_path not in sys.path:
    sys.path.insert(0, ai_vis_path)

# Register seo_health_report module
seo_health_report_path = os.path.join(project_root, "seo-health-report")
if seo_health_report_path not in sys.path:
    sys.path.insert(0, seo_health_report_path)

# Register as seo_health_report in sys.modules
if "seo_health_report" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "seo_health_report",
        os.path.join(seo_health_report_path, "__init__.py"),
        submodule_search_locations=[seo_health_report_path]
    )
    seo_health_report_module = importlib.util.module_from_spec(spec)
    sys.modules["seo_health_report"] = seo_health_report_module
    try:
        spec.loader.exec_module(seo_health_report_module)
    except Exception:
        pass

# Explicitly load the module to allow sub-imports
spec = importlib.util.spec_from_file_location("ai_visibility_audit", os.path.join(ai_vis_path, "__init__.py"))
ai_visibility_audit = importlib.util.module_from_spec(spec)
sys.modules["ai_visibility_audit"] = ai_visibility_audit
spec.loader.exec_module(ai_visibility_audit)

# Load env
load_dotenv(os.path.join(project_root, '.env'))

from ai_visibility_audit.scripts.query_ai_systems import query_claude, query_gemini, query_openai


async def test_ai_presence():
    brand = "Stripe"
    query = "What is Stripe?"


    output = []
    output.append(f"--- Testing AI Presence for {brand} ---")

    # Check Keys
    output.append(f"Anthropic Key Present: {bool(os.environ.get('ANTHROPIC_API_KEY'))}")
    output.append(f"OpenAI Key Present: {bool(os.environ.get('OPENAI_API_KEY'))}")
    output.append(f"Perplexity Key Present: {bool(os.environ.get('PERPLEXITY_API_KEY'))}")
    output.append(f"Google/Gemini Key Present: {bool(os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY'))}")
    output.append("-" * 30)

    # Test Claude
    try:
        output.append("Querying Claude...")
        res = await query_claude(query, brand)
        output.append(f"Claude Result: Mentioned={res.brand_mentioned}, Error={res.error}, ResponseLen={len(res.response)}")
        if res.error:
            output.append(f"Claude Error Details: {res.error}")
        output.append(f"Claude Response Preview: {res.response[:100]}...")
    except Exception as e:
        output.append(f"Claude Exception: {e}")

    # Test OpenAI
    try:
        output.append("\nQuerying OpenAI...")
        res = await query_openai(query, brand)
        output.append(f"OpenAI Result: Mentioned={res.brand_mentioned}, Error={res.error}, ResponseLen={len(res.response)}")
        if res.error:
            output.append(f"OpenAI Error Details: {res.error}")
        output.append(f"OpenAI Response Preview: {res.response[:100]}...")
    except Exception as e:
        output.append(f"OpenAI Exception: {e}")

    # Test Gemini
    try:
        output.append("\nQuerying Gemini...")
        res = await query_gemini(query, brand)
        output.append(f"Gemini Result: Mentioned={res.brand_mentioned}, Error={res.error}, ResponseLen={len(res.response)}")
        if res.error:
            output.append(f"Gemini Error Details: {res.error}")
        output.append(f"Gemini Response Preview: {res.response[:100]}...")
    except Exception as e:
         output.append(f"Gemini Exception: {e}")

    with open('debug_log.txt', 'w') as f:
        f.write('\n'.join(output))

    print("Debug log written to debug_log.txt")

if __name__ == "__main__":
    asyncio.run(test_ai_presence())
