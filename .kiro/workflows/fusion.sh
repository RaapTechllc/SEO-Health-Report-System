#!/bin/bash
# fusion.sh - Enhanced F-Thread implementation for result consolidation
# Runs multiple agents on same task, then fuses results for higher confidence

set -e

#===============================================================================
# CONFIGURATION
#===============================================================================

# Defaults (can be overridden via CLI)
FUSION_MODE=${FUSION_MODE:-"majority"}
AGENT_COUNT=${AGENT_COUNT:-3}
AGENT_TYPE=${AGENT_TYPE:-"code-surgeon"}
PROMPT=${PROMPT:-"Review the codebase for issues"}
OUTPUT_DIR="agents/fusion-results"
ACTIVITY_LOG="activity.log"
METRICS_FILE=".kiro/metrics.csv"
ENABLE_METRICS=${ENABLE_METRICS:-true}
TIMEOUT_MINUTES=${TIMEOUT_MINUTES:-30}
MIN_CONFIDENCE=${MIN_CONFIDENCE:-7}
CONSENSUS_THRESHOLD=${CONSENSUS_THRESHOLD:-0.6}  # 60% agreement for majority

#===============================================================================
# PARSE COMMAND LINE ARGUMENTS
#===============================================================================

show_help() {
  cat << EOF
Usage: fusion.sh [OPTIONS]

F-Thread fusion workflow - runs multiple agents on the same task and consolidates results.

OPTIONS:
  -m, --mode=MODE         Fusion mode: majority, best, merge, consensus, weighted (default: majority)
  -n, --agents=N          Number of agents to run (default: 3)
  -a, --agent-type=TYPE   Agent type to use (default: code-surgeon)
  -p, --prompt=PROMPT     Prompt to send to all agents
  -t, --timeout=MINUTES   Timeout per agent in minutes (default: 30)
  -c, --min-confidence=N  Minimum confidence threshold (default: 7)
  --consensus=THRESHOLD   Consensus threshold for majority mode (default: 0.6)
  --no-metrics            Disable metrics tracking
  -h, --help              Show this help message

FUSION MODES:
  majority    - Count common findings, keep those above consensus threshold
  best        - Select single highest-confidence result
  merge       - Combine all unique findings from all agents
  consensus   - Only keep findings that ALL agents agree on
  weighted    - Weight findings by agent confidence scores

EXAMPLES:
  # Run 5 agents and use majority vote
  ./fusion.sh --mode=majority --agents=5

  # Run code review with specific prompt
  ./fusion.sh --agent-type=code-surgeon --prompt="Review auth module for security issues"

  # High-confidence consensus mode
  ./fusion.sh --mode=consensus --agents=7 --min-confidence=8

THREAD TYPE:
  This script implements F-Threads (Fusion Threads) from the
  Thread-Based Engineering framework. Use it to gain higher
  confidence by running multiple agents and consolidating results.

EOF
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -m|--mode)
      FUSION_MODE="$2"
      shift 2
      ;;
    --mode=*)
      FUSION_MODE="${1#*=}"
      shift
      ;;
    -n|--agents)
      AGENT_COUNT="$2"
      shift 2
      ;;
    --agents=*)
      AGENT_COUNT="${1#*=}"
      shift
      ;;
    -a|--agent-type)
      AGENT_TYPE="$2"
      shift 2
      ;;
    --agent-type=*)
      AGENT_TYPE="${1#*=}"
      shift
      ;;
    -p|--prompt)
      PROMPT="$2"
      shift 2
      ;;
    --prompt=*)
      PROMPT="${1#*=}"
      shift
      ;;
    -t|--timeout)
      TIMEOUT_MINUTES="$2"
      shift 2
      ;;
    --timeout=*)
      TIMEOUT_MINUTES="${1#*=}"
      shift
      ;;
    -c|--min-confidence)
      MIN_CONFIDENCE="$2"
      shift 2
      ;;
    --min-confidence=*)
      MIN_CONFIDENCE="${1#*=}"
      shift
      ;;
    --consensus=*)
      CONSENSUS_THRESHOLD="${1#*=}"
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

