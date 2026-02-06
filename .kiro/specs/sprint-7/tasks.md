# Sprint 7: Tasks

## Overview
**Focus:** CI/CD + Staging→Prod + Chaos Hardening
**Prerequisites:** Sprint 6 complete (1074 tests passing, dashboard MVP, quotas, E2E tests)
**Duration:** ~10-14 days

---

## Phase 1: Build & Push Containers — Days 1-3

### Task 7.1.1: Enhance Dockerfiles for Production
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Improve Dockerfiles with multi-stage builds, security, and optimization
- **Deliverables:**
  - [ ] Update `infrastructure/docker/api.Dockerfile` with multi-stage build
  - [ ] Update `infrastructure/docker/worker.Dockerfile` with multi-stage build
  - [ ] Add non-root user for security
  - [ ] Optimize layer caching
  - [ ] Add build ARGs for version tagging
- **Acceptance Criteria:**
  - [ ] Images are smaller (<500MB)
  - [ ] Run as non-root user
  - [ ] Build args: VERSION, GIT_SHA, BUILD_DATE
  - [ ] Health checks work
- **Dependencies:** None

### Task 7.1.2: GitHub Actions - Build & Push Workflow
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** M (3-4h)
- **Description:** Create workflow to build and push Docker images to GitHub Container Registry
- **Deliverables:**
  - [ ] `.github/workflows/docker-build.yml`
  - [ ] Build API and Worker images in parallel
  - [ ] Push to ghcr.io with version tags
  - [ ] Include git SHA in image tags
- **Acceptance Criteria:**
  - [ ] Images tagged: `latest`, `sha-{commit}`, `v{version}`
  - [ ] Build matrix for API and Worker
  - [ ] Caching enabled for faster builds
  - [ ] Triggered on push to main and tags
- **Dependencies:** 7.1.1

### Task 7.1.3: Container Security Scanning
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** S (1-2h)
- **Description:** Add vulnerability scanning to container build pipeline
- **Deliverables:**
  - [ ] Trivy scanner integration in docker-build.yml
  - [ ] SARIF output for GitHub Security tab
  - [ ] Fail on CRITICAL vulnerabilities
- **Acceptance Criteria:**
  - [ ] Scan results visible in GitHub Security
  - [ ] CRITICAL vulns block merge
  - [ ] HIGH vulns generate warnings
- **Dependencies:** 7.1.2

---

## Phase 2: Staging Deploy Pipeline — Days 4-6

### Task 7.2.1: Staging Environment Configuration
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Create staging environment configuration and secrets
- **Deliverables:**
  - [ ] `infrastructure/envs/staging.env.example`
  - [ ] GitHub Secrets documentation
  - [ ] Staging database connection string pattern
  - [ ] Staging-specific feature flags
- **Acceptance Criteria:**
  - [ ] Clear separation from prod secrets
  - [ ] Environment validation at startup
  - [ ] Documented secret requirements
- **Dependencies:** None

### Task 7.2.2: Database Migration Script
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Create migration script for CI/CD pipeline
- **Deliverables:**
  - [ ] `scripts/run_migrations.sh`
  - [ ] Pre-migration backup option
  - [ ] Migration status check
  - [ ] Rollback support
- **Acceptance Criteria:**
  - [ ] Alembic migrations run cleanly
  - [ ] Exit codes indicate success/failure
  - [ ] Backup created before migration
  - [ ] Can rollback to previous version
- **Dependencies:** None

### Task 7.2.3: Staging Deploy Workflow
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** L (4-6h)
- **Description:** Create GitHub Actions workflow for staging deployment
- **Deliverables:**
  - [ ] `.github/workflows/deploy-staging.yml`
  - [ ] Pull latest images from ghcr.io
  - [ ] Run migrations
  - [ ] Deploy API and Worker
  - [ ] Run smoke tests after deploy
- **Acceptance Criteria:**
  - [ ] Triggered automatically after docker-build on main
  - [ ] Migrations run before deploy
  - [ ] Health checks pass post-deploy
  - [ ] Smoke tests verify basic functionality
  - [ ] Slack/Discord notification on completion
- **Dependencies:** 7.1.2, 7.2.1, 7.2.2

### Task 7.2.4: Staging Smoke Tests
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Create smoke test suite for post-deployment verification
- **Deliverables:**
  - [ ] `tests/smoke/test_staging_health.py`
  - [ ] API health endpoint check
  - [ ] Database connectivity check
  - [ ] Authentication flow check
  - [ ] Basic audit creation check
- **Acceptance Criteria:**
  - [ ] Tests run in <30 seconds
  - [ ] Clear pass/fail output
  - [ ] Tests configurable via env vars
  - [ ] Can run against any environment
