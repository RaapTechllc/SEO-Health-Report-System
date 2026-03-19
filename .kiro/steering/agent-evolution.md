# Agent Self-Evolution Protocol

This steering file defines the self-healing and continuous improvement protocol for all custom agents.

## Core Principle: Correct Once, Never Again

Every correction you make should be captured and applied permanently. LLMs don't learn between sessions - we must explicitly record learnings so they persist.

## The Self-Improvement System

### Key Files
- `LEARNINGS.md` - Captured corrections, preferences, patterns (project-level)
- `CLAUDE.md` - Applied rules that agents always follow
- `.kiro/steering/*.md` - Domain-specific guidance
- `~/.kiro/evolution/` - Global learnings across projects

### Capture Triggers
Capture a learning when:
1. User corrects you: "no, use X not Y"
2. You retry the same task multiple times
3. An approach fails and you try another
4. User expresses a preference
5. A workflow pattern emerges

### Learning Types

| Type | Marker | Example |
|------|--------|---------|
| Correction | `CORRECTION:` | "Use pnpm not npm" |
| Preference | `PREFER:` | "Always use TypeScript strict mode" |
| Pattern | `PATTERN:` | "Run lint before commit" |
| Anti-pattern | `AVOID:` | "Don't use any types" |

## Self-Reflection Trigger

At the end of any significant work session, reflect using RBT:

### 🌹 Roses (Strengths to Preserve)
- What worked well this session?
- Which tools were most effective?

### 🌱 Buds (Opportunities to Explore)
- What could be improved with minor tweaks?
- What patterns emerged that could be formalized?

### 🌵 Thorns (Failures to Fix)
- What errors occurred and why?
- What took longer than expected?

## Practical Implementation

### Manual Capture
After any correction, immediately update LEARNINGS.md:
```bash
# Using the self-improve script
./.kiro/workflows/self-improve.sh add correction "Use pnpm not npm"
./.kiro/workflows/self-improve.sh add pattern "Always run typecheck before commit"
```

### Automatic Capture
Use the `@reflect` prompt at session end:
```
@reflect
```
This analyzes the session and proposes learnings to capture.

### Applying Learnings
Periodically review LEARNINGS.md and promote important items:
1. **High-frequency corrections** → Add to CLAUDE.md
2. **Domain-specific patterns** → Add to relevant steering file
3. **Agent-specific learnings** → Update agent's prompt

### Commands
```bash
# Scan logs for potential learnings
./.kiro/workflows/self-improve.sh scan

# View learning statistics
./.kiro/workflows/self-improve.sh stats

# View improvement history
./.kiro/workflows/self-improve.sh history
```

## Self-Healing Behaviors

### On Error Detection
When an agent encounters an error:
1. Log the error context and stack trace
2. Attempt self-diagnosis using available tools
3. If fixable, apply the fix and continue
4. If not fixable, document the failure pattern for future prevention

### On Tool Failure
When a tool doesn't work as expected:
1. Check if the tool exists and is properly configured
2. Verify permissions and paths
3. Suggest tool additions or configuration changes
4. Document workarounds that succeeded

### On Context Gaps
When missing information causes problems:
1. Identify what information was needed
2. Suggest resources to add to agent config
3. Propose steering file additions for common patterns

## Improvement Categories

### Prompt Evolution
- Add specific instructions for common failure modes
- Include examples of good outputs
- Add constraints that prevent past mistakes
- Refine workflow descriptions

### Tool Evolution
- Add tools that would have helped
- Remove tools that cause confusion
- Adjust tool permissions for efficiency
- Configure tool settings for common patterns

### Resource Evolution
- Add files that provide useful context
- Remove resources that add noise
- Adjust glob patterns for better coverage

## Guardrails

### Core Identity Protection
Never modify these aspects of an agent:
- The agent's fundamental purpose
- Security-critical constraints
- Model selection (unless explicitly requested)

### Change Limits
- Maximum 3 prompt additions per session
- Maximum 2 tool changes per session
- All changes must be reversible

### Human Review Triggers
Flag for human review when:
- Confidence score < 5
- Change affects security settings
- Multiple consecutive failures on same issue
- Proposed change contradicts existing instructions

## Integration with Hooks

Agents can use hooks to automate evolution:

```json
{
  "hooks": {
    "stop": [
      {
        "command": "echo 'Session complete. Initiating self-reflection...'"
      }
    ]
  }
}
```

## Continuous Improvement Cycle

```
┌─────────────────────────────────────────────────────────┐
│                    AGENT SESSION                         │
├─────────────────────────────────────────────────────────┤
│  1. Execute task with current configuration             │
│  2. Monitor for errors, friction, and successes         │
│  3. At session end, trigger RBT reflection              │
│  4. Record insights to evolution log                    │
│  5. Propose specific improvements                       │
│  6. Apply high-confidence changes (or flag for review)  │
│  7. Next session benefits from improvements             │
└─────────────────────────────────────────────────────────┘
```

---

*"The Ralph Loop embodies the principle: agents plus code outperforms agents alone."*
