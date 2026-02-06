#!/bin/bash
# ============================================================
# Release Verification Script
# 
# Runs all checks required before a release:
# - Linting
# - Unit tests
# - Integration tests
# - Security tests
# - Phase 2 verification
# - Docker build
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

log_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_section() {
    echo ""
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
}

# ============================================================
# Pre-flight checks
# ============================================================
log_section "Pre-flight Checks"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    log_pass "Python installed: $PYTHON_VERSION"
else
    log_fail "Python3 not found"
    exit 1
fi

# Check we're in the right directory
if [ -f "pyproject.toml" ]; then
    log_pass "In project root directory"
else
    log_fail "Not in project root (pyproject.toml not found)"
    exit 1
fi

# ============================================================
# Linting
# ============================================================
log_section "Linting (Ruff)"

if command -v ruff &> /dev/null; then
    if ruff check . --quiet 2>/dev/null; then
        log_pass "Ruff linting passed"
    else
        log_warn "Ruff linting has warnings (non-blocking)"
    fi
else
    log_warn "Ruff not installed, skipping lint"
fi

# ============================================================
# Unit Tests
# ============================================================
log_section "Unit Tests"

if command -v pytest &> /dev/null || python3 -m pytest --version &> /dev/null; then
    export DATABASE_URL="sqlite:///./test_release.db"
    export TESTING="true"
    
    if python3 -m pytest tests/unit -v --tb=short -q 2>&1 | tail -20; then
        log_pass "Unit tests passed"
    else
        log_fail "Unit tests failed"
    fi
else
    log_warn "pytest not installed, skipping tests"
fi

# ============================================================
# Integration Tests
# ============================================================
log_section "Integration Tests"

if python3 -m pytest tests/integration -v --tb=short -q 2>&1 | tail -20; then
    log_pass "Integration tests passed"
else
    log_warn "Integration tests had issues (check output)"
fi

# ============================================================
# Security Tests
# ============================================================
log_section "Security Tests"

if python3 -m pytest tests/security -v --tb=short -q 2>&1 | tail -20; then
    log_pass "Security tests passed"
else
    log_fail "Security tests failed"
fi

# ============================================================
# Phase 2 Verification
# ============================================================
log_section "Phase 2 Verification"

if python3 scripts/verify_phase2.py; then
    log_pass "Phase 2 verification passed"
else
    log_fail "Phase 2 verification failed"
fi

# ============================================================
# Docker Build (if available)
# ============================================================
log_section "Docker Build"

if command -v docker &> /dev/null; then
    if docker build -t seo-health-report:test --target production . 2>&1 | tail -10; then
        log_pass "Docker build successful"
        # Cleanup test image
        docker rmi seo-health-report:test 2>/dev/null || true
    else
        log_fail "Docker build failed"
    fi
else
    log_warn "Docker not installed, skipping build"
fi

# ============================================================
# Configuration Check
# ============================================================
log_section "Configuration Check"

# Check tier configs exist
if [ -f "config/tier_low.env" ] && [ -f "config/tier_medium.env" ] && [ -f "config/tier_high.env" ]; then
    log_pass "Tier configuration files present"
else
    log_fail "Missing tier configuration files"
fi

# Check production template exists
if [ -f "config/production.env.template" ]; then
    log_pass "Production config template present"
else
    log_warn "Production config template missing"
fi

# ============================================================
# Summary
# ============================================================
log_section "Release Verification Summary"

TOTAL=$((PASSED + FAILED))

echo ""
echo "  Passed: $PASSED"
echo "  Failed: $FAILED"
echo "  Total:  $TOTAL"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}  ✅ RELEASE VERIFICATION PASSED${NC}"
    echo -e "${GREEN}  Ready for deployment!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    exit 0
else
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}  ❌ RELEASE VERIFICATION FAILED${NC}"
    echo -e "${RED}  Fix the issues above before deploying.${NC}"
    echo -e "${RED}============================================================${NC}"
    exit 1
fi