- **Dependencies:** 7.2.3

---

## Phase 3: Production Deploy Pipeline — Days 7-9

### Task 7.3.1: Production Environment Configuration
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Create production environment configuration with enhanced security
- **Deliverables:**
  - [ ] `infrastructure/envs/production.env.example`
  - [ ] Production-specific security headers
  - [ ] Production database requirements
  - [ ] Secrets rotation documentation
- **Acceptance Criteria:**
  - [ ] No debug settings in production
  - [ ] Strict CORS configuration
  - [ ] Database connection pooling configured
  - [ ] Rate limits appropriate for production
- **Dependencies:** 7.2.1

### Task 7.3.2: Production Deploy Workflow with Manual Approval
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** L (4-6h)
- **Description:** Create production deployment workflow with manual approval gate
- **Deliverables:**
  - [ ] `.github/workflows/deploy-production.yml`
  - [ ] Manual approval step using GitHub Environments
  - [ ] Pre-deploy checklist verification
  - [ ] Deployment with zero-downtime
  - [ ] Post-deploy verification
- **Acceptance Criteria:**
  - [ ] Requires manual approval from maintainers
  - [ ] Shows staging test results before approval
  - [ ] Deploys only tagged releases (v*)
  - [ ] Health checks before traffic switch
  - [ ] Notification on success/failure
- **Dependencies:** 7.2.3, 7.3.1

### Task 7.3.3: Rollback Procedure & Script
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** M (3-4h)
- **Description:** Create documented rollback procedure and automation
- **Deliverables:**
  - [ ] `scripts/rollback.sh`
  - [ ] `docs/ROLLBACK_PROCEDURE.md`
  - [ ] Rollback workflow `.github/workflows/rollback.yml`
  - [ ] Database rollback steps
- **Acceptance Criteria:**
  - [ ] Can rollback to any previous version
  - [ ] Database rollback documented (if needed)
  - [ ] Rollback takes <5 minutes
  - [ ] Team notified of rollback
- **Dependencies:** 7.3.2

### Task 7.3.4: Post-Deploy Monitoring & Alerts
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Add post-deployment monitoring and alerting
- **Deliverables:**
  - [x] Health check monitoring script (`scripts/post_deploy_monitor.sh`)
  - [x] Error rate monitoring via /metrics endpoint (`scripts/check_metrics.py`)
  - [x] Alert on deployment failure (Slack/Discord webhooks in workflows)
  - [x] Alert on elevated error rates post-deploy
- **Acceptance Criteria:**
  - [x] Alerts within 5 minutes of issue (2-min monitoring loop)
  - [x] Clear alert messages with context (version, timestamp, error details)
  - [x] Integration with existing /metrics endpoint
- **Dependencies:** 7.3.2

---

## Phase 4: Chaos Tests — Days 10-14

### Task 7.4.1: Timeout Simulation Tests
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (3-4h)
- **Description:** Create tests that simulate various timeout scenarios
- **Deliverables:**
  - [ ] `tests/chaos/test_timeouts.py`
  - [ ] PageSpeed API timeout simulation
  - [ ] Crawl timeout simulation
  - [ ] Database timeout simulation
  - [ ] External API timeout simulation
- **Acceptance Criteria:**
  - [ ] Audit returns partial results on timeout
  - [ ] No deadlocks on timeout
  - [ ] Error logged with timeout details
  - [ ] User-friendly error message
- **Dependencies:** None

### Task 7.4.2: Rate Limit (429) Handling Tests
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Test system behavior when external APIs return 429
- **Deliverables:**
  - [ ] `tests/chaos/test_rate_limits.py`
  - [ ] PageSpeed 429 handling
  - [ ] AI API 429 handling (if applicable)
  - [ ] Retry-after header respect
  - [ ] Exponential backoff verification
- **Acceptance Criteria:**
  - [ ] System retries with backoff
  - [ ] Respects Retry-After header
  - [ ] Returns partial results if retries exhausted
  - [ ] No cascading failures
- **Dependencies:** None

### Task 7.4.3: Robots.txt Blocking Tests
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Test system behavior when robots.txt blocks crawling
- **Deliverables:**
  - [ ] `tests/chaos/test_robots_blocking.py`
  - [ ] Full site block scenario
  - [ ] Partial path block scenario
  - [ ] Delayed robots.txt fetch scenario
  - [ ] Missing robots.txt scenario
- **Acceptance Criteria:**
  - [ ] Respects robots.txt directives
  - [ ] Clear error message when fully blocked
  - [ ] Partial results when partially blocked
  - [ ] Graceful handling of missing robots.txt
