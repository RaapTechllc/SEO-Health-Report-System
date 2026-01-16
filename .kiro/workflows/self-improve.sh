#!/bin/bash
# self-improve.sh - Automated self-improvement system
# Analyzes session logs, extracts learnings, and updates templates

set -e

#===============================================================================
# CONFIGURATION
#===============================================================================

LEARNINGS_FILE="LEARNINGS.md"
CLAUDE_FILE="CLAUDE.md"
ACTIVITY_LOG="activity.log"
IMPROVEMENT_LOG=".kiro/improvement-history.log"

#===============================================================================
# COMMANDS
#===============================================================================

show_help() {
  cat << EOF
Usage: self-improve.sh <command> [options]

Self-improvement system for the orchestrator template.

COMMANDS:
  scan              Scan activity log for potential learnings
  add <type> <msg>  Add a learning manually
  apply             Apply high-confidence learnings to templates
  history           Show improvement history
  stats             Show learning statistics

TYPES:
  correction  - Mistake to never repeat
  preference  - User's preferred approach
  pattern     - Reusable workflow discovered
  antipattern - Thing that caused problems

EXAMPLES:
  ./self-improve.sh scan
  ./self-improve.sh add correction "Use pnpm not npm for this project"
  ./self-improve.sh add pattern "Always run lint before commit"
  ./self-improve.sh apply

EOF
}

#===============================================================================
# FUNCTIONS
#===============================================================================

add_learning() {
  local type=$1
  local message=$2
  local date=$(date +%Y-%m-%d)
  local section=""
  
  case $type in
    correction) section="Corrections" ;;
    preference) section="Preferences" ;;
    pattern) section="Patterns" ;;
    antipattern) section="Anti-Patterns" ;;
    *) echo "Unknown type: $type"; exit 1 ;;
  esac
  
  # Find the section and append
  if grep -q "## $section" "$LEARNINGS_FILE"; then
    # Add after the section header and comment
    sed -i "/## $section/,/^## /{/^<!-- /a\\
- [$date] ${type^^}: $message
}" "$LEARNINGS_FILE" 2>/dev/null || {
      # macOS sed syntax
      sed -i '' "/## $section/,/^## /{/^<!-- /a\\
- [$date] ${type^^}: $message
}" "$LEARNINGS_FILE"
    }
  fi
  
  # Update last modified
  sed -i "s/\*Last updated:.*/\*Last updated: $date\*/" "$LEARNINGS_FILE" 2>/dev/null || \
  sed -i '' "s/\*Last updated:.*/\*Last updated: $date\*/" "$LEARNINGS_FILE"
  
  # Log the improvement
  echo "$(date -Iseconds) | ADD | $type | $message" >> "$IMPROVEMENT_LOG"
  
  echo "✅ Added $type: $message"
}

scan_for_learnings() {
  echo "Scanning activity log for potential learnings..."
  echo ""
  
  if [ ! -f "$ACTIVITY_LOG" ]; then
    echo "No activity log found."
    return
  fi
  
  echo "=== Potential Corrections (errors/retries) ==="
  grep -i "error\|failed\|retry\|wrong\|incorrect" "$ACTIVITY_LOG" 2>/dev/null | tail -10 || echo "None found"
  echo ""
  
  echo "=== Repeated Patterns (similar actions) ==="
  # Find repeated command patterns
  grep -oE "\[INFO\].*" "$ACTIVITY_LOG" 2>/dev/null | sort | uniq -c | sort -rn | head -5 || echo "None found"
  echo ""
  
  echo "=== Session Completions ==="
  grep -c "DONE\|complete\|finished" "$ACTIVITY_LOG" 2>/dev/null || echo "0"
  echo " sessions completed"
  echo ""
  
  echo "Review the above and use 'self-improve.sh add <type> <message>' to capture learnings."
}

show_history() {
  echo "Improvement History"
  echo "==================="
  
  if [ -f "$IMPROVEMENT_LOG" ]; then
    tail -20 "$IMPROVEMENT_LOG"
  else
    echo "No improvements recorded yet."
  fi
}

show_stats() {
  echo "Learning Statistics"
  echo "==================="
  
  if [ -f "$LEARNINGS_FILE" ]; then
    local corrections=$(grep -c "CORRECTION:" "$LEARNINGS_FILE" 2>/dev/null || echo 0)
    local preferences=$(grep -c "PREFER:" "$LEARNINGS_FILE" 2>/dev/null || echo 0)
    local patterns=$(grep -c "PATTERN:" "$LEARNINGS_FILE" 2>/dev/null || echo 0)
    local antipatterns=$(grep -c "AVOID:" "$LEARNINGS_FILE" 2>/dev/null || echo 0)
    local total=$((corrections + preferences + patterns + antipatterns))
    
    echo "Corrections:   $corrections"
    echo "Preferences:   $preferences"
    echo "Patterns:      $patterns"
    echo "Anti-patterns: $antipatterns"
    echo "─────────────────"
    echo "Total:         $total"
  else
    echo "No learnings file found."
  fi
}

apply_learnings() {
  echo "Applying learnings to templates..."
  echo ""
  echo "This will analyze LEARNINGS.md and suggest updates to:"
  echo "  - CLAUDE.md (project rules)"
  echo "  - .kiro/steering/*.md (steering files)"
  echo ""
  echo "Run with an AI agent to get intelligent suggestions:"
  echo "  kiro-cli --agent orchestrator 'Review LEARNINGS.md and suggest template updates'"
}

#===============================================================================
# MAIN
#===============================================================================

mkdir -p "$(dirname "$IMPROVEMENT_LOG")"

case "${1:-help}" in
  scan)
    scan_for_learnings
    ;;
  add)
    [ -z "$2" ] || [ -z "$3" ] && { echo "Usage: self-improve.sh add <type> <message>"; exit 1; }
    add_learning "$2" "$3"
    ;;
  apply)
    apply_learnings
    ;;
  history)
    show_history
    ;;
  stats)
    show_stats
    ;;
  help|--help|-h|*)
    show_help
    ;;
esac
