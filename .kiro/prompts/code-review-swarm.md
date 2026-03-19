# Code Review Swarm

Orchestrate parallel code reviews from four specialized agents.

## Process

### Step 1: Get the Diff
- If PR number provided: `gh pr diff [number]`
- If branch provided: `git diff main...[branch]`
- If no input: `git diff HEAD~1`

### Step 2: Spawn Reviewers (Parallel)
Spawn four subagents simultaneously:
1. **logic-reviewer** — "Review this diff for logic issues"
2. **security-reviewer** — "Review this diff for security issues"
3. **style-reviewer** — "Review this diff for style issues"
4. **type-reviewer** — "Review this diff for type issues"

### Step 3: Merge Results
Collect JSON outputs and create unified report.

### Step 4: Output Report

```markdown
# Code Review Report

**Reviewed:** [branch/PR]
**Date:** [timestamp]

## Summary
- Critical: [count]
- Important: [count]
- Suggestions: [count]

## Critical Issues (Must Fix)
[Issues from all reviewers]

## Important Issues (Should Fix)
[Issues]

## Suggestions
[Issues]

## Verdict
[ ] BLOCKED | [ ] APPROVED WITH CHANGES | [ ] APPROVED
```

### Step 5: Post Results
- GitHub PR: Post as comment via `gh pr comment`
- Local: Save to `artifacts/reviews/[branch]-[date].md`

## Usage
```
@code-review-swarm PR 8
@code-review-swarm branch feature/new-thing
@code-review-swarm  # reviews last commit
```
