# Strands Review

Context efficiency review using deletion hierarchy.

## Usage

```
@strands-review [target]
```

**Examples:**
- `@strands-review src/` - Review entire src directory
- `@strands-review --changed` - Review files changed since last commit
- `@strands-review src/auth/` - Review specific module

## What It Does

1. Analyzes target for context efficiency
2. Applies deletion hierarchy: Question → Delete → Simplify → Accelerate → Automate
3. Outputs actionable tasks sorted by impact
4. Calculates context density score

## Output

Produces categorized findings:
- **DELETE** - Remove immediately
- **CONSOLIDATE** - Merge duplicates
- **SIMPLIFY** - Reduce complexity
- **KEEP** - Justified code

## Integration

After review, if issues found:
```
@code-review-fix [strands-review output]
```

## Prompt

Review the following for context efficiency. Apply the deletion hierarchy strictly.

Target: {{target}}

Questions to answer:
1. What can be deleted with zero impact?
2. What duplicates can be consolidated?
3. What abstractions cost more than they save?
4. What's the overall context density score?

Use `git diff HEAD~5` to focus on recent changes if `--changed` flag used.

Output format per the strands-agent specification.

End with: "The best part is no part."