log() {
  local level=$1
  local message=$2
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] [$level] $message"
  echo "$timestamp: [F-Thread] $message" >> "$ACTIVITY_LOG"
}

log_metric() {
  if [ "$ENABLE_METRICS" = true ]; then
    local metric=$1
    local value=$2
    echo "$(date -Iseconds),$metric,$value,f-thread,$SESSION_ID" >> "$METRICS_FILE"
  fi
}

calculate_confidence() {
  local file=$1
  # Extract confidence score from result file
  local conf=$(grep -iE "confidence[:\s]*[0-9]+" "$file" 2>/dev/null | grep -oE "[0-9]+" | head -1)
  echo "${conf:-5}"
}

#===============================================================================
# AGENT EXECUTION
#===============================================================================

run_fusion_agent() {
  local index=$1
  local agent=$2
  local prompt=$3
  local timeout_sec=$((TIMEOUT_MINUTES * 60))
  local start_time=$(date +%s)
  
  local output_file="$OUTPUT_DIR/agent-$index-result.md"
  local log_file="$OUTPUT_DIR/agent-$index.log"
  
  log "INFO" "Starting fusion agent $index ($agent)"
  
  # Initialize log
  echo "$(date): Starting agent $index" > "$log_file"
  echo "Agent: $agent" >> "$log_file"
  echo "Prompt: $prompt" >> "$log_file"
  echo "---" >> "$log_file"
  
  # Run agent with timeout
  # REPLACE THIS BLOCK WITH ACTUAL KIRO-CLI EXECUTION:
  # timeout ${timeout_sec}s kiro-cli --agent "$agent" --prompt "$prompt" > "$output_file" 2>> "$log_file"
  
  # Simulated execution (remove in production)
  sleep $((RANDOM % 10 + 3))
  
  # Generate simulated output with varying findings
  local conf=$((RANDOM % 4 + 6))
  local finding_count=$((RANDOM % 5 + 2))
  
  cat > "$output_file" << EOF
# Agent $index Analysis Results

## Task
$prompt

## Findings
EOF
  
  # Generate varied findings for realistic fusion testing
  local findings=("Security vulnerability in auth module" "Missing input validation" "SQL injection risk" "XSS vulnerability" "Hardcoded credentials" "Insecure API endpoint" "Missing rate limiting" "Weak password policy")
  local selected_findings=()
  
  for i in $(seq 1 $finding_count); do
    local idx=$((RANDOM % ${#findings[@]}))
    echo "- ${findings[$idx]}" >> "$output_file"
    selected_findings+=("${findings[$idx]}")
  done
  
  cat >> "$output_file" << EOF

## Confidence: $conf/10

## Severity Assessment
- Critical: $((RANDOM % 2))
- High: $((RANDOM % 3))
- Medium: $((RANDOM % 4 + 1))
- Low: $((RANDOM % 3))

## Recommendations
EOF
  
  for i in $(seq 1 $((RANDOM % 3 + 1))); do
    echo "$i. Fix finding: ${selected_findings[$((i-1))]:-General improvement needed}" >> "$output_file"
  done
  
  cat >> "$output_file" << EOF

## Agent Metadata
- Agent ID: $index
- Agent Type: $agent
- Execution Time: $(($(date +%s) - start_time))s
- Timestamp: $(date -Iseconds)
EOF
  
  echo "$(date): Agent $index completed (confidence: $conf)" >> "$log_file"
  echo "<promise>DONE</promise>" >> "$log_file"
  
  log "INFO" "Agent $index completed with confidence $conf/10"
  log_metric "agent_confidence" "$conf" 
}

#===============================================================================
# FUSION ALGORITHMS
#===============================================================================

fuse_majority() {
  log "INFO" "Applying majority vote fusion (threshold: ${CONSENSUS_THRESHOLD})"
  
  local output_file="$OUTPUT_DIR/fusion-result.md"
  local min_count=$(echo "$AGENT_COUNT * $CONSENSUS_THRESHOLD" | bc | cut -d. -f1)
  [ -z "$min_count" ] && min_count=$((AGENT_COUNT / 2))
  
  cat > "$output_file" << EOF
# F-Thread Fusion Results (Majority Vote)

## Fusion Parameters
- Agents: $AGENT_COUNT
- Mode: majority
- Consensus Threshold: ${CONSENSUS_THRESHOLD} (min $min_count agents must agree)
- Timestamp: $(date -Iseconds)

## Consensus Findings
Findings that appeared in at least $min_count agent results:

EOF
  
  # Extract and count findings
  cat "$OUTPUT_DIR"/agent-*-result.md 2>/dev/null | \
    grep -E "^- " | \
    sort | \
    uniq -c | \
    sort -rn | \
    while read count finding; do
      if [ "$count" -ge "$min_count" ]; then
        echo "- [${count}/${AGENT_COUNT}] $finding" >> "$output_file"
      fi
    done
  
  # Calculate consensus score
  local total_findings=$(cat "$OUTPUT_DIR"/agent-*-result.md 2>/dev/null | grep -E "^- " | wc -l)
  local consensus_findings=$(cat "$OUTPUT_DIR"/agent-*-result.md 2>/dev/null | grep -E "^- " | sort | uniq -c | awk -v min="$min_count" '$1 >= min' | wc -l)
  local consensus_score=0
  [ "$total_findings" -gt 0 ] && consensus_score=$((consensus_findings * 100 / AGENT_COUNT))
  
  cat >> "$output_file" << EOF

## Fusion Statistics
- Total unique findings: $(cat "$OUTPUT_DIR"/agent-*-result.md 2>/dev/null | grep -E "^- " | sort -u | wc -l)
- Consensus findings: $consensus_findings
- Consensus score: ${consensus_score}%

## Individual Agent Confidences
EOF
  
  for f in "$OUTPUT_DIR"/agent-*-result.md; do
    local agent_num=$(basename "$f" | grep -oE "[0-9]+")
    local conf=$(calculate_confidence "$f")
    echo "- Agent $agent_num: $conf/10" >> "$output_file"
  done
  
  log_metric "fusion_consensus_score" "$consensus_score"
  log "INFO" "Majority fusion complete: $output_file"
}

fuse_best() {
  log "INFO" "Selecting best result by confidence (min: $MIN_CONFIDENCE)"
  
  local best_file=""
  local best_conf=0
  local best_agent=0
  
  for f in "$OUTPUT_DIR"/agent-*-result.md; do
    local conf=$(calculate_confidence "$f")
    if [ "$conf" -gt "$best_conf" ]; then
      best_conf=$conf
      best_file=$f
      best_agent=$(basename "$f" | grep -oE "[0-9]+")
    fi
  done
  
  if [ -z "$best_file" ] || [ "$best_conf" -lt "$MIN_CONFIDENCE" ]; then
    log "WARN" "No agent met minimum confidence threshold ($MIN_CONFIDENCE)"
    echo "# Fusion Failed - No High Confidence Result" > "$OUTPUT_DIR/fusion-result.md"
    echo "Best confidence: $best_conf (required: $MIN_CONFIDENCE)" >> "$OUTPUT_DIR/fusion-result.md"
    return 1
  fi
  
  local output_file="$OUTPUT_DIR/fusion-result.md"
  
  cat > "$output_file" << EOF
# F-Thread Fusion Results (Best Selection)

## Selection Criteria
- Mode: best
- Minimum confidence: $MIN_CONFIDENCE
- Selected: Agent $best_agent (confidence: $best_conf/10)
- Timestamp: $(date -Iseconds)

## Selected Result

EOF
  
  cat "$best_file" >> "$output_file"
  
  cat >> "$output_file" << EOF

## Other Agent Scores
EOF
  
  for f in "$OUTPUT_DIR"/agent-*-result.md; do
    local agent_num=$(basename "$f" | grep -oE "[0-9]+")
    local conf=$(calculate_confidence "$f")
    local marker=""
    [ "$f" = "$best_file" ] && marker=" (SELECTED)"
    echo "- Agent $agent_num: $conf/10$marker" >> "$output_file"
  done
  
  log_metric "fusion_best_confidence" "$best_conf"
  log "INFO" "Best selection complete: Agent $best_agent (confidence: $best_conf)"
}

fuse_merge() {
  log "INFO" "Merging all unique findings"
  
  local output_file="$OUTPUT_DIR/fusion-result.md"
  
  cat > "$output_file" << EOF
# F-Thread Fusion Results (Merged)

## Fusion Parameters
- Agents: $AGENT_COUNT
- Mode: merge
- Timestamp: $(date -Iseconds)

## All Unique Findings
EOF
  
  cat "$OUTPUT_DIR"/agent-*-result.md 2>/dev/null | grep -E "^- " | sort -u >> "$output_file"
  
  cat >> "$output_file" << EOF

## All Recommendations
EOF
  
  cat "$OUTPUT_DIR"/agent-*-result.md 2>/dev/null | grep -E "^[0-9]+\. " | sort -u >> "$output_file"
  
  local unique_count=$(cat "$OUTPUT_DIR"/agent-*-result.md 2>/dev/null | grep -E "^- " | sort -u | wc -l)
  
  cat >> "$output_file" << EOF

## Merge Statistics
- Total unique findings: $unique_count
- Source agents: $AGENT_COUNT
EOF
  
  log_metric "fusion_merged_findings" "$unique_count"
  log "INFO" "Merge fusion complete: $unique_count unique findings"
}

fuse_consensus() {
  log "INFO" "Applying strict consensus (100% agreement required)"
  
  local output_file="$OUTPUT_DIR/fusion-result.md"
  
  cat > "$output_file" << EOF
# F-Thread Fusion Results (Strict Consensus)

## Fusion Parameters
- Agents: $AGENT_COUNT
- Mode: consensus (100% agreement)
- Timestamp: $(date -Iseconds)

## Consensus Findings
Only findings that ALL agents agreed on:

EOF
  
  # Find findings that appear in ALL agent results
  cat "$OUTPUT_DIR"/agent-*-result.md 2>/dev/null | \
    grep -E "^- " | \
    sort | \
    uniq -c | \
    awk -v count="$AGENT_COUNT" '$1 == count {$1=""; print}' >> "$output_file"
  
  local consensus_count=$(cat "$OUTPUT_DIR"/agent-*-result.md 2>/dev/null | grep -E "^- " | sort | uniq -c | awk -v count="$AGENT_COUNT" '$1 == count' | wc -l)
  
  cat >> "$output_file" << EOF

## Consensus Statistics
- Findings with 100% agreement: $consensus_count
- Total agents: $AGENT_COUNT
EOF
  
  log_metric "fusion_consensus_count" "$consensus_count"
  log "INFO" "Strict consensus complete: $consensus_count findings with full agreement"
}

fuse_weighted() {
  log "INFO" "Applying weighted fusion by confidence scores"
  
  local output_file="$OUTPUT_DIR/fusion-result.md"
  
  cat > "$output_file" << EOF
# F-Thread Fusion Results (Weighted)

## Fusion Parameters
- Agents: $AGENT_COUNT
- Mode: weighted
- Timestamp: $(date -Iseconds)

## Weighted Findings
Findings weighted by agent confidence scores:

EOF
  
  # Create temp file for weighted scoring
  local temp_file=$(mktemp)
  
  for f in "$OUTPUT_DIR"/agent-*-result.md; do
    local conf=$(calculate_confidence "$f")
    # Extract findings and weight by confidence
    grep -E "^- " "$f" 2>/dev/null | while read finding; do
      echo "$conf $finding" >> "$temp_file"
    done
  done
  
  # Aggregate weighted scores
  sort "$temp_file" | awk '
    {
      finding = $0
      sub(/^[0-9]+ /, "", finding)
      weight = $1
      scores[finding] += weight
      count[finding]++
    }
    END {
      for (f in scores) {
        avg = scores[f] / count[f]
        printf "%.1f|%s\n", scores[f], f
      }
    }
  ' | sort -t'|' -k1 -rn | while IFS='|' read score finding; do
    echo "- [$score pts] $finding" >> "$output_file"
  done
  
  rm -f "$temp_file"
  
  log "INFO" "Weighted fusion complete"
}

#===============================================================================
# MAIN EXECUTION
#===============================================================================

main() {
  local start_time=$(date +%s)
  
  echo "=========================================="
  echo "F-Thread Fusion Workflow"
  echo "=========================================="
  echo "Mode: $FUSION_MODE"
  echo "Agents: $AGENT_COUNT"
  echo "Agent Type: $AGENT_TYPE"
  echo "Prompt: ${PROMPT:0:50}..."
  echo "Timeout: ${TIMEOUT_MINUTES}m per agent"
  echo "=========================================="
  
  # Initialize
  mkdir -p "$OUTPUT_DIR"
  mkdir -p "$(dirname "$METRICS_FILE")"
  
  if [ "$ENABLE_METRICS" = true ] && [ ! -f "$METRICS_FILE" ]; then
    echo "timestamp,metric,value,thread_type,session_id" > "$METRICS_FILE"
  fi
  
  log "INFO" "Starting F-Thread fusion with $AGENT_COUNT agents"
  log_metric "session_start" "1"
  log_metric "fusion_mode" "$FUSION_MODE"
  log_metric "agent_count" "$AGENT_COUNT"
  
  # Launch all agents in parallel
  echo ""
  echo "Launching $AGENT_COUNT agents in parallel..."
  
  declare -a PIDS
  for i in $(seq 1 $AGENT_COUNT); do
    run_fusion_agent "$i" "$AGENT_TYPE" "$PROMPT" &
    PIDS+=($!)
    sleep 0.5  # Slight stagger to prevent resource spike
  done
  
  # Wait for all agents to complete
  echo "Waiting for agents to complete..."
  wait "${PIDS[@]}"
  
  echo ""
  echo "All agents completed. Applying fusion..."
  echo ""
  
  # Apply fusion based on mode
  case $FUSION_MODE in
    majority)
      fuse_majority
      ;;
    best)
      fuse_best
      ;;
    merge)
      fuse_merge
      ;;
    consensus)
      fuse_consensus
      ;;
    weighted)
      fuse_weighted
      ;;
    *)
      log "ERROR" "Unknown fusion mode: $FUSION_MODE"
      exit 1
      ;;
  esac
  
  # Calculate duration
  local end_time=$(date +%s)
  local duration=$((end_time - start_time))
  
  # Final report
  echo ""
  echo "=========================================="
  echo "F-Thread Fusion Complete!"
  echo "=========================================="
  echo "Mode: $FUSION_MODE"
  echo "Agents: $AGENT_COUNT"
  echo "Duration: ${duration}s"
  echo "Results: $OUTPUT_DIR/fusion-result.md"
  echo ""
  
  # Show preview of results
  echo "Preview:"
  echo "---"
  head -30 "$OUTPUT_DIR/fusion-result.md"
  echo "..."
  echo ""
  
  # Log final metrics
  log_metric "session_end" "1"
  log_metric "duration_seconds" "$duration"
  
  log "INFO" "F-Thread fusion complete in ${duration}s"
}

# Run main
main "$@"
