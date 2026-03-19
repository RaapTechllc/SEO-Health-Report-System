#!/bin/bash
# b-thread-orchestrator.sh - B-Thread meta-orchestration for nested thread compositions
# Coordinates P-threads, F-threads, C-threads, and L-threads in complex workflows

set -e

#===============================================================================
# CONFIGURATION
#===============================================================================

WORKFLOW_NAME=${WORKFLOW_NAME:-"b-thread-workflow"}
COMPOSITION_FILE=${COMPOSITION_FILE:-""}
OUTPUT_DIR="agents/b-thread-$WORKFLOW_NAME"
STATE_DIR=".kiro/thread-state"
ACTIVITY_LOG="activity.log"
METRICS_FILE=".kiro/metrics.csv"
ENABLE_METRICS=${ENABLE_METRICS:-true}
MAX_RETRIES=${MAX_RETRIES:-3}
STALL_THRESHOLD_MINUTES=${STALL_THRESHOLD_MINUTES:-15}

#===============================================================================
# PARSE COMMAND LINE ARGUMENTS
#===============================================================================

show_help() {
  cat << EOF
Usage: b-thread-orchestrator.sh [OPTIONS]

B-Thread meta-orchestrator - coordinates nested thread compositions.

OPTIONS:
  -n, --name=NAME           Workflow name (default: b-thread-workflow)
  -c, --composition=FILE    JSON file defining thread composition
  -t, --template=TYPE       Built-in template: feature, review, deploy
  --max-retries=N           Max retries for failed threads (default: 3)
  --stall-threshold=MIN     Minutes before restarting stalled thread (default: 15)
  --no-metrics              Disable metrics tracking
  -h, --help                Show this help message

BUILT-IN TEMPLATES:
  feature  - Full feature development with nested threads
  review   - Multi-agent code review with fusion
  deploy   - Deployment workflow with validation

COMPOSITION FILE FORMAT:
  {
    "name": "my-workflow",
    "phases": [
      {
        "name": "research",
        "type": "p-thread",
        "agents": ["security-specialist", "test-architect"]
      },
      {
        "name": "review",
        "type": "f-thread",
        "agent": "code-surgeon",
        "count": 3,
        "fusion": "majority"
      },
      {
        "name": "deploy",
        "type": "c-thread",
        "phases": ["prepare", "execute", "validate"]
      }
    ]
  }

EXAMPLES:
  # Run with built-in template
  ./b-thread-orchestrator.sh --template=feature --name=user-auth

  # Run with custom composition
  ./b-thread-orchestrator.sh --composition=my-workflow.json

THREAD TYPE:
  This script implements B-Threads (Big/Meta Threads) from the
  Thread-Based Engineering framework. It orchestrates other thread
  types for complex, multi-phase workflows.

EOF
}

TEMPLATE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    -n|--name)
      WORKFLOW_NAME="$2"
      shift 2
      ;;
    --name=*)
      WORKFLOW_NAME="${1#*=}"
      shift
      ;;
    -c|--composition)
      COMPOSITION_FILE="$2"
      shift 2
      ;;
    --composition=*)
      COMPOSITION_FILE="${1#*=}"
      shift
      ;;
    -t|--template)
      TEMPLATE="$2"
      shift 2
      ;;
    --template=*)
      TEMPLATE="${1#*=}"
      shift
      ;;
    --max-retries=*)
      MAX_RETRIES="${1#*=}"
      shift
      ;;
    --stall-threshold=*)
      STALL_THRESHOLD_MINUTES="${1#*=}"
      shift
      ;;
    --no-metrics)
      ENABLE_METRICS=false
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
# UTILITY FUNCTIONS
#===============================================================================

SESSION_ID=$(date +%s)
OUTPUT_DIR="agents/b-thread-$WORKFLOW_NAME"

log() {
  local level=$1
  local message=$2
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] [$level] $message"
  echo "$timestamp: [B-Thread] $message" >> "$ACTIVITY_LOG"
}

log_metric() {
  if [ "$ENABLE_METRICS" = true ]; then
    local metric=$1
    local value=$2
    echo "$(date -Iseconds),$metric,$value,b-thread,$SESSION_ID" >> "$METRICS_FILE"
  fi
}

