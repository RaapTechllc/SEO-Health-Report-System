# Code Fix Plan - Critical Issues from Review

## Security Specialist Tasks (Priority 1 - CRITICAL)
- [ ] **Task 1.1:** Fix CORS wildcard vulnerability in api_server.py
  - Replace `allow_origins=["*"]` with specific domains
  - Add environment variable for allowed origins
  - Test CORS configuration

- [ ] **Task 1.2:** Add API authentication system
  - Implement Bearer token authentication
  - Add API key validation middleware
  - Update all endpoints to require authentication

- [ ] **Task 1.3:** Implement rate limiting
  - Add rate limiting middleware
  - Configure per-IP request limits
  - Add rate limit headers to responses

- [ ] **Task 1.4:** Remove hardcoded API keys
  - Replace demo key in competitive-monitor/api.py
  - Add proper environment variable handling
  - Update documentation

## Code Surgeon Tasks (Priority 2 - MODERATE)
- [ ] **Task 2.1:** Standardize async/sync patterns
  - Review mixed async/sync usage
  - Convert blocking operations to async where beneficial
  - Ensure consistent error handling

- [ ] **Task 2.2:** Improve error handling consistency
  - Standardize error response format across modules
  - Add proper exception handling in API endpoints
  - Implement graceful degradation patterns

- [ ] **Task 2.3:** Address technical debt items
  - Review DEVLOG.md TODO items
  - Prioritize and fix high-impact technical debt
  - Update documentation

## Test Architect Tasks (Priority 2 - MODERATE)
- [ ] **Task 3.1:** Increase test coverage for security fixes
  - Add tests for authentication middleware
  - Add tests for rate limiting
  - Add tests for CORS configuration

- [ ] **Task 3.2:** Add integration tests for API endpoints
  - Test full audit workflow
  - Test error handling scenarios
  - Test business profile functionality

- [ ] **Task 3.3:** Create smoke tests for critical paths
  - Add smoke tests for main audit flow
  - Add smoke tests for API server startup
  - Add smoke tests for security middleware

## Success Criteria
- [ ] All security vulnerabilities fixed (CORS, auth, rate limiting)
- [ ] API endpoints properly secured and tested
- [ ] Test coverage increased to >60%
- [ ] All critical paths have smoke tests
- [ ] No hardcoded secrets in codebase
- [ ] Consistent error handling across modules

## Validation
- [ ] Security scan passes
- [ ] All tests pass
- [ ] API endpoints require authentication
- [ ] Rate limiting works correctly
- [ ] CORS only allows specified domains
