# Deployment Checklist

Pre-deployment verification for production readiness.

## Checks

### 1. Code Quality
- [ ] All tests passing
- [ ] No TypeScript errors
- [ ] ESLint clean
- [ ] No console.log in production code

### 2. Database
- [ ] Migrations up to date
- [ ] No pending schema changes
- [ ] Seed data appropriate for environment

### 3. Environment
- [ ] All required env vars documented
- [ ] No hardcoded secrets
- [ ] Production URLs configured

### 4. Security
- [ ] Auth flows tested
- [ ] Input validation in place
- [ ] CORS configured correctly
- [ ] Rate limiting enabled

### 5. Performance
- [ ] Build succeeds
- [ ] Bundle size acceptable
- [ ] No obvious N+1 queries

### 6. Documentation
- [ ] README updated
- [ ] API changes documented
- [ ] Changelog updated

## Workflow

1. Run build and tests
2. Check for security issues
3. Verify environment configuration
4. Generate deployment report

Output a pass/fail status for each check with details on any failures.
