#!/bin/bash
# ralph-kiro.sh - Enhanced P-Thread parallel agent spawner with circuit breaker
# Implements Ralph Loop pattern with intelligent exit detection and worktree isolation

set -e

#===============================================================================
# CONFIGURATION
#===============================================================================

PARALLEL_COUNT=${PARALLEL_COUNT:-5}
MAX_PARALLEL=${MAX_PARALLEL:-15}
TIMEOUT_HOURS=${TIMEOUT_HOURS:-4}
STALL_THRESHOLD_MINUTES=${STALL_THRESHOLD_MINUTES:-15}
MAX_ITERATIONS=${MAX_ITERATIONS:-50}
ENABLE_METRICS=${ENABLE_METRICS:-true}
RESOURCE_CHECK_INTERVAL=${RESOURCE_CHECK_INTERVAL:-60}

# Worktree isolation settings
USE_WORKTREES=${USE_WORKTREES:-false}
WORKTREE_BASE=${WORKTREE_BASE:-"../.worktrees"}
AUTO_MERGE=${AUTO_MERGE:-false}
VALIDATE_BEFORE_MERGE=${VALIDATE_BEFORE_MERGE:-true}

# Circuit breaker settings
CIRCUIT_BREAKER_THRESHOLD=${CIRCUIT_BREAKER_THRESHOLD:-3}
CIRCUIT_BREAKER_COOLDOWN=${CIRCUIT_BREAKER_COOLDOWN:-300}
CIRCUIT_BREAKER_FILE=".kiro/.circuit_breaker"

# Auto-recovery settings
RESTART_POLICY=${RESTART_POLICY:-"once"}  # never | once | always
MAX_RESTARTS=${MAX_RESTARTS:-3}
RESTART_DELAY=${RESTART_DELAY:-30}

# Completion detection settings
COMPLETION_INDICATOR_THRESHOLD=${COMPLETION_INDICATOR_THRESHOLD:-2}

DEFAULT_AGENTS=(
  "security-specialist"
  "test-architect"
  "doc-smith"
  "code-surgeon"
)

AGENTS_DIR="agents"
METRICS_FILE=".kiro/metrics.csv"
ACTIVITY_LOG="activity.log"

#===============================================================================
# CIRCUIT BREAKER
#===============================================================================

init_circuit_breaker() {
  if [ ! -f "$CIRCUIT_BREAKER_FILE" ]; then
    echo '{"failures":0,"last_failure":0,"state":"closed"}' > "$CIRCUIT_BREAKER_FILE"
  fi
}

check_circuit_breaker() {
  if [ ! -f "$CIRCUIT_BREAKER_FILE" ]; then
    return 0  # OK to proceed
  fi
  
  local state=$(grep -o '"state":"[^"]*"' "$CIRCUIT_BREAKER_FILE" | cut -d'"' -f4)
  local last_failure=$(grep -o '"last_failure":[0-9]*' "$CIRCUIT_BREAKER_FILE" | cut -d':' -f2)
  local now=$(date +%s)
  
  if [ "$state" = "open" ]; then
    local elapsed=$((now - last_failure))
    if [ $elapsed -gt $CIRCUIT_BREAKER_COOLDOWN ]; then
      log "INFO" "Circuit breaker cooldown complete, resetting to half-open"
      echo '{"failures":0,"last_failure":0,"state":"half-open"}' > "$CIRCUIT_BREAKER_FILE"
      return 0
    else
      local remaining=$((CIRCUIT_BREAKER_COOLDOWN - elapsed))
      log "WARN" "Circuit breaker OPEN - waiting ${remaining}s before retry"
      return 1
    fi
  fi
  
  return 0
}

record_failure() {
  local failures=$(grep -o '"failures":[0-9]*' "$CIRCUIT_BREAKER_FILE" | cut -d':' -f2)
  ((failures++))
  local now=$(date +%s)
  
  if [ $failures -ge $CIRCUIT_BREAKER_THRESHOLD ]; then
    log "WARN" "Circuit breaker TRIPPED after $failures consecutive failures"
    echo "{\"failures\":$failures,\"last_failure\":$now,\"state\":\"open\"}" > "$CIRCUIT_BREAKER_FILE"
  else
    echo "{\"failures\":$failures,\"last_failure\":$now,\"state\":\"closed\"}" > "$CIRCUIT_BREAKER_FILE"
  fi
}

record_success() {
  echo '{"failures":0,"last_failure":0,"state":"closed"}' > "$CIRCUIT_BREAKER_FILE"
}

