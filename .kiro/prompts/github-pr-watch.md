# GitHub PR Watcher

Monitor PRs and trigger appropriate actions.

## Check PRs by State
```bash
gh pr list --label needs-review --json number,title
gh pr list --label approved --json number,title
gh pr list --label needs-fixes --json number,title
```

## Process Each Category

**needs-review:** Trigger code review swarm, update labels
**approved:** Verify checks pass, merge if ready
**needs-fixes:** Report status, wait for intervention

## Usage
Run periodically or on-demand: `@github-pr-watch`