save_thread_state() {
  local thread_name=$1
  local thread_type=$2
  local status=$3
  
  mkdir -p "$STATE_DIR"
  cat > "$STATE_DIR/${thread_name}.json" << EOF
{
  "name": "$thread_name",
  "type": "$thread_type",
  "status": "$status",
  "timestamp": "$(date -Iseconds)",
  "session_id": "$SESSION_ID"
}
EOF
}

load_thread_state() {
  local thread_name=$1
  local state_file="$STATE_DIR/${thread_name}.json"
  
  if [ -f "$state_file" ]; then
    cat "$state_file"
    return 0
  fi
  return 1
}

check_thread_complete() {
  local thread_name=$1
  local state_file="$STATE_DIR/${thread_name}.json"
  
  if [ -f "$state_file" ]; then
    grep -q '"status": "complete"' "$state_file" && return 0
  fi
  return 1
}

#===============================================================================
# THREAD EXECUTION FUNCTIONS
#===============================================================================

run_p_thread() {
  local name=$1
  local agents=$2  # Comma-separated
  
  log "INFO" "Starting P-Thread: $name"
  save_thread_state "$name" "p-thread" "running"
  
  local output_dir="$OUTPUT_DIR/p-thread-$name"
  mkdir -p "$output_dir"
  
  # Convert agents to array
  IFS=',' read -ra agent_list <<< "$agents"
  
  # Call ralph-kiro.sh with custom agents
  ./.kiro/workflows/ralph-kiro.sh \
    --agents="$agents" \
    --parallel=${#agent_list[@]} \
    2>&1 | tee "$output_dir/execution.log"
  
  local exit_code=$?
  
  if [ $exit_code -eq 0 ]; then
    save_thread_state "$name" "p-thread" "complete"
    log "INFO" "P-Thread $name completed successfully"
    return 0
  else
    save_thread_state "$name" "p-thread" "failed"
    log "ERROR" "P-Thread $name failed"
    return 1
  fi
}

run_f_thread() {
  local name=$1
  local agent=$2
  local count=$3
  local fusion_mode=$4
  
  log "INFO" "Starting F-Thread: $name (${count}x $agent, mode: $fusion_mode)"
  save_thread_state "$name" "f-thread" "running"
  
  local output_dir="$OUTPUT_DIR/f-thread-$name"
  mkdir -p "$output_dir"
  
  # Call fusion.sh
  ./.kiro/workflows/fusion.sh \
    --mode="$fusion_mode" \
    --agents="$count" \
    --agent-type="$agent" \
    2>&1 | tee "$output_dir/execution.log"
  
  local exit_code=$?
  
  if [ $exit_code -eq 0 ]; then
    save_thread_state "$name" "f-thread" "complete"
    log "INFO" "F-Thread $name completed successfully"
    return 0
  else
    save_thread_state "$name" "f-thread" "failed"
    log "ERROR" "F-Thread $name failed"
    return 1
  fi
}

run_c_thread() {
  local name=$1
  local phases=$2  # Comma-separated
  local agent=$3
  
  log "INFO" "Starting C-Thread: $name"
  save_thread_state "$name" "c-thread" "running"
  
  local output_dir="$OUTPUT_DIR/c-thread-$name"
  mkdir -p "$output_dir"
  
  # Call chain-workflow.sh
  ./.kiro/workflows/chain-workflow.sh \
    --name="$name" \
    --phases="$phases" \
    --agent="${agent:-orchestrator}" \
    --auto \
    2>&1 | tee "$output_dir/execution.log"
  
  local exit_code=$?
  
  if [ $exit_code -eq 0 ]; then
    save_thread_state "$name" "c-thread" "complete"
    log "INFO" "C-Thread $name completed successfully"
    return 0
  else
    save_thread_state "$name" "c-thread" "failed"
    log "ERROR" "C-Thread $name failed"
    return 1
  fi
}

run_l_thread() {
  local name=$1
  local agent=$2
  local max_hours=$3
  
  log "INFO" "Starting L-Thread: $name (agent: $agent, max: ${max_hours}h)"
  save_thread_state "$name" "l-thread" "running"
  
  local output_dir="$OUTPUT_DIR/l-thread-$name"
  mkdir -p "$output_dir"
  
  # Call ralph-kiro.sh in long-running mode
  ./.kiro/workflows/ralph-kiro.sh \
    --agents="$agent" \
    --parallel=1 \
    --timeout="$max_hours" \
    --max-iter=200 \
    2>&1 | tee "$output_dir/execution.log"
  
  local exit_code=$?
  
  if [ $exit_code -eq 0 ]; then
    save_thread_state "$name" "l-thread" "complete"
    log "INFO" "L-Thread $name completed successfully"
    return 0
  else
    save_thread_state "$name" "l-thread" "failed"
    log "ERROR" "L-Thread $name failed"
    return 1
  fi
}

#===============================================================================
# BUILT-IN TEMPLATES
#===============================================================================

run_feature_template() {
  log "INFO" "Running feature development template"
  
  # Phase 1: Research (P-Thread)
  echo ""
  echo "=== Phase 1: Research (P-Thread) ==="
  run_p_thread "research" "security-specialist,test-architect" || true
  
  # Phase 2: Design (C-Thread)
  echo ""
  echo "=== Phase 2: Design (C-Thread) ==="
  run_c_thread "design" "requirements,architecture,api-design" "orchestrator" || true
  
  # Phase 3: Implementation (P-Thread)
  echo ""
  echo "=== Phase 3: Implementation (P-Thread) ==="
  run_p_thread "implement" "frontend-designer,db-wizard,code-surgeon" || true
  
  # Phase 4: Review (F-Thread)
  echo ""
  echo "=== Phase 4: Review (F-Thread) ==="
  run_f_thread "review" "code-surgeon" 3 "majority" || true
  
  # Phase 5: Deploy (C-Thread)
  echo ""
  echo "=== Phase 5: Deploy (C-Thread) ==="
  run_c_thread "deploy" "test,stage,production" "devops-automator" || true
}

run_review_template() {
  log "INFO" "Running code review template"
  
  # Parallel initial review
  echo ""
  echo "=== Phase 1: Parallel Initial Review ==="
  run_p_thread "initial-review" "security-specialist,test-architect,code-surgeon" || true
  
  # Fusion deep review
  echo ""
  echo "=== Phase 2: Fusion Deep Review ==="
  run_f_thread "deep-review" "code-surgeon" 5 "weighted" || true
  
  # Final synthesis
  echo ""
  echo "=== Phase 3: Final Synthesis ==="
  run_c_thread "synthesis" "compile-findings,prioritize,create-report" "doc-smith" || true
}

run_deploy_template() {
  log "INFO" "Running deployment template"
  
  # Pre-deploy validation (F-Thread)
  echo ""
  echo "=== Phase 1: Pre-Deploy Validation ==="
  run_f_thread "pre-validate" "security-specialist" 3 "consensus" || true
  
  # Deployment (C-Thread)
  echo ""
  echo "=== Phase 2: Deployment ==="
  run_c_thread "deployment" "backup,migrate,deploy,verify" "devops-automator" || true
  
  # Post-deploy monitoring (L-Thread) - uses devops-automator
  echo ""
  echo "=== Phase 3: Post-Deploy Monitoring ==="
  run_l_thread "monitoring" "devops-automator" 2 || true
}

#===============================================================================
# COMPOSITION FILE EXECUTION
#===============================================================================

run_composition_file() {
  local file=$1
  
  if [ ! -f "$file" ]; then
    log "ERROR" "Composition file not found: $file"
    exit 1
  fi
  
  log "INFO" "Running composition from: $file"
  
  # Parse and execute each phase
  # Note: This requires jq for JSON parsing
  if ! command -v jq &> /dev/null; then
    log "ERROR" "jq is required for composition files. Install with: apt install jq"
    exit 1
  fi
  
  local phase_count=$(jq '.phases | length' "$file")
  
  for i in $(seq 0 $((phase_count - 1))); do
    local phase_name=$(jq -r ".phases[$i].name" "$file")
    local phase_type=$(jq -r ".phases[$i].type" "$file")
    
    echo ""
    echo "=== Phase $((i + 1))/$phase_count: $phase_name ($phase_type) ==="
    
    case $phase_type in
      p-thread)
        local agents=$(jq -r ".phases[$i].agents | join(\",\")" "$file")
        run_p_thread "$phase_name" "$agents" || true
        ;;
      f-thread)
        local agent=$(jq -r ".phases[$i].agent" "$file")
        local count=$(jq -r ".phases[$i].count // 3" "$file")
        local fusion=$(jq -r ".phases[$i].fusion // \"majority\"" "$file")
        run_f_thread "$phase_name" "$agent" "$count" "$fusion" || true
        ;;
      c-thread)
        local phases=$(jq -r ".phases[$i].phases | join(\",\")" "$file")
        local agent=$(jq -r ".phases[$i].agent // \"orchestrator\"" "$file")
        run_c_thread "$phase_name" "$phases" "$agent" || true
        ;;
      l-thread)
        local agent=$(jq -r ".phases[$i].agent" "$file")
        local hours=$(jq -r ".phases[$i].hours // 4" "$file")
        run_l_thread "$phase_name" "$agent" "$hours" || true
        ;;
      *)
        log "WARN" "Unknown phase type: $phase_type"
        ;;
    esac
  done
}

