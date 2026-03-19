# Ralph PRD - Interactive Planning

You are creating a Product Requirements Document through structured dialogue.
This process ensures comprehensive planning before any implementation begins.

## Mode Selection

First, determine which mode to use:

**Quick Mode** — User says "quick", "fast", or provides extensive context upfront
**Interactive Mode** — Default. Use when context seems incomplete.

---

## Interactive Mode Process

Ask these questions ONE AT A TIME. Wait for each answer before proceeding.

### Question 1: Goal
"What is the main goal of this feature/task? What does success look like when it's complete?"

### Question 2: Requirements
"What are the specific requirements? Are there any hard constraints (tech stack, performance, compatibility)?"

### Question 3: Scope Boundaries
"What is explicitly OUT of scope? What should this NOT do or change?"

### Question 4: Dependencies
"What dependencies or blockers exist? Does this require other work to be completed first?"

### Question 5: Validation
"How will we know it's working? What tests or checks validate success?"

### Question 6: Risks
"What could go wrong? What's the rollback plan if this breaks something?"

---

## After All Questions Answered

Generate the PRD in this format:

```markdown
# PRD: [Feature Name]

**Created:** [Date]
**Status:** Draft
**Author:** Orchestrator + [Human Name if provided]

## Problem Statement
[1-2 sentences describing the problem this solves]

## Success Criteria
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]
- [ ] [Measurable outcome 3]

## Requirements

### Must Have
- [Requirement 1]
- [Requirement 2]

### Should Have
- [Requirement 3]

### Out of Scope
- [Explicitly excluded item 1]
- [Explicitly excluded item 2]

## Technical Approach
[High-level description of how this will be built]

### Components Affected
- [File/Module 1]
- [File/Module 2]

### Dependencies
- [Dependency 1]
- [Dependency 2]

## Task Breakdown

### Phase 1: [Name]
- [ ] Task 1.1 — [Description] (~[estimate])
- [ ] Task 1.2 — [Description] (~[estimate])

### Phase 2: [Name]
- [ ] Task 2.1 — [Description] (~[estimate])
- [ ] Task 2.2 — [Description] (~[estimate])

## Testing Strategy
- [ ] [Test type 1]: [What it validates]
- [ ] [Test type 2]: [What it validates]

## Risks & Mitigation
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | Low/Med/High | Low/Med/High | [How to handle] |

## Rollback Plan
[Steps to undo this change if needed]
```

---

## Quick Mode Process

When in quick mode, skip the questions and generate the PRD directly from provided context.
Still include all sections, marking unknowns as "TBD - clarify before implementation".

---

## Output Location

Save the generated PRD to: `artifacts/plans/[feature-slug].md`

After saving, ask: "PRD saved. Ready to proceed with implementation, or would you like to revise any section?"
