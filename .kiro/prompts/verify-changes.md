# Verify Changes Prompt

You are responsible for verifying that code changes don't introduce regressions through automated testing.

## Task
Run the appropriate test suite to verify recent changes and ensure system stability.

## Testing Strategy

### Phase 1: Smoke Tests (Fast Validation)
Run the smoke test suite first for quick feedback:
```bash
python3 -m pytest tests/smoke/ -x --tb=short -v
```

**Success Criteria:**
- All smoke tests pass
- Execution time < 60 seconds
- No critical path failures

### Phase 2: Full Test Suite (Comprehensive Validation)
If smoke tests pass, run the full test suite:
```bash
python3 -m pytest tests/ --tb=short -v
```

**Success Criteria:**
- All tests pass
- No new test failures introduced
- Performance within acceptable bounds

## Failure Response Protocol

### When Tests Fail
1. **Capture failure details**: Test names, error messages, stack traces
2. **Trigger RCA analysis**: Invoke `@rca` prompt with failure information
3. **Block further execution**: Do not proceed until issues are resolved

### RCA Trigger Format
```
@rca

Test failures detected during verification:

**Failed Tests:**
- test_name_1: error_message_1
- test_name_2: error_message_2

**Full Output:**
[paste complete test output]

Please analyze and provide:
1. Root cause of failures
2. Immediate fix recommendations  
3. Prevention strategies
```

## Output Format

Provide structured results:

```json
{
  "verification_status": "pass|fail|partial",
  "smoke_tests": {
    "status": "pass|fail",
    "test_count": 5,
    "duration_seconds": 12.3,
    "failures": []
  },
  "full_suite": {
    "status": "pass|fail|skipped",
    "test_count": 150,
    "duration_seconds": 45.7,
    "failures": []
  },
  "recommendation": "proceed|fix_required|investigate"
}
```

## Success Actions
- **All tests pass**: Log success and allow workflow to continue
- **Smoke tests pass, full suite skipped**: Acceptable for rapid iteration
- **Any failures**: Block execution and require manual intervention

## Performance Monitoring
- Track test execution times
- Alert if smoke tests exceed 60 seconds
- Alert if full suite exceeds 10 minutes
