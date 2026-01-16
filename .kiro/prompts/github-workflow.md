# GitHub PR Workflow

Manage the full PR lifecycle: create, review, merge.

## Creating a PR
After implementation complete:
1. Commit all changes
2. Run: `bash .kiro/scripts/create-pr.sh "feat: [description]" "[body]"`

## Reviewing a PR
1. Check PRs: `gh pr list --label needs-review`
2. Trigger swarm: `@code-review-swarm PR [number]`
3. Results post as PR comment

## Handling Feedback
- **Critical** — Must fix before merge
- **Important** — Should fix
- **Suggestion** — Optional

## Merging
1. Check: `bash .kiro/scripts/check-pr-status.sh [number]`
2. Merge: `bash .kiro/scripts/merge-pr.sh [number] --squash`

## Labels
- `agent-created` — PR by agent
- `needs-review` — Awaiting review
- `needs-fixes` — Issues found
- `approved` — Ready to merge
- `blocked` — Cannot proceed
