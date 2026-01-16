#!/bin/bash
# Merge a PR after validation
# Usage: merge-pr.sh [PR_NUMBER] [--squash|--rebase|--merge]

PR_NUMBER="${1:-$(gh pr view --json number -q '.number' 2>/dev/null)}"
MERGE_METHOD="${2:---squash}"

if [ -z "$PR_NUMBER" ]; then
  echo "❌ No PR number provided"
  exit 1
fi

MERGEABLE=$(gh pr view "$PR_NUMBER" --json mergeable -q '.mergeable')
if [ "$MERGEABLE" != "MERGEABLE" ]; then
  echo "❌ PR is not mergeable (status: $MERGEABLE)"
  exit 1
fi

echo "Merging PR #$PR_NUMBER..."
gh pr merge "$PR_NUMBER" "$MERGE_METHOD" --delete-branch
