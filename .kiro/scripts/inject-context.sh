#!/bin/bash
# Context injection script for agent spawn
# Outputs context information for the agent to consume

echo "═══════════════════════════════════════════════════════════"
echo "AGENT CONTEXT INJECTION"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "## Working Directory"
pwd
echo ""
echo "## Git Branch"
git branch --show-current 2>/dev/null || echo "Not in a git repository"
echo ""
echo "## Git Status (brief)"
git status --short 2>/dev/null | head -10
echo ""
echo "## Active Plan"
if [ -f PLAN.md ]; then
  head -40 PLAN.md
else
  echo "No PLAN.md found in current directory"
fi
echo ""
echo "## Current Progress"
if [ -f PROGRESS.md ]; then
  tail -25 PROGRESS.md
else
  echo "No PROGRESS.md found in current directory"
fi
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "IMPORTANT: You are in an isolated environment."
echo "DO NOT switch branches or navigate to parent directories."
echo "Complete your assigned task within this context."
echo "═══════════════════════════════════════════════════════════"
