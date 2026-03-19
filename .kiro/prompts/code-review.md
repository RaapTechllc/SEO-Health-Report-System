# Code Review

Routes to appropriate review method based on scope.

## Routing

**Use Swarm Review (@code-review-swarm) when:**
- Reviewing a PR
- Reviewing a feature branch
- Changes span multiple files
- User requests "thorough" or "comprehensive" review

**Use Quick Review (inline) when:**
- Single file change
- User requests "quick" review
- Hotfix or small patch

## Quick Review Process

For small changes, review inline without spawning subagents:
1. Get the diff
2. Check for obvious issues across all categories
3. Provide brief feedback

## Default

Default to swarm review for anything more than 50 lines changed.
