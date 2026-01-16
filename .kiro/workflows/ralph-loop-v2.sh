#!/bin/bash
# .kiro/workflows/ralph-loop-v2.sh
#
# Improved Ralph loop with:
# - State management
# - Validation gates
# - Worktree awareness
# - Max iterations
# - Proper stop hook integration

set -e

# ============================================================================
# Configuration
# ============================================================================
STATE_DIR=".kiro/state"
STATE_FILE="$STATE_DIR/ralph-state.json"
LAST_OUTPUT="/tmp/kiro-ralph-last-output.txt"

# Default values
MAX_ITERATIONS=20
COMPLETION_PHRASE="<promise>DONE</promise>"

# ============================================================================
# Argument parsing
# ============================================================================
usage() {
  echo "Usage: $0 --task <task_description> [options]"
  echo ""
  echo "Options:"
  echo "  --task          Task description or path to plan file (required)"
  echo "  --max-iterations Maximum loop iterations (default: 20)"
  echo "  --worktrees     Enable worktree isolation"
  echo "  --agent         Agent to use (default: orchestrator)"
  echo "  --dry-run       Show what would be done without executing"
  echo ""
  echo "Examples:"
  echo "  $0 --task 'implement user authentication'"
  echo "  $0 --task .kiro/specs/plans/user-auth.plan.md --max-iterations 30"
  exit 1
}

TASK=""
USE_WORKTREES=false
AGENT="orchestrator"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --task)
      TASK="$2"
      shift 2
      ;;
    --max-iterations)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --worktrees)
      USE_WORKTREES=true
      shift
      ;;
    --agent)
      AGENT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

if [ -z "$TASK" ]; then
  echo "Error: --task is required"
  usage
fi

# ============================================================================
# Worktree context detection
# ============================================================================
get_worktree_context() {
  local main_repo
  main_repo=$(git worktree list --porcelain 2>/dev/null | head -1 | sed 's/worktree //')
  local current_dir
  current_dir=$(pwd)
  
  if [ "$main_repo" != "$current_dir" ] && [ -n "$main_repo" ]; then
    echo "## WORKTREE CONTEXT"
    echo "You are operating in a Git worktree, not the main repository."
    echo ""
    echo "- Main repository: $main_repo"
    echo "- Current worktree: $current_dir"
    echo "- Current branch: $(git branch --show-current)"
    echo ""
    echo "CRITICAL:"
    echo "- All file paths are relative to THIS worktree directory"
    echo "- package.json, Cargo.toml, etc. are in THIS directory"
    echo "- Do NOT try to access files in the main repository"
    echo ""
  fi
}

# ============================================================================
# State management
# ============================================================================
init_state() {
  mkdir -p "$STATE_DIR"
  
  # Read task content if it's a file
  local task_content="$TASK"
  if [ -f "$TASK" ]; then
    task_content=$(cat "$TASK")
  fi
  
  cat > "$STATE_FILE" << EOF
{
  "task": $(echo "$task_content" | jq -Rs .),
  "task_source": "$TASK",
  "iteration": 1,
  "max_iterations": $MAX_ITERATIONS,
  "completion_phrase": "$COMPLETION_PHRASE",
  "active": true,
  "started_at": "$(date -Iseconds)",
  "validation_passed": {
    "syntax": false,
    "unit_tests": false,
    "integration": false
  },
  "worktree": {
    "enabled": $USE_WORKTREES,
    "path": "$(pwd)",
    "branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')"
  },
  "agent": "$AGENT"
}
EOF

  echo "[ralph-loop] State initialized at $STATE_FILE"
}

# ============================================================================
# Build the prompt
# ============================================================================
build_prompt() {
  local worktree_context
  worktree_context=$(get_worktree_context)
  
  local task_content="$TASK"
  if [ -f "$TASK" ]; then
    task_content="Read and execute the plan at: $TASK"
  fi

  cat << EOF
$worktree_context

## RALPH LOOP EXECUTION

You are in iteration 1 of a maximum $MAX_ITERATIONS iterations.

### Your Task
$task_content

### Rules
1. Work on the task until complete
2. After each significant change, run validation:
   - Lint/typecheck (required)
   - Unit tests (required)
   - Integration tests (if applicable)
3. Update PROGRESS.md after each subtask
4. Only output "$COMPLETION_PHRASE" when:
   - ALL tasks are complete
   - ALL validations pass
   - You have verified the implementation works

### Validation Commands
Run these after each change:
\`\`\`bash
# Level 1: Syntax (required)
npm run lint && npm run typecheck

# Level 2: Unit tests (required)  
npm run test:unit

# Level 3: Integration (final check)
npm run test:integration
\`\`\`

### Output Format
When truly complete, end your response with:
$COMPLETION_PHRASE

If not complete, explain what remains and continue working.

BEGIN EXECUTION:
EOF
}

# ============================================================================
# Main execution
# ============================================================================
main() {
  echo "╔════════════════════════════════════════════════════════════════╗"
  echo "║              RALPH LOOP v2 - Starting Execution                ║"
  echo "╚════════════════════════════════════════════════════════════════╝"
  echo ""
  echo "Task: $TASK"
  echo "Max iterations: $MAX_ITERATIONS"
  echo "Agent: $AGENT"
  echo "Worktrees: $USE_WORKTREES"
  echo ""
  
  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would initialize state and start loop"
    echo ""
    echo "Generated prompt:"
    echo "─────────────────────────────────────────────────────────────────"
    build_prompt
    echo "─────────────────────────────────────────────────────────────────"
    exit 0
  fi
  
  # Initialize state
  init_state
  
  # Build prompt
  local prompt
  prompt=$(build_prompt)
  
  # Save prompt for reference
  echo "$prompt" > "$STATE_DIR/ralph-prompt.md"
  
  # Start the agent
  echo "[ralph-loop] Starting agent: $AGENT"
  echo "[ralph-loop] Stop hook will manage loop continuation"
  echo ""
  
  # Pipe prompt to kiro-cli
  # The stop hook (.kiro/hooks/ralph-stop.sh) handles loop continuation
  echo "$prompt" | kiro-cli --agent "$AGENT" 2>&1 | tee "$LAST_OUTPUT"
  
  # Check final state
  if [ -f "$STATE_FILE" ]; then
    local exit_reason
    exit_reason=$(jq -r '.exit_reason // "unknown"' "$STATE_FILE")
    local final_iteration
    final_iteration=$(jq -r '.iteration' "$STATE_FILE")
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    RALPH LOOP COMPLETE                         ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo "Exit reason: $exit_reason"
    echo "Total iterations: $final_iteration"
  fi
}

main
