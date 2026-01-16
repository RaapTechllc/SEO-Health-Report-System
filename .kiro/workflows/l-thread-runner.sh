#!/bin/bash
# l-thread-runner.sh - L-Thread implementation for extended autonomous execution
# Enables hours/days-long agent runs with self-validation and stop hooks

set -e

#===============================================================================
# CONFIGURATION
#===============================================================================

AGENT_TYPE=${AGENT_TYPE:-"orchestrator"}
TASK_PROMPT=${TASK_PROMPT:-""}
TASK_FILE=${TASK_FILE:-""}
MAX_HOURS=${MAX_HOURS:-8}
MAX_ITERATIONS=${MAX_ITERATIONS:-500}
CHECKPOINT_INTERVAL_MINUTES=${CHECKPOINT_INTERVAL_MINUTES:-30}
VALIDATION_COMMAND=${VALIDATION_COMMAND:-""}
STOP_ON_VALIDATION_FAIL=${STOP_ON_VALIDATION_FAIL:-false}
AUTO_RETRY_ON_ERROR=${AUTO_RETRY_ON_ERROR:-true}
MAX_RETRIES=${MAX_RETRIES:-3}
OUTPUT_DIR="agents/l-thread"
ACTIVITY_LOG="activity.log"
METRICS_FILE=".kiro/metrics.csv"
ENABLE_METRICS=${ENABLE_METRICS:-true}
NOTIFY_ON_COMPLETE=${NOTIFY_ON_COMPLETE:-true}

#===============================================================================
# PARSE COMMAND LINE ARGUMENTS
#===============================================================================

show_help() {
  cat << EOF
Usage: l-thread-runner.sh [OPTIONS]

L-Thread runner - extended autonomous agent execution with self-validation.

OPTIONS:
  -a, --agent=TYPE          Agent type to run (default: orchestrator)
  -p, --prompt=PROMPT       Task prompt for the agent
  -f, --task-file=FILE      File containing task description
  -t, --max-hours=N         Maximum runtime in hours (default: 8)
  -i, --max-iterations=N    Maximum iterations (default: 500)
  -c, --checkpoint=MIN      Checkpoint interval in minutes (default: 30)
  -v, --validation=CMD      Validation command to run at checkpoints
  --stop-on-fail            Stop if validation fails (default: continue)
  --no-retry                Disable auto-retry on errors
  --max-retries=N           Maximum retry attempts (default: 3)
  --no-metrics              Disable metrics tracking
  --no-notify               Disable completion notification
  -h, --help                Show this help message

VALIDATION COMMANDS:
  The validation command runs at each checkpoint. Examples:
  - "npm test"              Run test suite
  - "npm run lint"          Run linter
  - "npm run build"         Run build
  - "./validate.sh"         Custom validation script

EXAMPLES:
  # Long-running code improvement
  ./l-thread-runner.sh --agent=code-surgeon --prompt="Refactor the auth module" --max-hours=4

  # Overnight documentation
  ./l-thread-runner.sh --agent=doc-smith --task-file=doc-tasks.md --max-hours=12

  # With validation
  ./l-thread-runner.sh --agent=test-architect \\
    --prompt="Improve test coverage" \\
    --validation="npm test" \\
    --stop-on-fail

THREAD TYPE:
  This script implements L-Threads (Long-running Threads) from the
  Thread-Based Engineering framework. Use it for extended autonomous
  work with minimal human intervention.

EOF
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -a|--agent)
      AGENT_TYPE="$2"
      shift 2
      ;;
    --agent=*)
      AGENT_TYPE="${1#*=}"
      shift
      ;;
    -p|--prompt)
      TASK_PROMPT="$2"
      shift 2
      ;;
    --prompt=*)
      TASK_PROMPT="${1#*=}"
      shift
      ;;
    -f|--task-file)
      TASK_FILE="$2"
      shift 2
      ;;
    --task-file=*)
      TASK_FILE="${1#*=}"
      shift
      ;;
    -t|--max-hours)
      MAX_HOURS="$2"
      shift 2
      ;;
    --max-hours=*)
      MAX_HOURS="${1#*=}"
      shift
      ;;
    -i|--max-iterations)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --max-iterations=*)
      MAX_ITERATIONS="${1#*=}"
      shift
      ;;
    -c|--checkpoint)
      CHECKPOINT_INTERVAL_MINUTES="$2"
      shift 2
      ;;
    --checkpoint=*)
      CHECKPOINT_INTERVAL_MINUTES="${1#*=}"
      shift
      ;;
    -v|--validation)
      VALIDATION_COMMAND="$2"
      shift 2
      ;;
    --validation=*)
      VALIDATION_COMMAND="${1#*=}"
      shift
      ;;
    --stop-on-fail)
      STOP_ON_VALIDATION_FAIL=true
      shift
      ;;
    --no-retry)
      AUTO_RETRY_ON_ERROR=false
      shift
      ;;
    --max-retries=*)
      MAX_RETRIES="${1#*=}"
      shift
      ;;
    --no-metrics)
      ENABLE_METRICS=false
      shift
      ;;
    --no-notify)
      NOTIFY_ON_COMPLETE=false
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

