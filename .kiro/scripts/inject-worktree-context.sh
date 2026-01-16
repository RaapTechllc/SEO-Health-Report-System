#!/bin/bash
# Enhanced context for worktree environments
# Used by Ralph loop and parallel execution agents

echo "═══════════════════════════════════════════════════════════"
echo "WORKTREE AGENT CONTEXT"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "## Environment"
echo "Working Directory: $(pwd)"
echo "Git Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
echo "Git Root: $(git rev-parse --show-toplevel 2>/dev/null || echo 'unknown')"
echo ""

# Check if we're in a worktree
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  WORKTREE_ROOT=$(git rev-parse --show-toplevel)
  MAIN_WORKTREE=$(git worktree list | head -1 | awk '{print $1}')
  
  if [ "$WORKTREE_ROOT" != "$MAIN_WORKTREE" ]; then
    echo "## Worktree Status: ISOLATED WORKTREE"
    echo "Main Repository: $MAIN_WORKTREE"
    echo "Current Worktree: $WORKTREE_ROOT"
    echo ""
    echo "⚠️  YOU ARE IN AN ISOLATED WORKTREE"
    echo "⚠️  Do NOT run: git checkout, git switch, cd .."
    echo "⚠️  Stay in this directory and complete your task"
  else
    echo "## Worktree Status: MAIN REPOSITORY"
  fi
fi

echo ""
echo "## Task Assignment"
if [ -f PLAN.md ]; then
  echo "Plan file found. Current tasks:"
  grep -E "^- \[ \]" PLAN.md | head -10
else
  echo "No PLAN.md - check for task in conversation context"
fi

echo ""
echo "## Recent Activity"
if [ -f PROGRESS.md ]; then
  echo "Last 10 progress entries:"
  tail -10 PROGRESS.md
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
