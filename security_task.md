## SECURITY SPECIALIST TASK

You are working in an isolated Git worktree to fix critical security vulnerabilities.

### CRITICAL SECURITY FIXES NEEDED:

**Task 1.1: Fix CORS Wildcard (api_server.py:33)**
- Current: allow_origins=["*"] 
- Fix: Use specific domains from environment variable
- Add ALLOWED_ORIGINS env var

**Task 1.2: Add API Authentication**
- Implement Bearer token authentication
- Add middleware to validate API keys
- Protect all endpoints

**Task 1.3: Add Rate Limiting**
- Implement per-IP rate limiting
- Add rate limit headers
- Configure reasonable limits

**Task 1.4: Remove Hardcoded Keys**
- Fix competitive-monitor/api.py:29 demo key
- Use environment variables properly

### VALIDATION:
After each fix, run: python -m pytest tests/unit/test_security.py

### COMPLETION:
When all security fixes are complete, output: <promise>DONE</promise>

BEGIN SECURITY FIXES:
