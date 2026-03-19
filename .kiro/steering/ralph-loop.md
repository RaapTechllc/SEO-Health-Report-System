# Ralph Loop Methodology

The Ralph Loop is an autonomous iteration pattern where agents work in cycles until task completion, with self-validation at each step.

## Core Concept

```
┌─────────────────────────────────────────────────────────┐
│                     RALPH LOOP                          │
├─────────────────────────────────────────────────────────┤
│  1. Load task from PLAN.md                              │
│  2. Execute task with available tools                   │
│  3. Validate work (tests, lint, type check)             │
│  4. Update PROGRESS.md with status                      │
│  5. If not done: Loop back to step 1                    │
│  6. If done: Output <promise>DONE</promise>             │
└─────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Completion Signal
Agents signal completion with:
```
<promise>DONE</promise>
```

For checkpoint pauses (C-threads):
```
<promise>CHECKPOINT</promise>
```

For full workflow completion:
```
<promise>COMPLETE</promise>
```

### 2. State Files

| File | Purpose |
|------|---------|
| `PLAN.md` | Task checklist with acceptance criteria |
| `PROGRESS.md` | Real-time status updates |
| `activity.log` | Execution timeline and events |

### 3. Validation Hooks

The Ralph Loop integrates validation at each iteration:
- **Lint check**: Code style compliance
- **Type check**: TypeScript/type safety
- **Tests**: Unit and integration tests
- **Build**: Compilation succeeds

## Implementation Patterns

### Basic Ralph Loop (Single Agent)
```bash
while ! grep -q "<promise>DONE</promise>" output.log; do
  run_iteration
  validate_work
  update_progress
done
```

### Parallel Ralph Loop (P-Thread)
```bash
for agent in $AGENTS; do
  run_ralph_loop $agent &
done
wait
merge_results
```

### Chained Ralph Loop (C-Thread)
```bash
for phase in $PHASES; do
  while ! phase_complete $phase; do
    run_iteration
  done
  wait_for_review
done
```

## Stop Hooks

Stop hooks intercept the completion signal to add validation:

```json
{
  "hooks": {
    "stop": [
      {
        "command": "npm run lint && npm run typecheck",
        "on_fail": "continue"
      }
    ]
  }
}
```

### Stop Hook Flow
```
Agent attempts to stop
       │
       v
┌─────────────────┐
│  Stop Hook      │
│  Runs           │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Pass?   │
    └────┬────┘
         │
    Yes  │  No
    ┌────┴────┐
    │         │
    v         v
  DONE    Continue
          Loop
```

## Best Practices

### 1. Clear Completion Criteria
Define exactly what "done" means in PLAN.md:
```markdown
## Task 1.1: Implement login form
- [ ] Form renders with email/password fields
- [ ] Validation shows errors for invalid input
- [ ] Submit calls API endpoint
- [ ] Success redirects to dashboard
- [ ] All tests pass
```

### 2. Incremental Progress Updates
Update PROGRESS.md after each meaningful action:
```markdown
### Task 1.1 Progress
- [x] Created LoginForm component (10:30)
- [x] Added validation logic (10:45)
- [ ] Implement API call (in progress)
```

### 3. Timeout Safeguards
Prevent infinite loops:
```bash
MAX_ITERATIONS=50
TIMEOUT_HOURS=4

iteration=0
while [ $iteration -lt $MAX_ITERATIONS ]; do
  # ... loop body
  ((iteration++))
done
```

### 4. Stall Detection
Re-spawn agents that show no progress:
```bash
STALL_THRESHOLD_MINUTES=15

check_progress() {
  last_update=$(stat -c %Y PROGRESS.md)
  now=$(date +%s)
  diff=$(( (now - last_update) / 60 ))
  
  if [ $diff -gt $STALL_THRESHOLD_MINUTES ]; then
    restart_agent
  fi
}
```

## Integration with Thread Types

| Thread Type | Ralph Loop Usage |
|-------------|------------------|
| Base | Single iteration, manual review |
| P-Thread | Parallel loops, coordinated completion |
| C-Thread | Loop per phase, checkpoint between |
| F-Thread | Multiple loops, fuse results |
| B-Thread | Orchestrator manages sub-loops |
| L-Thread | Extended loop duration |

## Monitoring

### Activity Log Format
```
2026-01-12 10:30:00: security-specialist - Starting iteration
2026-01-12 10:30:15: security-specialist - Running validation
2026-01-12 10:30:20: security-specialist - Validation passed
2026-01-12 10:30:25: security-specialist - COMPLETED all tasks
```

### Real-Time Monitoring
```bash
# Watch activity
tail -f activity.log

# Watch progress
tail -f PROGRESS.md

# Monitor all agents
watch -n 5 'cat agents/*/output.log | tail -20'
```

## Troubleshooting

### Agent Never Completes
- Check if completion criteria are achievable
- Verify `<promise>DONE</promise>` signal is being written
- Increase max_iterations if legitimately needs more time
- Check for blocking errors in output.log

### Agent Completes Too Early
- Tighten acceptance criteria in PLAN.md
- Add validation hooks (lint, test, typecheck)
- Require explicit verification steps

### Progress Stalls
- Check for tool failures in output.log
- Verify file permissions
- Ensure context isn't exceeding limits
- Restart with fresh context if needed

---

*"The Ralph Loop embodies the principle: agents plus code outperforms agents alone."*
