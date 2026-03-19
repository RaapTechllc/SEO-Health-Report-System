# Plan Feature

Intelligent planning that adapts to your input.

## Routing Logic

Analyze the user's request:

**Route to Interactive PRD (@ralph-prd) when:**
- Request is vague or high-level ("build a login system")
- Missing key details (no success criteria, no scope boundaries)
- User explicitly asks for "thorough" or "detailed" planning
- Complex feature spanning multiple components

**Route to Quick Plan (@create-plan) when:**
- User says "quick" or "fast"
- Comprehensive context already provided
- Simple, well-defined task
- User provides explicit requirements list

## Default Behavior

If uncertain, ask: "Would you like a quick plan from what you've provided, or should we go through the interactive PRD process to ensure nothing is missed?"

## Integration with Execution

After planning completes:
1. Plan is saved to appropriate location
2. Offer to begin execution with `@execute`
3. Or create worktree for parallel execution with `@create-shard`

---

## Full SPEC Workflow (when using @ralph-prd)

### Phase 1: Requirements
Create `.kiro/specs/[feature-name]/requirements.md` with:

```markdown
# Requirements - [Feature Name]

## Overview
[One paragraph describing the feature and its value]

## User Stories

### US-1: [Story Title]
**As a** [user type]
**I want** [capability]
**So that** [benefit]

**Acceptance Criteria (EARS):**
- WHEN [trigger], THE SYSTEM SHALL [response]
- IF [condition], THEN [behavior]
- THE SYSTEM SHALL [capability] WITHIN [constraint]

## Functional Requirements
- FR-1: [Requirement]
- FR-2: [Requirement]

## Non-Functional Requirements
- NFR-1: Performance - [constraint]
- NFR-2: Security - [constraint]
- NFR-3: Accessibility - [constraint]

## Out of Scope
- [What this feature does NOT include]

## Open Questions
- [ ] [Decision needed]
```

### Phase 2: Design (after approval)
Create `.kiro/specs/[feature-name]/design.md`

### Phase 3: Tasks (after design approval)
Create `.kiro/specs/[feature-name]/tasks.md`

### Phase 4: Implementation (task by task)
Execute one task at a time with specialist delegation

## Approval Gates

Wait for explicit approval before each phase transition:
- "requirements approved" → Design
- "design approved" → Tasks  
- "start task 1" → Implementation
