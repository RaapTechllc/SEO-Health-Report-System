---
description: End-of-session memory capture - update devlog, steering, and knowledge
---

# Memory: End-of-Session Capture

## Purpose

Lock in learnings from this session so the next `@plan-feature` is better. Update persistent documentation with what happened, what was decided, and what changed.

## Inputs to Read

Before updating anything, read these files:

1. **DEVLOG.md** (or `examples/DEVLOG.md`) - create if missing
2. **The plan file used this session** - ask me for path if unknown
3. **`.agents/execution-reports/*`** - newest relevant file (if exists)
4. **`.agents/system-reviews/*`** - newest relevant file (if exists)

## Outputs to Update

### 1. DEVLOG.md

Append a new entry with:

```markdown
## [DATE] - [Session Summary Title]

### What We Attempted
- [Goal or feature worked on]

### What Shipped
- [Concrete deliverables completed]
- [Files created/modified]

### Decisions Made
- [Decision]: [Rationale]
- [Decision]: [Rationale]

### Risks Introduced or Removed
- [+/-] [Risk description]

### Follow-ups / TODOs
- [ ] [Action item]
- [ ] [Action item]

### Technical Notes
- [Any gotchas discovered]
- [Patterns that worked well]
```

### 2. Steering Documents (only if stable rules emerged)

Update or create in `.kiro/steering/`:

**Update `tech.md` if:**
- Architecture decisions changed
- New technology constraints discovered
- Performance requirements clarified
- Security patterns established

**Update `structure.md` if:**
- Folder conventions changed
- File naming patterns established
- Module organization clarified

**Create new steering doc if:**
- Discovered a repeatable rule (e.g., `testing.md`, `api-standards.md`, `error-handling.md`)
- Found patterns that should apply to all future work

### 3. Knowledge Base (if enabled)

If `/knowledge` is available:
- Add key docs from this session (plan, reports)
- Index new reference material discovered
- Note: `kiro-cli settings chat.enableKnowledge true` to enable

## Quality Bar

- Keep updates short and specific
- Prefer checklists and bullet points
- Don't restate obvious things
- Mark uncertain items as "Assumption: [X]"
- Include file paths for traceability

## Patch Criteria (token waste + stability)

Only patch prompts when the change reduces repeat token waste across projects.

**A patch is allowed if it fixes one of these:**
- Missing prerequisites (install, env vars, services, migrations)
- Missing "Inputs/Outputs" causing back-and-forth
- Missing acceptance criteria causing rework
- Missing quality gates causing failures late (tests/typecheck/lint)
- Missing "where to write artifacts" causing drift
- Missing safety rules (authz, validation, secrets)

**A patch is NOT allowed if it:**
- Encodes a one-off decision or naming convention unique to this repo
- Hardcodes app-specific paths (except template-standard paths like DEVLOG.md)
- Adds extra steps that most projects won't need

## Two-Strike or High-Impact Rule

Apply a prompt patch only if:
- The issue happened at least **twice** across sessions, OR
- The issue is **high-impact** (blocked progress, broke builds, security risk)

**Default bias: Conservative** - Don't patch on first occurrence unless it blocked work or caused security/build failures.

## Production Checks

Before finishing, verify:

- [ ] DEVLOG entry includes what shipped (not just what was attempted)
- [ ] Any new patterns are documented in steering
- [ ] Risks are explicitly called out
- [ ] Follow-ups have owners or are actionable
- [ ] No sensitive data in documentation

## Finish

Print a short summary:

```
✅ Memory Updated

Files Modified:
- DEVLOG.md (added: [session title])
- .kiro/steering/tech.md (updated: [what])
- [other files]

Next session starts here: [1-sentence summary of where to pick up]
```

## Integration with @plan-feature

This prompt is designed to run at the END of a session. The workflow is:

1. `@plan-feature` → creates plan with "End-of-session" section
2. `@execute` → implements the plan
3. `@code-review` → validates quality
4. `@execution-report` → documents what happened
5. `@system-review` → identifies process improvements
6. **`@memory`** → captures learnings, updates docs

The plan's "End-of-session" section tells `@memory` what to capture.
