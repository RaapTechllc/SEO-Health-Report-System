# Context Efficiency Standards

Code quality = Value delivered / Context consumed

## Hard Limits

| Metric | Limit | Action if Exceeded |
|--------|-------|-------------------|
| Function LOC | 50 | Split or simplify |
| File LOC | 300 | Split into modules |
| Cyclomatic complexity | 10 | Refactor |
| Import count per file | 15 | Consolidate deps |
| Nesting depth | 3 | Flatten logic |

## Context Density Targets

| File Type | Target Score | Notes |
|-----------|--------------|-------|
| Core business logic | 9-10 | Every line essential |
| API routes | 7-8 | Minimal boilerplate |
| Tests | 6-7 | Clear, not clever |
| Config | 8-9 | No unused options |
| Utils/helpers | 7-8 | Reused 3+ times |
| Types/interfaces | 8-9 | Add safety, not ceremony |

## Deletion Review Required

Before any PR:
1. Run `@strands-review` on changed files
2. Address all DELETE items
3. Justify any CONSOLIDATE items not addressed
4. Context density score must be ≥6

## Red Flags (Auto-reject)

- [ ] Unused imports
- [ ] Commented-out code
- [ ] TODO without issue link
- [ ] Console.log in production code
- [ ] Any `any` type without comment
- [ ] Functions >50 LOC
- [ ] Files >300 LOC

## Acceptable Exceptions

Document in code comment if:
- External API requires verbose handling
- Performance-critical section needs unrolled code
- Legacy compatibility requires duplication

Format: `// STRANDS-EXCEPTION: [reason]`

## Weekly Cleanup

Every Friday:
1. Run full codebase strands review
2. Create cleanup PR for DELETE items
3. Track context density trend