- **Dependencies:** None

### Task 7.4.4: Network Failure Tests
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Test system resilience to network failures
- **Deliverables:**
  - [ ] `tests/chaos/test_network_failures.py`
  - [ ] DNS resolution failure
  - [ ] Connection refused
  - [ ] Connection reset
  - [ ] SSL/TLS errors
- **Acceptance Criteria:**
  - [ ] Clear error messages for each failure type
  - [ ] No hung connections
  - [ ] Timeouts applied correctly
  - [ ] Partial results where possible
- **Dependencies:** None

### Task 7.4.5: Concurrent Audit Chaos Tests
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (3-4h)
- **Description:** Test system under concurrent audit load with failures
- **Deliverables:**
  - [ ] `tests/chaos/test_concurrent_failures.py`
  - [ ] Multiple audits with random failures
  - [ ] Database connection pool exhaustion
  - [ ] Worker crash recovery
  - [ ] Queue overflow handling
- **Acceptance Criteria:**
  - [ ] No database deadlocks
  - [ ] Failed audits don't affect others
  - [ ] System recovers from worker crash
  - [ ] Queue handles backpressure
- **Dependencies:** 7.4.1, 7.4.2

### Task 7.4.6: Chaos Test CI Integration
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** S (1-2h)
- **Description:** Integrate chaos tests into CI pipeline
- **Deliverables:**
  - [ ] Update `.github/workflows/ci.yml` with chaos test job
  - [ ] Chaos tests run on PR to main
  - [ ] Chaos test results in CI summary
- **Acceptance Criteria:**
  - [ ] Chaos tests don't block regular PRs (warning only)
  - [ ] Required for release branches
  - [ ] Clear reporting of chaos test results
- **Dependencies:** 7.4.1-7.4.5

---

## Summary

| Phase | Tasks | Effort | Focus |
|-------|-------|--------|-------|
| Build & Push | 7.1.1-7.1.3 | M+M+S | Container Pipeline |
| Staging Deploy | 7.2.1-7.2.4 | M+M+L+M | Staging CI/CD |
| Prod Deploy | 7.3.1-7.3.4 | M+L+M+M | Production CI/CD |
| Chaos Tests | 7.4.1-7.4.6 | M+M+M+M+M+S | Resilience Testing |

**Total Tasks:** 17
**Estimated Duration:** 10-14 days

## Critical Path

```
7.1.1 Dockerfiles ──→ 7.1.2 Build Workflow ──→ 7.1.3 Security Scan
                              ↓
7.2.1 Staging Config ────────────────────┐
7.2.2 Migration Script ──────────────────┼──→ 7.2.3 Staging Deploy ──→ 7.2.4 Smoke Tests
                                         │            ↓
7.3.1 Prod Config ──────────────────────────→ 7.3.2 Prod Deploy ──→ 7.3.3 Rollback
                                                      ↓
                                              7.3.4 Monitoring

7.4.1 Timeouts ────┐
7.4.2 Rate Limits ─┼──→ 7.4.5 Concurrent Chaos ──→ 7.4.6 CI Integration
7.4.3 Robots ──────┤
7.4.4 Network ─────┘
```

## Exit Criteria Checklist
- [ ] Docker images build and push to ghcr.io
- [ ] Images tagged with git SHA and version
- [ ] Security scan passes (no CRITICAL vulnerabilities)
- [ ] Staging deploy pipeline works end-to-end
- [ ] Migrations run automatically in staging
- [ ] Smoke tests pass after staging deploy
- [ ] Production deploy requires manual approval
- [ ] Rollback procedure documented and tested
- [ ] Chaos tests prove no deadlocks
- [ ] Partial results work on failures
- [ ] All chaos tests integrated in CI
- [ ] Test count >1150 (currently 1074)
- [ ] All CI checks pass

## Quick Start

To begin Sprint 7, start with Task 7.1.1 (Enhance Dockerfiles):

```bash
# View current Dockerfiles
cat infrastructure/docker/api.Dockerfile
cat infrastructure/docker/worker.Dockerfile

# Run tests after implementation
python3 -m pytest tests/ -v --ignore=tests/unit/test_async_operations.py --ignore=tests/test_cache.py
```

## Notes

- Existing Dockerfiles at infrastructure/docker/ need multi-stage builds
- GitHub Container Registry (ghcr.io) used for image storage
- Alembic migrations at infrastructure/migrations/versions/
- Existing CI at .github/workflows/ci.yml needs chaos test integration
- verify_release.sh at scripts/ should be updated for new checks
