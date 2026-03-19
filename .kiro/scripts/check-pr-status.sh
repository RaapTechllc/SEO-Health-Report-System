#!/bin/bash
# Check status of a PR
# Usage: check-pr-status.sh [PR_NUMBER]

PR_NUMBER="${1:-$(gh pr view --json number -q '.number' 2>/dev/null)}"

if [ -z "$PR_NUMBER" ]; then
  echo "No PR found for current branch"
  exit 1
fi

echo "PR #$PR_NUMBER Status"
echo "═══════════════════════"
gh pr view "$PR_NUMBER" --json title,state,labels,mergeable \
  --template 'Title: {{.title}}
State: {{.state}}
Mergeable: {{.mergeable}}
Labels: {{range .labels}}{{.name}} {{end}}
'