#===============================================================================
# VALIDATION
#===============================================================================

if [ -z "$TASK_PROMPT" ] && [ -z "$TASK_FILE" ]; then
  echo "Error: Either --prompt or --task-file is required"
  show_help
  exit 1
fi

if [ -n "$TASK_FILE" ] && [ ! -f "$TASK_FILE" ]; then
  echo "Error: Task file not found: $TASK_FILE"
  exit 1
fi

# Load task from file if specified
if [ -n "$TASK_FILE" ]; then
  TASK_PROMPT=$(cat "$TASK_FILE")
fi

#===============================================================================
# UTILITY FUNCTIONS
#===============================================================================

SESSION_ID=$(date +%s)
OUTPUT_DIR="agents/l-thread-$SESSION_ID"
STATE_FILE="$OUTPUT_DIR/.state"
CHECKPOINT_FILE="$OUTPUT_DIR/.checkpoint"

log() {
  local level=$1
  local message=$2
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] [$level] $message"
  echo "$timestamp: [L-Thread] $message" >> "$ACTIVITY_LOG"
}

log_metric() {
  if [ "$ENABLE_METRICS" = true ]; then
    local metric=$1
    local value=$2
    echo "$(date -Iseconds),$metric,$value,l-thread,$SESSION_ID" >> "$METRICS_FILE"
  fi
}

notify_user() {
  local title=$1
  local message=$2
  
  if [ "$NOTIFY_ON_COMPLETE" != true ]; then
    return
  fi
  
  # Try different notification methods
  if command -v notify-send &> /dev/null; then
    notify-send "$title" "$message"
  elif command -v osascript &> /dev/null; then
    osascript -e "display notification \"$message\" with title \"$title\""
  elif command -v powershell.exe &> /dev/null; then
    powershell.exe -Command "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('$message', '$title')" &> /dev/null &
  else
    echo -e "\a"  # Terminal bell
  fi
}

save_state() {
  local iteration=$1
  local status=$2
  local checkpoint=$3
  
  cat > "$STATE_FILE" << EOF
{
  "session_id": "$SESSION_ID",
  "agent": "$AGENT_TYPE",
  "iteration": $iteration,
  "status": "$status",
  "last_checkpoint": "$checkpoint",
  "start_time": "$START_TIME",
  "timestamp": "$(date -Iseconds)"
}
EOF
}

run_validation() {
  if [ -z "$VALIDATION_COMMAND" ]; then
    return 0
  fi
  
  log "INFO" "Running validation: $VALIDATION_COMMAND"
  
  local validation_output="$OUTPUT_DIR/validation-$(date +%s).log"
  
  if eval "$VALIDATION_COMMAND" > "$validation_output" 2>&1; then
    log "INFO" "Validation passed"
    log_metric "validation_pass" "1"
    return 0
  else
    log "WARN" "Validation failed"
    log_metric "validation_fail" "1"
    cat "$validation_output"
    return 1
  fi
}

