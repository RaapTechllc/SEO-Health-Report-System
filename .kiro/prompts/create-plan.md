# Create Implementation Plan from PRD

Generate a detailed implementation plan for the next pending phase.

## Arguments: $ARGUMENTS

The argument should be a path to a PRD file, e.g.:
`.kiro/specs/prds/user-auth.prd.md`

## Process

1. **Read the PRD** at the specified path
2. **Find the next PENDING phase** in the Implementation Phases table
3. **Research the codebase** for context needed
4. **Create detailed plan** with tasks, validation, and gotchas

## Output: Save to `.kiro/specs/plans/{feature}-phase-{n}.plan.md`

---

## Plan Template

```markdown
# Implementation Plan: {Feature} - Phase {N}

**Source PRD:** {path to PRD}
**Phase:** {N} of {total}
**Created:** {date}
**Status:** IN_PROGRESS

## Phase Goal

{What this phase accomplishes - from PRD}

## Prerequisites

- [ ] Phase {N-1} complete (if applicable)
- [ ] {Other prerequisite}

## All Needed Context

### Files to Modify
```
path/to/file1.ts    # {what changes needed}
path/to/file2.ts    # {what changes needed}
```

### Files to Create
```
path/to/new-file.ts # {purpose}
```

### Reference Files (read-only)
```
path/to/reference.ts # {why helpful}
```

### Documentation
- url: {relevant doc URL}
  section: {specific section}
  why: {why needed}

### Code Patterns

{Show existing patterns to follow}

```typescript
// Example from codebase showing the pattern
```

## Tasks

### Task 1: {Name}
- [ ] Subtask 1.1
- [ ] Subtask 1.2
- **Validation:** `{command to verify}`

### Task 2: {Name}
- [ ] Subtask 2.1
- [ ] Subtask 2.2
- **Validation:** `{command to verify}`

### Task 3: {Name}
- [ ] Subtask 3.1
- [ ] Subtask 3.2
- **Validation:** `{command to verify}`

## Known Gotchas

> CRITICAL: {Must handle this or implementation will fail}

> CRITICAL: {Another critical consideration}

> NOTE: {Less critical but worth noting}

## Validation Loop

### After Each Task
```bash
npm run lint
npm run typecheck
```

### After All Tasks
```bash
npm run test:unit
npm run test:integration
```

### Manual Verification
{Steps to manually verify the phase works}

## Completion Criteria

This phase is COMPLETE when:
1. [ ] All tasks checked off
2. [ ] All validation commands pass
3. [ ] {Phase-specific criterion}
4. [ ] {Phase-specific criterion}

## Notes

{Any additional context the implementer should know}
```

---

## Instructions

1. Read the PRD file completely
2. Identify the next PENDING phase
3. Research files mentioned + any others needed
4. Break the phase into 3-7 concrete tasks
5. Each task must have validation
6. Include actual code patterns from the codebase
7. Add CRITICAL gotchas from your research
8. Save the plan file
9. Update the PRD's phase status to IN_PROGRESS
