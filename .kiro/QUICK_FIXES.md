# Quick Fixes - Production Hardening
**Priority: HIGH** | **Time: ~30 minutes**

## 1. Install Test Dependencies ⚡
```bash
pip3 install pytest pytest-asyncio pytest-cov hypothesis
```

## 2. Run Test Suite ✅
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run smoke tests only (fast)
python3 -m pytest tests/smoke/ -v

# Check coverage
python3 -m pytest tests/ --cov=seo-health-report --cov-report=html
```

## 3. Fix .gitignore 🔒
```bash
# Add sensitive files to .gitignore
echo ".env.local" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore

# Remove from git if already committed
git rm --cached .env.local 2>/dev/null || true
```

## 4. Verify Core Functionality 🧪
```bash
# Test basic audit
python3 run_audit.py --url https://example.com --company "Example Corp"

# Test premium report
python3 run_premium_audit.py --url https://example.com --company "Example Corp"
```

## 5. Check API Keys 🔑
```bash
# Verify required keys are set
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.local')

keys = {
    'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
    'GOOGLE_GEMINI_API_KEY': os.getenv('GOOGLE_GEMINI_API_KEY'),
    'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
}

for key, value in keys.items():
    status = '✅' if value else '❌'
    print(f'{status} {key}: {\"Set\" if value else \"Not set\"}')"
```

## 6. Performance Baseline 📊
```bash
# Time a full audit
time python3 run_audit.py --url https://example.com --company "Test"

# Expected: 30-60 seconds
```

## Expected Results
- ✅ All smoke tests pass
- ✅ Coverage > 80%
- ✅ No sensitive files in git
- ✅ API keys configured
- ✅ Reports generate successfully
- ✅ Performance within acceptable range

## If Tests Fail
1. Check logs: `tail -50 logs/seo-health-report.log`
2. Verify dependencies: `pip3 list | grep -E "pytest|requests|beautifulsoup"`
3. Check Python version: `python3 --version` (should be 3.9+)

## Success Criteria
All items checked = **Production Ready** ✅