check_completion() {
  local output_file=$1
  
  if [ -f "$output_file" ]; then
    # Check for completion signals
    if grep -q "<promise>DONE</promise>" "$output_file" 2>/dev/null; then
      return 0
    fi
    if grep -q "<promise>COMPLETE</promise>" "$output_file" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

#===============================================================================
# STOP HOOK
#===============================================================================

# Stop hook - runs when agent tries to complete
stop_hook() {
  local iteration=$1
  local output_file=$2
  
  log "INFO" "Stop hook triggered at iteration $iteration"
  
  # Run validation if configured
  if ! run_validation; then
    if [ "$STOP_ON_VALIDATION_FAIL" = true ]; then
      log "ERROR" "Validation failed - stopping"
      return 1
    else
      log "WARN" "Validation failed - continuing anyway"
    fi
  fi
  
  # Check if work is actually complete
  if check_completion "$output_file"; then
    log "INFO" "Work complete - allowing stop"
    return 0
  fi
  
  # Check remaining time
  local elapsed=$(($(date +%s) - START_TIME))
  local max_seconds=$((MAX_HOURS * 3600))
  local remaining=$((max_seconds - elapsed))
  
  if [ $remaining -le 0 ]; then
    log "WARN" "Max time reached - allowing stop"
    return 0
  fi
  
  # Check remaining iterations
  if [ $iteration -ge $MAX_ITERATIONS ]; then
    log "WARN" "Max iterations reached - allowing stop"
    return 0
  fi
  
  log "INFO" "Work incomplete - continuing (${remaining}s remaining)"
  return 2  # Signal to continue
}

#===============================================================================
# MAIN EXECUTION LOOP
#===============================================================================

run_agent_iteration() {
  local iteration=$1
  local output_file="$OUTPUT_DIR/iteration-$iteration.md"
  
  log "INFO" "Starting iteration $iteration"
  log_metric "iteration_start" "$iteration"
  
  # Create iteration prompt
  local iteration_prompt="$TASK_PROMPT

## Iteration Context
- This is iteration $iteration of a long-running task
- Max iterations: $MAX_ITERATIONS
- Continue working until the task is complete
- Signal completion with <promise>DONE</promise>

## Previous Progress
$(cat "$OUTPUT_DIR/progress.md" 2>/dev/null || echo "No previous progress")
"

  # Run agent (REPLACE WITH ACTUAL KIRO-CLI)
  # timeout ${TIMEOUT_PER_ITERATION}s kiro-cli --agent "$AGENT_TYPE" --prompt "$iteration_prompt" > "$output_file" 2>&1
  
  # Simulated execution (remove in production)
  echo "# Iteration $iteration Output" > "$output_file"
  echo "" >> "$output_file"
  echo "## Work Performed" >> "$output_file"
  echo "- Analyzed task requirements" >> "$output_file"
  echo "- Made progress on implementation" >> "$output_file"
  echo "- Updated documentation" >> "$output_file"
  echo "" >> "$output_file"
  
  sleep $((RANDOM % 5 + 2))
  
  # Simulate completion (10% chance per iteration)
  if [ $((RANDOM % 10)) -eq 0 ]; then
    echo "<promise>DONE</promise>" >> "$output_file"
  fi
  
  # Update progress file
  cat >> "$OUTPUT_DIR/progress.md" << EOF

## Iteration $iteration ($(date -Iseconds))
$(grep -A 100 "## Work Performed" "$output_file" 2>/dev/null | head -20)

EOF
  
  log_metric "iteration_complete" "$iteration"
  return 0
}

main() {
  START_TIME=$(date +%s)
  local max_seconds=$((MAX_HOURS * 3600))
  local checkpoint_seconds=$((CHECKPOINT_INTERVAL_MINUTES * 60))
  local last_checkpoint=$START_TIME
  local iteration=0
  local retry_count=0
  local completed=false
  
  echo "=========================================="
  echo "L-Thread Long-Running Agent"
  echo "=========================================="
  echo "Agent: $AGENT_TYPE"
  echo "Max runtime: ${MAX_HOURS}h"
  echo "Max iterations: $MAX_ITERATIONS"
  echo "Checkpoint interval: ${CHECKPOINT_INTERVAL_MINUTES}m"
  echo "Validation: ${VALIDATION_COMMAND:-none}"
  echo "=========================================="
  echo ""
  echo "Task:"
  echo "${TASK_PROMPT:0:200}..."
  echo ""
  echo "=========================================="
  
  # Initialize
  mkdir -p "$OUTPUT_DIR"
  mkdir -p "$(dirname "$METRICS_FILE")"
  
  if [ "$ENABLE_METRICS" = true ] && [ ! -f "$METRICS_FILE" ]; then
    echo "timestamp,metric,value,thread_type,session_id" > "$METRICS_FILE"
  fi
  
  # Initialize progress file
  cat > "$OUTPUT_DIR/progress.md" << EOF
# L-Thread Progress Log

## Task
$TASK_PROMPT

## Session Info
- Session ID: $SESSION_ID
- Agent: $AGENT_TYPE
- Started: $(date -Iseconds)
- Max Runtime: ${MAX_HOURS}h
- Max Iterations: $MAX_ITERATIONS

## Progress
EOF
  
  log "INFO" "Starting L-Thread: $AGENT_TYPE (max: ${MAX_HOURS}h, ${MAX_ITERATIONS} iterations)"
  log_metric "session_start" "1"
  log_metric "max_hours" "$MAX_HOURS"
  log_metric "max_iterations" "$MAX_ITERATIONS"
  
  # Main execution loop
  while [ $iteration -lt $MAX_ITERATIONS ]; do
    # Check time limit
    local elapsed=$(($(date +%s) - START_TIME))
    if [ $elapsed -ge $max_seconds ]; then
      log "WARN" "Max runtime reached (${MAX_HOURS}h)"
      break
    fi
    
    ((iteration++))
    save_state $iteration "running" "$(date -Iseconds)"
    
    # Run iteration
    if run_agent_iteration $iteration; then
      retry_count=0
      
      # Check for completion
      if check_completion "$OUTPUT_DIR/iteration-$iteration.md"; then
        log "INFO" "Agent signaled completion"
        
        # Run stop hook
        local hook_result
        stop_hook $iteration "$OUTPUT_DIR/iteration-$iteration.md"
        hook_result=$?
        
        if [ $hook_result -eq 0 ]; then
          completed=true
          break
        elif [ $hook_result -eq 1 ]; then
          log "ERROR" "Stop hook failed - aborting"
          break
        fi
        # hook_result == 2 means continue
      fi
      
      # Checkpoint check
      local now=$(date +%s)
      if [ $((now - last_checkpoint)) -ge $checkpoint_seconds ]; then
        log "INFO" "Checkpoint at iteration $iteration"
        last_checkpoint=$now
        save_state $iteration "checkpoint" "$(date -Iseconds)"
        
        # Run validation at checkpoint
        if ! run_validation; then
          if [ "$STOP_ON_VALIDATION_FAIL" = true ]; then
            log "ERROR" "Checkpoint validation failed - stopping"
            break
          fi
        fi
        
        log_metric "checkpoint" "$iteration"
      fi
      
    else
      # Iteration failed
      if [ "$AUTO_RETRY_ON_ERROR" = true ] && [ $retry_count -lt $MAX_RETRIES ]; then
        ((retry_count++))
        log "WARN" "Iteration failed, retrying ($retry_count/$MAX_RETRIES)"
        ((iteration--))  # Retry same iteration
        sleep 5
      else
        log "ERROR" "Iteration failed after $MAX_RETRIES retries"
        break
      fi
    fi
    
    # Brief pause between iterations
    sleep 2
  done
  
  # Calculate final stats
  local end_time=$(date +%s)
  local duration=$((end_time - START_TIME))
  local duration_hours=$(echo "scale=2; $duration / 3600" | bc)
  
  # Save final state
  if $completed; then
    save_state $iteration "complete" "$(date -Iseconds)"
  else
    save_state $iteration "stopped" "$(date -Iseconds)"
  fi
  
  # Generate summary
  cat > "$OUTPUT_DIR/summary.md" << EOF
# L-Thread Execution Summary

## Result
Status: $(if $completed; then echo "COMPLETED"; else echo "STOPPED"; fi)

## Statistics
- Total iterations: $iteration
- Runtime: ${duration_hours}h ($duration seconds)
- Checkpoints: $(grep -c "checkpoint" "$METRICS_FILE" 2>/dev/null || echo 0)
- Validation passes: $(grep -c "validation_pass" "$METRICS_FILE" 2>/dev/null || echo 0)
- Validation fails: $(grep -c "validation_fail" "$METRICS_FILE" 2>/dev/null || echo 0)

## Task
$TASK_PROMPT

## Output Files
$(ls -1 "$OUTPUT_DIR"/*.md 2>/dev/null)
EOF
  
  # Final report
  echo ""
  echo "=========================================="
  echo "L-Thread Execution Complete!"
  echo "=========================================="
  echo "Status: $(if $completed; then echo "COMPLETED"; else echo "STOPPED"; fi)"
  echo "Iterations: $iteration"
  echo "Runtime: ${duration_hours}h"
  echo "Output: $OUTPUT_DIR/"
  echo ""
  
  # Log final metrics
  log_metric "session_end" "1"
  log_metric "duration_seconds" "$duration"
  log_metric "total_iterations" "$iteration"
  log_metric "completed" "$(if $completed; then echo 1; else echo 0; fi)"
  
  # Notify user
  notify_user "L-Thread Complete" "Agent $AGENT_TYPE finished after $iteration iterations (${duration_hours}h)"
  
  log "INFO" "L-Thread complete: $iteration iterations in ${duration_hours}h"
  
  if $completed; then
    exit 0
  else
    exit 1
  fi
}

# Run main
main "$@"