reset_circuit_breaker() {
  echo '{"failures":0,"last_failure":0,"state":"closed"}' > "$CIRCUIT_BREAKER_FILE"
  log "INFO" "Circuit breaker reset"
}

#===============================================================================
# COMPLETION DETECTION (Ralph Pattern)
#===============================================================================

count_completion_indicators() {
  local output_file=$1
  local count=0
  
  if [ ! -f "$output_file" ]; then
    echo 0
    return
  fi
  
  # Check for various completion signals
  grep -c "task.*complete\|finished\|done\|all.*pass\|success" "$output_file" 2>/dev/null || true
}

check_exit_signal() {
  local output_file=$1
  
  if [ ! -f "$output_file" ]; then
    return 1
  fi
  
  # Check for explicit completion signal
  if grep -q "<promise>DONE</promise>" "$output_file" 2>/dev/null; then
    return 0
  fi
  
  if grep -q "<promise>COMPLETE</promise>" "$output_file" 2>/dev/null; then
    return 0
  fi
  
  # Check for EXIT_SIGNAL in RALPH_STATUS block
  if grep -q "EXIT_SIGNAL.*true" "$output_file" 2>/dev/null; then
    return 0
  fi
  
  return 1
}

should_exit() {
  local agent=$1
  local output_file="$AGENTS_DIR/$agent/output.log"
  
  # Dual-condition check (Ralph pattern)
  local indicators=$(count_completion_indicators "$output_file")
  
  if [ "$indicators" -ge "$COMPLETION_INDICATOR_THRESHOLD" ]; then
    if check_exit_signal "$output_file"; then
      log "INFO" "$agent - Exit conditions met (indicators: $indicators, signal: true)"
      return 0
    else
      log "DEBUG" "$agent - Indicators met ($indicators) but no EXIT_SIGNAL, continuing"
    fi
  fi
  
  return 1
}

#===============================================================================
# PARSE COMMAND LINE ARGUMENTS
#===============================================================================

show_help() {
  cat << EOF
Usage: ralph-kiro.sh [OPTIONS]

P-Thread parallel agent spawner with circuit breaker protection and worktree isolation.

OPTIONS:
  -p, --parallel=N        Number of parallel agents (default: 5, max: 15)
  -t, --timeout=H         Timeout in hours (default: 4)
  -m, --max-iter=N        Maximum iterations per agent (default: 50)
  -a, --agents=LIST       Comma-separated agent list
  --no-metrics            Disable metrics tracking
  --stall-threshold=M     Minutes before restarting stalled agent (default: 15)
  --reset-circuit         Reset the circuit breaker
  --circuit-status        Show circuit breaker status

WORKTREE ISOLATION:
  --worktrees             Enable git worktree isolation (each agent gets own branch)
  --auto-merge            Auto-merge completed worktrees to main
  --no-validate           Skip validation before merge
  -h, --help              Show this help message

COMPLETION DETECTION:
  Agents exit when BOTH conditions are met:
  1. Completion indicators >= $COMPLETION_INDICATOR_THRESHOLD
  2. Explicit EXIT_SIGNAL (e.g., <promise>DONE</promise>)

CIRCUIT BREAKER:
  Opens after $CIRCUIT_BREAKER_THRESHOLD consecutive failures.
  Cooldown period: ${CIRCUIT_BREAKER_COOLDOWN}s

EXAMPLES:
  ./ralph-kiro.sh --parallel=10
  ./ralph-kiro.sh --agents=code-surgeon,test-architect
  ./ralph-kiro.sh --reset-circuit

EOF
}

CUSTOM_AGENTS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--parallel)
      PARALLEL_COUNT="$2"
      shift 2
      ;;
    --parallel=*)
      PARALLEL_COUNT="${1#*=}"
      shift
      ;;
    -t|--timeout)
      TIMEOUT_HOURS="$2"
      shift 2
      ;;
    --timeout=*)
      TIMEOUT_HOURS="${1#*=}"
      shift
      ;;
    -m|--max-iter)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --max-iter=*)
      MAX_ITERATIONS="${1#*=}"
      shift
      ;;
    -a|--agents)
      IFS=',' read -ra CUSTOM_AGENTS <<< "$2"
      shift 2
      ;;
    --agents=*)
      IFS=',' read -ra CUSTOM_AGENTS <<< "${1#*=}"
      shift
      ;;
    --no-metrics)
      ENABLE_METRICS=false
      shift
      ;;
    --stall-threshold=*)
      STALL_THRESHOLD_MINUTES="${1#*=}"
      shift
      ;;
    --worktrees)
      USE_WORKTREES=true
      shift
      ;;
    --auto-merge)
      AUTO_MERGE=true
      shift
      ;;
    --no-validate)
      VALIDATE_BEFORE_MERGE=false
      shift
      ;;
    --reset-circuit)
      init_circuit_breaker
      reset_circuit_breaker
      exit 0
      ;;
    --circuit-status)
      if [ -f "$CIRCUIT_BREAKER_FILE" ]; then
        cat "$CIRCUIT_BREAKER_FILE"
      else
        echo "Circuit breaker not initialized"
      fi
      exit 0
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

