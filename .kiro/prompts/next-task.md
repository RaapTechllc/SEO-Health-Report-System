# Next Task

Continue to the next task in the current spec workflow.

## Prerequisites
- Active spec in `.kiro/specs/[feature-name]/`
- `tasks.md` exists with task list
- Previous task completed or this is first task

## Workflow

1. **Load Context**
   - Read `tasks.md` to find next uncompleted task
   - Read only files relevant to that specific task
   - Do NOT load entire codebase

2. **Execute Task**
   - Focus on ONE task only
   - Follow acceptance criteria exactly
   - Delegate to specialist if beneficial:
     - Tests → `test-architect`
     - UI → `frontend-designer`
     - DB → `db-wizard`
     - Docs → `doc-smith`

3. **Verify**
   - Check against acceptance criteria
   - Run relevant tests if applicable
   - Update task status in `tasks.md`

4. **Report**
   - Brief summary of what was done
   - Any issues encountered
   - Propose next task but WAIT for confirmation

## Task Status Format

```markdown
- [x] Task 1: [Title] ✅ Completed
- [ ] Task 2: [Title] ← Current
- [ ] Task 3: [Title]
```

## Important

- NEVER auto-continue to next task
- ALWAYS wait for user confirmation
- Keep summaries brief (3-5 lines)
