# Execute Implementation Plan

Execute a plan file and implement all tasks with validation.

## Arguments: $ARGUMENTS

The argument should be a path to a plan file, e.g.:
`.kiro/specs/plans/user-auth-phase-1.plan.md`

## Execution Rules

### 1. Read and Understand
- Read the entire plan file
- Understand the phase goal
- Review all context files listed
- Note the CRITICAL gotchas

### 2. Execute Tasks Sequentially
For EACH task in the plan:

```
┌─────────────────────────────────────────────────────────────┐
│  TASK EXECUTION LOOP                                        │
├─────────────────────────────────────────────────────────────┤
│  1. Read task requirements                                  │
│  2. Implement the task                                      │
│  3. Run task-specific validation                            │
│  4. If validation fails:                                    │
│     - Analyze the error                                     │
│     - Fix the issue                                         │
│     - Re-run validation                                     │
│     - Repeat until passing                                  │
│  5. Check off the task in the plan file                     │
│  6. Update PROGRESS.md                                      │
│  7. Move to next task                                       │
└─────────────────────────────────────────────────────────────┘
```

### 3. Validate Continuously
After EVERY file change:
```bash
npm run lint
npm run typecheck
```

Do NOT proceed to the next task if these fail.

### 4. Handle Failures
If you get stuck on a task:
1. Note the specific error
2. Check gotchas - is this a known issue?
3. Search codebase for similar patterns
4. Try alternative approach
5. If still stuck after 3 attempts, document blocker and continue

### 5. Completion
When all tasks are done:

1. Run final validation:
```bash
npm run lint
npm run typecheck
npm run test:unit
npm run test:integration
```

2. Verify all completion criteria from the plan

3. Update the source PRD:
   - Change phase status from IN_PROGRESS to COMPLETE
   - Add entry to Progress Log table

4. Archive the plan:
```bash
mv {plan-path} .kiro/specs/plans/completed/
```

5. Create implementation report:
   Save to `.kiro/specs/reports/{feature}-phase-{n}-report.md`

6. Output completion signal:
```
<promise>DONE</promise>
```

## Report Template

```markdown
# Implementation Report: {Feature} - Phase {N}

**Completed:** {date}
**Duration:** {time estimate}

## Summary
{1-2 sentences on what was accomplished}

## Changes Made

### Files Created
- `path/to/file.ts` - {purpose}

### Files Modified
- `path/to/file.ts` - {what changed}

## Validation Results

```
✓ Lint: passed
✓ Typecheck: passed
✓ Unit tests: X/Y passed
✓ Integration: passed
```

## Issues Encountered
- {Issue 1}: {how resolved}
- {Issue 2}: {how resolved}

## Next Steps
{What the next phase should address}
```

---

## IMPORTANT

- Do NOT skip validation steps
- Do NOT mark tasks complete before validation passes
- Do NOT output `<promise>DONE</promise>` until ALL criteria met
- DO update PROGRESS.md after each task
- DO check off tasks as you complete them
- DO handle errors gracefully - fix before moving on
