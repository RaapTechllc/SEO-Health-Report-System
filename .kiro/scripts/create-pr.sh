#!/bin/bash
# Create a PR from current branch
# Usage: create-pr.sh "PR Title" "PR Body" [base_branch]

TITLE="${1:-"Agent implementation"}"
BODY="${2:-"Automated PR created by orchestrator agent."}"
BRANCH=$(git branch --show-current)
BASE_BRANCH="${3:-main}"

if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "❌ Cannot create PR from main/master branch"
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️  Committing uncommitted changes..."
  git add -A
  git commit -m "chore: auto-commit before PR creation"
fi

echo "Pushing branch..."
git push -u origin "$BRANCH" 2>&1

echo "Creating PR..."
gh pr create --title "$TITLE" --body "$BODY" --base "$BASE_BRANCH" --label "agent-created,needs-review"
