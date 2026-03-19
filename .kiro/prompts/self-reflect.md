# Self-Reflection Prompt

Trigger the agent self-evolution protocol using the RBT (Roses, Buds, Thorns) framework.

## When to Use
- At the end of a significant work session
- After completing a major task
- When encountering repeated errors
- When explicitly asked to reflect

## Reflection Process

### 1. Session Context
Document:
- Project name
- Task attempted
- Approximate duration
- Tools used

### 2. RBT Analysis

#### 🌹 Roses (What Worked)
- Successful patterns
- Effective tool usage
- Good outcomes

#### 🌱 Buds (Opportunities)
- Minor improvements possible
- Tools that would help
- Patterns to formalize

#### 🌵 Thorns (Failures)
- Errors encountered
- Time wasted
- Confusion points

### 3. Proposed Changes
Based on the analysis, propose:
- Prompt improvements
- Tool recommendations
- Resource suggestions

### 4. Confidence Score
Rate 1-10 how confident you are the changes will help.

## Output Location
Record insights to:
```
~/.kiro/evolution/[agent-name]-evolution.md
```

## Example Entry

```markdown
## Session: [Date] - [Brief Description]

### Context
- Project: [project name]
- Task: [what was attempted]
- Duration: [time spent]

### RBT Analysis

#### 🌹 Roses
- [What worked well]

#### 🌱 Buds
- [Improvement opportunities]

#### 🌵 Thorns
- [Failures and friction]

### Proposed Changes
[Specific improvements]

### Confidence Score
[1-10]
```

## Guardrails
- Maximum 3 prompt additions per session
- Maximum 2 tool changes per session
- Flag for human review if confidence < 5
