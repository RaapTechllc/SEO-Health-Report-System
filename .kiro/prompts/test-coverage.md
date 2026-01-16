# Test Coverage Analysis

Analyze test coverage and identify gaps in the test suite.

## Analysis Steps

1. **Current Coverage**
   - Run existing tests
   - Identify coverage metrics
   - Find untested files/functions

2. **Critical Paths**
   - Authentication flows
   - Data mutations (create, update, delete)
   - API endpoints
   - Error handling paths

3. **Test Quality**
   - Are tests testing behavior or implementation?
   - Are there flaky tests?
   - Is test data realistic?

## Recommendations

For each gap identified:
- **File/Function**: What needs testing
- **Priority**: High/Medium/Low
- **Test Type**: Unit/Integration/E2E
- **Suggested Test**: Brief description of what to test

## Output

1. Coverage summary
2. Prioritized list of testing gaps
3. Suggested test implementations for top 3 gaps
