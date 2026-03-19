---
description: Fix issues found in code review
---

# Code Review Fix

## Purpose

Fix issues identified in a code review, one by one, with tests to verify each fix.

## Inputs to Read

1. **Code review file or description**: `$ARGUMENTS` (ask if not provided)
2. **Scope**: Which files/areas to focus on (ask if not provided)

## Process

### 1. Understand Issues

Read the code review file (if provided) to understand all issues:
- Severity of each issue
- File and line locations
- Suggested fixes

### 2. Fix Each Issue

For each issue, in order of severity (critical → high → medium → low):

1. **Explain** what was wrong
2. **Implement** the fix
3. **Add/update tests** to verify the fix
4. **Run tests** to confirm

### 3. Validate All Fixes

After all fixes:
```bash
# Run linting
[project-specific lint command]

# Run type checking
[project-specific typecheck command]

# Run tests
[project-specific test command]
```

## Outputs

### Fix Report

Save to: `.agents/code-review-fixes/[review-name]-fixes.md`

```markdown
# Code Review Fixes

## Review Source
- File: [path to review or "verbal description"]
- Date: [date]

## Issues Fixed

### Issue 1: [title]
- **Severity**: [critical/high/medium/low]
- **File**: [path]
- **Problem**: [what was wrong]
- **Fix**: [what was changed]
- **Test**: [test added/updated]

### Issue 2: [title]
...

## Validation Results
- Lint: ✓/✗
- Types: ✓/✗
- Tests: ✓/✗ [X passed, Y failed]

## Files Modified
- [list of files]
```

## Quality Gates

- [ ] All critical/high issues fixed
- [ ] Tests added for each fix
- [ ] All tests pass
- [ ] Lint/typecheck clean
- [ ] No new issues introduced

## Finish

Print summary:
```
✅ Code Review Fixes Complete

Issues fixed: X (Y critical, Z high, W medium)
Tests added: N
Files modified: [list]

Ready for: @code-review (re-review) or commit
```