#===============================================================================
# MAIN EXECUTION
#===============================================================================

main() {
  local start_time=$(date +%s)
  
  echo "=========================================="
  echo "B-Thread Meta-Orchestrator"
  echo "=========================================="
  echo "Workflow: $WORKFLOW_NAME"
  echo "Template: ${TEMPLATE:-custom}"
  echo "Composition: ${COMPOSITION_FILE:-none}"
  echo "=========================================="
  
  # Initialize
  mkdir -p "$OUTPUT_DIR"
  mkdir -p "$STATE_DIR"
  mkdir -p "$(dirname "$METRICS_FILE")"
  
  if [ "$ENABLE_METRICS" = true ] && [ ! -f "$METRICS_FILE" ]; then
    echo "timestamp,metric,value,thread_type,session_id" > "$METRICS_FILE"
  fi
  
  log "INFO" "Starting B-Thread orchestration: $WORKFLOW_NAME"
  log_metric "session_start" "1"
  
  # Execute based on input type
  if [ -n "$COMPOSITION_FILE" ]; then
    run_composition_file "$COMPOSITION_FILE"
  elif [ -n "$TEMPLATE" ]; then
    case $TEMPLATE in
      feature)
        run_feature_template
        ;;
      review)
        run_review_template
        ;;
      deploy)
        run_deploy_template
        ;;
      *)
        log "ERROR" "Unknown template: $TEMPLATE"
        exit 1
        ;;
    esac
  else
    log "ERROR" "No template or composition file specified"
    show_help
    exit 1
  fi
  
  # Calculate duration
  local end_time=$(date +%s)
  local duration=$((end_time - start_time))
  local duration_min=$((duration / 60))
  
  # Collect thread results
  echo ""
  echo "=========================================="
  echo "B-Thread Orchestration Complete!"
  echo "=========================================="
  echo "Duration: ${duration_min} minutes"
  echo ""
  echo "Thread Results:"
  echo "---------------"
  
  local completed=0
  local failed=0
  
  for state_file in "$STATE_DIR"/*.json; do
    if [ -f "$state_file" ]; then
      local name=$(basename "$state_file" .json)
      local status=$(grep -o '"status": "[^"]*"' "$state_file" | cut -d'"' -f4)
      local type=$(grep -o '"type": "[^"]*"' "$state_file" | cut -d'"' -f4)
      
      if [ "$status" = "complete" ]; then
        echo "  [COMPLETE] $name ($type)"
        ((completed++))
      else
        echo "  [FAILED] $name ($type)"
        ((failed++))
      fi
    fi
  done
  
  echo ""
  echo "Summary: $completed completed, $failed failed"
  echo "Output: $OUTPUT_DIR/"
  echo ""
  
  # Log final metrics
  log_metric "session_end" "1"
  log_metric "duration_seconds" "$duration"
  log_metric "threads_completed" "$completed"
  log_metric "threads_failed" "$failed"
  
  log "INFO" "B-Thread orchestration complete: $completed threads succeeded"
  
  if [ "$failed" -gt 0 ]; then
    exit 1
  fi
}

# Run main
main "$@"
