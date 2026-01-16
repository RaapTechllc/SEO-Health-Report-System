# Create Product Requirement Document

Create a structured PRD with implementation phases for: $ARGUMENTS

## Process

1. **Analyze the request** - Understand what's being asked
2. **Research the codebase** - Find relevant files, patterns, dependencies
3. **Create the PRD** with all sections below

## Output: Save to `.kiro/specs/prds/{feature-slug}.prd.md`

---

## PRD Template

```markdown
# PRD: {Feature Name}

**Created:** {date}
**Status:** ACTIVE
**Author:** AI Orchestrator

## Goal

{What are we building? One paragraph max.}

## Why

{Business value, user impact. Why now?}

- Reason 1
- Reason 2
- Reason 3

## What

{Detailed feature description}

### Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

### Out of Scope

- Item 1
- Item 2

## Implementation Phases

| Phase | Description | Status | Dependencies | Estimated Effort |
|-------|-------------|--------|--------------|------------------|
| 1 | {phase 1 description} | PENDING | None | Small |
| 2 | {phase 2 description} | PENDING | Phase 1 | Medium |
| 3 | {phase 3 description} | PENDING | Phase 2 | Medium |

### Phase Details

#### Phase 1: {Name}
- Task 1.1: ...
- Task 1.2: ...
- Validation: {how to verify this phase is complete}

#### Phase 2: {Name}
- Task 2.1: ...
- Task 2.2: ...
- Validation: {how to verify this phase is complete}

#### Phase 3: {Name}
- Task 3.1: ...
- Task 3.2: ...
- Validation: {how to verify this phase is complete}

## Technical Context

### Relevant Files
- `path/to/file.ts` - {why relevant}
- `path/to/other.ts` - {why relevant}

### Dependencies
- Package 1: {version, purpose}
- Package 2: {version, purpose}

### Patterns to Follow
- {existing pattern 1}
- {existing pattern 2}

## Known Gotchas

<!-- Mark critical items that could derail implementation -->

> CRITICAL: {gotcha 1}

> CRITICAL: {gotcha 2}

> NOTE: {less critical consideration}

## Validation Strategy

### Level 1: Syntax & Style
```bash
npm run lint
npm run typecheck
```

### Level 2: Unit Tests
```bash
npm run test:unit
```

### Level 3: Integration
```bash
npm run test:integration
```

## Progress Log

| Date | Phase | Update |
|------|-------|--------|
| {date} | - | PRD created |

```

---

## Instructions

1. Fill in ALL sections of the template
2. Break down into 2-5 phases (not too granular)
3. Each phase should be independently valuable
4. Include file paths that you actually found
5. Mark dependencies between phases
6. Add CRITICAL notes for common mistakes
7. Save the file and confirm the path
