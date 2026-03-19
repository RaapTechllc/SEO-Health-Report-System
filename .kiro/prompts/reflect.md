# Reflect - Self-Improvement Analysis

Analyze the current session for corrections, errors, and patterns. Update LEARNINGS.md.

## Trigger Words
- "reflect"
- "what did we learn"
- "capture learnings"

## Process

### 1. Scan Session for Corrections
Look for patterns indicating user corrections:
- "no, use X instead of Y"
- "actually, do it this way"
- "that's wrong, it should be"
- "don't do X, do Y"
- "I said X not Y"
- Repeated attempts at same task
- Errors followed by different approach

### 2. Identify Each Learning Type

**Corrections** (mistakes to never repeat):
- Wrong tool/library used
- Incorrect syntax or API
- Misunderstood requirement

**Preferences** (user's preferred approach):
- Code style choices
- Tool preferences
- Workflow patterns

**Patterns** (reusable workflows):
- Multi-step processes done repeatedly
- Commands run in sequence
- Successful problem-solving approaches

**Anti-Patterns** (things that caused problems):
- Approaches that failed
- Tools that didn't work
- Assumptions that were wrong

### 3. Update LEARNINGS.md
For each learning found, append to appropriate section:
```markdown
- [YYYY-MM-DD] TYPE: "description"
```

### 4. Propose Template Updates
If learning applies broadly, suggest updates to:
- `CLAUDE.md` - Project-wide rules
- `.kiro/steering/*.md` - Steering files
- `.kiro/agents/*.json` - Agent prompts

### 5. Report Summary
```
## Session Reflection

### Corrections Captured: N
- [list each]

### Preferences Noted: N
- [list each]

### Patterns Discovered: N
- [list each]

### Proposed Template Updates:
- [file]: [change]

### Confidence: X/10
```

## Important
- Only capture REUSABLE learnings
- Skip one-time fixes or project-specific details
- Focus on "correct once, never again" items
- Ask for confirmation before updating templates