if [ ${#CUSTOM_AGENTS[@]} -gt 0 ]; then
  AGENTS=("${CUSTOM_AGENTS[@]}")
else
  AGENTS=("${DEFAULT_AGENTS[@]}")
fi

if [ "$PARALLEL_COUNT" -gt "$MAX_PARALLEL" ]; then
  echo "Warning: Parallel count capped at $MAX_PARALLEL"
  PARALLEL_COUNT=$MAX_PARALLEL
fi

#===============================================================================
# UTILITY FUNCTIONS
#===============================================================================

log() {
  local level=$1
  local message=$2
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] [$level] $message"
  echo "$timestamp: $message" >> "$ACTIVITY_LOG"
}

log_metric() {
  if [ "$ENABLE_METRICS" = true ]; then
    local metric=$1
    local value=$2
    echo "$(date -Iseconds),$metric,$value,p-thread,$SESSION_ID" >> "$METRICS_FILE"
  fi
}

check_resources() {
  local mem_available=4096
  if command -v free &> /dev/null; then
    mem_available=$(free -m | awk '/^Mem:/{print $7}')
  elif command -v vm_stat &> /dev/null; then
    mem_available=$(vm_stat | awk '/Pages free/ {print int($3*4096/1048576)}')
  fi
  
  if [ "$mem_available" -lt 1024 ]; then
    log "WARN" "Low memory: ${mem_available}MB available"
    return 1
  fi
  return 0
}

check_agent_stalled() {
  local agent=$1
  local output_file="$AGENTS_DIR/$agent/output.log"
  
  if [ -f "$output_file" ]; then
    local last_modified=$(stat -c %Y "$output_file" 2>/dev/null || stat -f %m "$output_file" 2>/dev/null)
    local now=$(date +%s)
    local diff=$(( (now - last_modified) / 60 ))
    
    if [ "$diff" -gt "$STALL_THRESHOLD_MINUTES" ]; then
      return 0
    fi
  fi
  return 1
}

#===============================================================================
# AGENT EXECUTION
#===============================================================================

# Worktree helper functions
setup_agent_worktree() {
  local agent=$1
  if [ "$USE_WORKTREES" = true ]; then
    log "INFO" "Creating worktree for $agent"
    ./.kiro/workflows/worktree-manager.sh create "$agent" 2>/dev/null || true
  fi
}

cleanup_agent_worktree() {
  local agent=$1
  if [ "$USE_WORKTREES" = true ] && [ "$AUTO_MERGE" = true ]; then
    log "INFO" "Merging and cleaning up worktree for $agent"
    if [ "$VALIDATE_BEFORE_MERGE" = true ]; then
      ./.kiro/workflows/worktree-manager.sh merge "$agent" 2>/dev/null || true
    else
      ./.kiro/workflows/worktree-manager.sh merge "$agent" --no-validate 2>/dev/null || true
    fi
    ./.kiro/workflows/worktree-manager.sh cleanup "$agent" 2>/dev/null || true
  fi
}

get_agent_workdir() {
  local agent=$1
  if [ "$USE_WORKTREES" = true ]; then
    local project_name=$(basename "$(pwd)")
    echo "../.worktrees/$project_name-$agent"
  else
    echo "."
  fi
}

run_agent_loop() {
  local agent=$1
  local iteration=0
  local start_time=$(date +%s)
  local timeout_seconds=$((TIMEOUT_HOURS * 3600))
  local workdir=$(get_agent_workdir "$agent")
  
  log "INFO" "Starting $agent (max: $MAX_ITERATIONS iterations)"
  
  # Setup worktree if enabled
  setup_agent_worktree "$agent"
  
  mkdir -p "$AGENTS_DIR/$agent"
  
  [ -f "PLAN.md" ] && cp PLAN.md "$AGENTS_DIR/$agent/"
  [ -f "PROGRESS.md" ] && cp PROGRESS.md "$AGENTS_DIR/$agent/"
  
  while [ $iteration -lt $MAX_ITERATIONS ]; do
    # Check circuit breaker
    if ! check_circuit_breaker; then
      log "WARN" "$agent - Circuit breaker open, pausing"
      sleep 60
      continue
    fi
    
    # Check timeout
    local elapsed=$(($(date +%s) - start_time))
    if [ $elapsed -gt $timeout_seconds ]; then
      log "WARN" "$agent - Timeout reached"
      break
    fi
    
    # Check completion (dual-condition)
    if should_exit "$agent"; then
      record_success
      cleanup_agent_worktree "$agent"
      break
    fi
    
    ((iteration++))
    log "INFO" "$agent - Iteration $iteration/$MAX_ITERATIONS (workdir: $workdir)"
    log_metric "iteration" "$iteration"
    
    # Run agent in appropriate directory
    echo "$(date): Running kiro-cli --agent $agent (iteration $iteration)" >> "$AGENTS_DIR/$agent/output.log"
    
    # REPLACE WITH ACTUAL EXECUTION:
    # cd "$workdir" && kiro-cli --agent "$agent" --prompt "Continue working on assigned tasks from PLAN.md" >> "$AGENTS_DIR/$agent/output.log" 2>&1
    # local exit_code=$?
    # cd - > /dev/null
    # if [ $exit_code -ne 0 ]; then
    #   record_failure
    # fi
    
    sleep 2
  done
  
  if [ $iteration -ge $MAX_ITERATIONS ]; then
    log "WARN" "$agent - Max iterations reached"
    record_failure
  fi
  
  log_metric "total_iterations" "$iteration"
}

#===============================================================================
# MAIN
#===============================================================================

main() {
  SESSION_ID=$(date +%s)
  local start_time=$(date +%s)
  
  init_circuit_breaker
  
  if ! check_circuit_breaker; then
    echo "❌ Circuit breaker is OPEN. Use --reset-circuit to reset."
    exit 1
  fi
  
  echo "=========================================="
  echo "🔄 P-Thread Ralph Loop"
  echo "=========================================="
  echo "Agents: ${AGENTS[*]}"
  echo "Parallel: $PARALLEL_COUNT | Timeout: ${TIMEOUT_HOURS}h"
  echo "Max iterations: $MAX_ITERATIONS"
  if [ "$USE_WORKTREES" = true ]; then
    echo "Worktree isolation: ENABLED"
    echo "Auto-merge: $AUTO_MERGE"
  fi
  echo "=========================================="
  
  if [ "$ENABLE_METRICS" = true ]; then
    mkdir -p "$(dirname "$METRICS_FILE")"
    [ ! -f "$METRICS_FILE" ] && echo "timestamp,metric,value,thread_type,session_id" > "$METRICS_FILE"
    log_metric "session_start" "1"
  fi
  
  echo "$(date): P-Thread started (session: $SESSION_ID)" > "$ACTIVITY_LOG"
  mkdir -p "$AGENTS_DIR"
  
  declare -a PIDS
  local launched=0
  
  for agent in "${AGENTS[@]}"; do
    while [ $launched -ge $PARALLEL_COUNT ]; do
      for i in "${!PIDS[@]}"; do
        if ! kill -0 "${PIDS[$i]}" 2>/dev/null; then
          unset "PIDS[$i]"
          ((launched--))
        fi
      done
      sleep 1
    done
    
    log "INFO" "Launching: $agent"
    run_agent_loop "$agent" &
    PIDS+=($!)
    ((launched++))
    sleep 1
  done
  
  echo ""
  echo "📊 Monitoring... (tail -f $ACTIVITY_LOG)"
  
  wait "${PIDS[@]}" 2>/dev/null || true
  
  local end_time=$(date +%s)
  local duration=$((end_time - start_time))
  
  echo ""
  echo "=========================================="
  echo "✅ Complete (${duration}s)"
  echo "=========================================="
  
  local completed=0
  for agent in "${AGENTS[@]}"; do
    if should_exit "$agent"; then
      echo "✅ $agent"
      ((completed++))
    else
      echo "❌ $agent"
    fi
  done
  
  echo ""
  echo "Result: $completed/${#AGENTS[@]} completed"
  
  if [ "$ENABLE_METRICS" = true ]; then
    log_metric "session_end" "1"
    log_metric "duration_seconds" "$duration"
    log_metric "agents_completed" "$completed"
  fi
}

main "$@"
