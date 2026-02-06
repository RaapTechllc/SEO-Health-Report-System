
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from social_media_audit.social_media_audit import get_grok_sentiment
except ImportError:
    # Handle case where social_media_audit is a package or just a folder
    sys.path.append(str(Path(__file__).parent / "social-media-audit"))
    from social_media_audit import get_grok_sentiment

def test_grok_integration():
    print("🧪 Testing Grok Integration...")

    # Check for API Key
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        print("⚠️  XAI_API_KEY not found in environment.")
        print("   To test real Grok integration, set XAI_API_KEY in your .env file.")
        print("   Proceeding with mock test (expecting graceful fallback)...")
    else:
        print("✅ XAI_API_KEY found.")

    # Test with a known tech company
    company = "Vercel"
    domain = "vercel.com"

    print(f"\nrunning analysis for: {company} ({domain})")
    try:
        result = get_grok_sentiment(company, domain)
        print("\n📊 Result:")
        print(json.dumps(result, indent=2))

        if result.get("available"):
            print("\n✅ Grok integration successful!")
            if result.get("score") > 0:
                print(f"   Sentiment Score: {result['score']}")
                print(f"   Summary: {result['summary']}")
        else:
            print("\nℹ️  Grok integration handled missing key/error correctly.")
            print("   (This is expected if you haven't added an XAI payment method yet)")

    except Exception as e:
        print(f"\n❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from dotenv import load_dotenv
    # Load from .env and .env.local
    load_dotenv()
    load_dotenv(".env.local", override=True)

    test_grok_integration()
