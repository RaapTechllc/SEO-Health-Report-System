# Workflow Status

Check the current status of all active spec workflows.

## Output Format

```markdown
## Active Specs

### [Feature Name]
- **Phase**: Requirements | Design | Tasks | Implementation
- **Progress**: X/Y tasks completed
- **Next Action**: [What needs to happen next]
- **Blockers**: [Any blocking issues]

### [Another Feature]
...

## Recently Completed
- [Feature] - Completed [date]
```

## Checks

1. Scan `.kiro/specs/` for all feature directories
2. For each spec:
   - Check which files exist (requirements.md, design.md, tasks.md)
   - Count completed vs total tasks
   - Identify current phase
   - Note any open questions or blockers

## Quick Actions

After showing status, offer:
- "Continue [feature]" - Resume work on a spec
- "Review [feature]" - Show details of a spec
- "Archive [feature]" - Mark as complete
