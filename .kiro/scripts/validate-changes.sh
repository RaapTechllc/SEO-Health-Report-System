#!/bin/bash
# Post-response validation script
# Runs appropriate tests based on project type

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "VALIDATION RESULTS"
echo "═══════════════════════════════════════════════════════════"

VALIDATION_FAILED=0

# Node.js / TypeScript projects
if [ -f package.json ]; then
  echo ""
  echo "## Package.json detected - running Node validations"
  
  # TypeScript check
  if grep -q '"typescript"' package.json 2>/dev/null || [ -f tsconfig.json ]; then
    echo ""
    echo "### TypeScript Compilation"
    npx tsc --noEmit 2>&1 | tail -15
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
      VALIDATION_FAILED=1
      echo "❌ TypeScript errors detected"
    else
      echo "✅ TypeScript compilation passed"
    fi
  fi
  
  # Lint check
  if grep -q '"lint"' package.json 2>/dev/null; then
    echo ""
    echo "### Linting"
    npm run lint 2>&1 | tail -10
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
      echo "⚠️  Lint warnings/errors detected"
    else
      echo "✅ Linting passed"
    fi
  fi
  
  # Test check (only if tests exist)
  if grep -q '"test"' package.json 2>/dev/null; then
    echo ""
    echo "### Tests"
    timeout 60 npm test 2>&1 | tail -20
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
      VALIDATION_FAILED=1
      echo "❌ Tests failed"
    else
      echo "✅ Tests passed"
    fi
  fi
fi

# Python projects
if [ -f requirements.txt ] || [ -f pyproject.toml ] || [ -f setup.py ]; then
  echo ""
  echo "## Python project detected - running Python validations"
  
  # Pytest
  if [ -f pytest.ini ] || [ -d tests ] || [ -d test ]; then
    echo ""
    echo "### Pytest"
    timeout 60 pytest --tb=short -q 2>&1 | tail -20
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
      VALIDATION_FAILED=1
      echo "❌ Pytest failed"
    else
      echo "✅ Pytest passed"
    fi
  fi
  
  # Type checking with mypy
  if [ -f mypy.ini ] || grep -q "mypy" requirements.txt 2>/dev/null; then
    echo ""
    echo "### Mypy Type Checking"
    mypy . --ignore-missing-imports 2>&1 | tail -10
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
      echo "⚠️  Type errors detected"
    else
      echo "✅ Type checking passed"
    fi
  fi
fi

# Go projects
if [ -f go.mod ]; then
  echo ""
  echo "## Go project detected - running Go validations"
  
  echo ""
  echo "### Go Build"
  go build ./... 2>&1 | tail -10
  if [ ${PIPESTATUS[0]} -ne 0 ]; then
    VALIDATION_FAILED=1
    echo "❌ Go build failed"
  else
    echo "✅ Go build passed"
  fi
  
  echo ""
  echo "### Go Test"
  timeout 60 go test ./... 2>&1 | tail -15
  if [ ${PIPESTATUS[0]} -ne 0 ]; then
    VALIDATION_FAILED=1
    echo "❌ Go tests failed"
  else
    echo "✅ Go tests passed"
  fi
fi

# Shell script validation
SHELL_SCRIPTS=$(find . -maxdepth 3 -name "*.sh" -type f 2>/dev/null | head -5)
if [ -n "$SHELL_SCRIPTS" ]; then
  echo ""
  echo "## Shell Scripts - Syntax Check"
  for script in $SHELL_SCRIPTS; do
    bash -n "$script" 2>&1
    if [ $? -ne 0 ]; then
      echo "❌ Syntax error in $script"
    fi
  done
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
if [ $VALIDATION_FAILED -eq 1 ]; then
  echo "❌ VALIDATION FAILED - Please fix the errors above"
  echo "Do not mark this task complete until validations pass."
else
  echo "✅ VALIDATION PASSED"
fi
echo "═══════════════════════════════════════════════════════════"

exit $VALIDATION_FAILED
