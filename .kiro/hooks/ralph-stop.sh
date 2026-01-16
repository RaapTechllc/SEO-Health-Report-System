#!/bin/bash
# .kiro/hooks/ralph-stop.sh
# 
# Stop hook for the Ralph loop. This runs every time Claude tries to exit.
# It prevents premature exit by checking:
# 1. Is the loop active?
# 2. Have all validation gates passed?
# 3. Has the completion phrase been output?
# 4. Have we hit max iterations?

set -e

STATE_FILE=".kiro/state/ralph-state.json"
LAST_OUTPUT="/tmp/kiro-ralph-last-output.txt"

# Helper: Read JSON value
read_state() {
  jq -r "$1" "$STATE_FILE" 2>/dev/null || echo "null"
}

# Helper: Update JSON value
update_state() {
  local key="$1"
  local value="$2"
  jq "$key = $value" "$STATE_FILE" > /tmp/ralph-state-tmp.json && \
    mv /tmp/ralph-state-tmp.json "$STATE_FILE"
}

# Check if state file exists
if [ ! -f "$STATE_FILE" ]; then
  # No active loop, allow exit
  exit 0
fi

# Read current state
ACTIVE=$(read_state '.active')
ITERATION=$(read_state '.iteration')
MAX_ITERATIONS=$(read_state '.max_iterations')
TASK=$(read_state '.task')
VALIDATION_SYNTAX=$(read_state '.validation_passed.syntax')
VALIDATION_UNIT=$(read_state '.validation_passed.unit_tests')
VALIDATION_INTEGRATION=$(read_state '.validation_passed.integration')

# Debug output (goes to claude's stderr)
echo "[ralph-stop] Iteration: $ITERATION/$MAX_ITERATIONS" >&2
echo "[ralph-stop] Active: $ACTIVE" >&2

# Exit early if loop not active
if [ "$ACTIVE" != "true" ]; then
  echo "[ralph-stop] Loop not active, allowing exit" >&2
  exit 0
fi

# Check max iterations
if [ "$ITERATION" -ge "$MAX_ITERATIONS" ]; then
  echo "[ralph-stop] Max iterations reached ($MAX_ITERATIONS). Force exit." >&2
  update_state '.active' 'false'
  update_state '.exit_reason' '"max_iterations"'
  exit 0
fi

# Run validation commands and update state
run_validations() {
  echo "[ralph-stop] Running validation gates..." >&2
  
  # Level 1: Syntax (required)
  if command -v npm &> /dev/null && [ -f "package.json" ]; then
    if npm run lint --silent 2>/dev/null && npm run typecheck --silent 2>/dev/null; then
      update_state '.validation_passed.syntax' 'true'
      echo "[ralph-stop] ✓ Syntax passed" >&2
    else
      update_state '.validation_passed.syntax' 'false'
      echo "[ralph-stop] ✗ Syntax failed" >&2
      return 1
    fi
  else
    # No JS project, skip
    update_state '.validation_passed.syntax' 'true'
  fi
  
  # Level 2: Unit tests (required)
  if command -v npm &> /dev/null && [ -f "package.json" ]; then
    if npm run test:unit --silent 2>/dev/null; then
      update_state '.validation_passed.unit_tests' 'true'
      echo "[ralph-stop] ✓ Unit tests passed" >&2
    else
      update_state '.validation_passed.unit_tests' 'false'
      echo "[ralph-stop] ✗ Unit tests failed" >&2
      return 1
    fi
  else
    update_state '.validation_passed.unit_tests' 'true'
  fi
  
  return 0
}

# Check for completion phrase in last output
check_completion() {
  if [ -f "$LAST_OUTPUT" ]; then
    if grep -q "<promise>DONE</promise>" "$LAST_OUTPUT"; then
      return 0
    fi
  fi
  return 1
}

# Main logic
if check_completion; then
  echo "[ralph-stop] Completion phrase found, running final validation..." >&2
  
  if run_validations; then
    echo "[ralph-stop] All validations passed. Allowing exit." >&2
    update_state '.active' 'false'
    update_state '.exit_reason' '"completed"'
    update_state '.completed_at' "\"$(date -Iseconds)\""
    exit 0
  else
    echo "[ralph-stop] Validation failed. Agent said DONE but work incomplete." >&2
    # Continue loop - agent needs to fix validation failures
  fi
fi

# Continue the loop
NEXT_ITERATION=$((ITERATION + 1))
update_state '.iteration' "$NEXT_ITERATION"
echo "[ralph-stop] Continuing loop (iteration $NEXT_ITERATION)..." >&2

# Return non-zero to prevent exit and trigger continuation
exit 1
