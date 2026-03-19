#!/bin/bash
# metrics-tracker.sh - Comprehensive thread performance metrics and dashboard
# Tracks tool calls, duration, parallel count, success rate, and improvement trends

set -e

#===============================================================================
# CONFIGURATION
#===============================================================================

METRICS_FILE=".kiro/metrics.csv"
REPORT_FILE=".kiro/metrics-report.md"
DASHBOARD_FILE=".kiro/metrics-dashboard.md"
TRENDS_FILE=".kiro/metrics-trends.csv"
SESSION_ID=""
SESSION_START=""

#===============================================================================
# CORE FUNCTIONS
#===============================================================================

# Initialize metrics file if it doesn't exist
init_metrics() {
  mkdir -p "$(dirname "$METRICS_FILE")"
  
  if [ ! -f "$METRICS_FILE" ]; then
    echo "timestamp,metric,value,thread_type,session_id,tags" > "$METRICS_FILE"
    echo "Metrics file initialized: $METRICS_FILE"
  fi
  
  if [ ! -f "$TRENDS_FILE" ]; then
    echo "date,total_sessions,total_tool_calls,avg_duration,success_rate,max_parallel,thread_diversity" > "$TRENDS_FILE"
    echo "Trends file initialized: $TRENDS_FILE"
  fi
}

# Log a metric with optional tags
log_metric() {
  local metric=$1
  local value=$2
  local thread_type=${3:-"base"}
  local session=${4:-$SESSION_ID}
  local tags=${5:-""}
  
  [ -z "$session" ] && session=$(date +%s)
  
  echo "$(date -Iseconds),$metric,$value,$thread_type,$session,$tags" >> "$METRICS_FILE"
}

# Start a session
start_session() {
  local thread_type=$1
  local description=${2:-""}
  
  init_metrics
  
  SESSION_ID=$(date +%s)
  SESSION_START=$(date +%s)
  
  log_metric "session_start" "1" "$thread_type" "$SESSION_ID" "$description"
  echo "$SESSION_ID"
}

# End a session
end_session() {
  local thread_type=$1
  local tool_calls=${2:-0}
  local success=${3:-1}
  
  local duration=$(($(date +%s) - SESSION_START))
  
  log_metric "session_end" "1" "$thread_type" "$SESSION_ID"
  log_metric "duration_seconds" "$duration" "$thread_type" "$SESSION_ID"
  log_metric "tool_calls" "$tool_calls" "$thread_type" "$SESSION_ID"
  log_metric "success" "$success" "$thread_type" "$SESSION_ID"
}

# Log parallel agent count
log_parallel() {
  local count=$1
  log_metric "parallel_agents" "$count" "p-thread" "$SESSION_ID"
}

# Log fusion result
log_fusion() {
  local agent_count=$1
  local fusion_mode=$2
  local confidence=$3
  
  log_metric "fusion_agents" "$agent_count" "f-thread" "$SESSION_ID"
  log_metric "fusion_mode" "$fusion_mode" "f-thread" "$SESSION_ID"
  log_metric "fusion_confidence" "$confidence" "f-thread" "$SESSION_ID"
}

# Log chain phase
log_chain_phase() {
  local phase=$1
  local status=$2
  
  log_metric "chain_phase" "$phase" "c-thread" "$SESSION_ID"
  log_metric "phase_status" "$status" "c-thread" "$SESSION_ID"
}

# Log B-thread composition
log_composition() {
  local composition_type=$1
  local child_threads=$2
  
  log_metric "composition_type" "$composition_type" "b-thread" "$SESSION_ID"
  log_metric "child_threads" "$child_threads" "b-thread" "$SESSION_ID"
}

# Log L-thread autonomy
log_autonomy() {
  local iterations=$1
  local hours=$2
  local checkpoints=$3
  
  log_metric "autonomy_iterations" "$iterations" "l-thread" "$SESSION_ID"
  log_metric "autonomy_hours" "$hours" "l-thread" "$SESSION_ID"
  log_metric "autonomy_checkpoints" "$checkpoints" "l-thread" "$SESSION_ID"
}

#===============================================================================
# ANALYSIS FUNCTIONS
#===============================================================================

# Calculate statistics from metrics
calculate_stats() {
  local period=${1:-"all"}  # all, today, week, month
  local filter=""
  
  case $period in
    today)
      filter=$(date +%Y-%m-%d)
      ;;
    week)
      filter=$(date -d "7 days ago" +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d)
      ;;
    month)
      filter=$(date -d "30 days ago" +%Y-%m-%d 2>/dev/null || date -v-30d +%Y-%m-%d)
      ;;
  esac
  
  if [ -n "$filter" ]; then
    local data=$(grep "$filter" "$METRICS_FILE" 2>/dev/null)
  else
    local data=$(cat "$METRICS_FILE" 2>/dev/null)
  fi
  
  # Calculate metrics
  local total_sessions=$(echo "$data" | grep "session_start" | wc -l)
  local total_tool_calls=$(echo "$data" | awk -F',' '/tool_calls/ {sum+=$3} END {print sum+0}')
  local avg_duration=$(echo "$data" | awk -F',' '/duration_seconds/ {sum+=$3; count++} END {if(count>0) print int(sum/count); else print 0}')
  local success_count=$(echo "$data" | awk -F',' '/,success,1,/ {count++} END {print count+0}')
  local total_completed=$(echo "$data" | grep ",success," | wc -l)
  local success_rate=0
  [ "$total_completed" -gt 0 ] && success_rate=$((success_count * 100 / total_completed))
  local max_parallel=$(echo "$data" | awk -F',' '/parallel_agents/ {if($3>max) max=$3} END {print max+0}')
  
  # Thread type counts
  local base_count=$(echo "$data" | grep ",base," | grep "session_start" | wc -l)
  local p_count=$(echo "$data" | grep ",p-thread," | grep "session_start" | wc -l)
  local c_count=$(echo "$data" | grep ",c-thread," | grep "session_start" | wc -l)
  local f_count=$(echo "$data" | grep ",f-thread," | grep "session_start" | wc -l)
  local b_count=$(echo "$data" | grep ",b-thread," | grep "session_start" | wc -l)
  local l_count=$(echo "$data" | grep ",l-thread," | grep "session_start" | wc -l)
  
  # Calculate thread diversity (unique thread types used)
  local thread_diversity=0
  [ "$base_count" -gt 0 ] && ((thread_diversity++))
  [ "$p_count" -gt 0 ] && ((thread_diversity++))
  [ "$c_count" -gt 0 ] && ((thread_diversity++))
  [ "$f_count" -gt 0 ] && ((thread_diversity++))
  [ "$b_count" -gt 0 ] && ((thread_diversity++))
  [ "$l_count" -gt 0 ] && ((thread_diversity++))
  
  # Output as JSON-like format
  cat << EOF
{
  "period": "$period",
  "total_sessions": $total_sessions,
  "total_tool_calls": $total_tool_calls,
  "avg_duration": $avg_duration,
  "success_rate": $success_rate,
  "max_parallel": $max_parallel,
  "thread_diversity": $thread_diversity,
  "thread_counts": {
    "base": $base_count,
    "p_thread": $p_count,
    "c_thread": $c_count,
    "f_thread": $f_count,
    "b_thread": $b_count,
    "l_thread": $l_count
  }
}
EOF
}

# Record daily trend
record_trend() {
  local today=$(date +%Y-%m-%d)
  
  # Check if already recorded today
  if grep -q "^$today," "$TRENDS_FILE" 2>/dev/null; then
    return 0
  fi
  
  # Get today's stats
  local stats=$(calculate_stats "today")
  
  local sessions=$(echo "$stats" | grep "total_sessions" | grep -oE "[0-9]+")
  local tools=$(echo "$stats" | grep "total_tool_calls" | grep -oE "[0-9]+")
  local duration=$(echo "$stats" | grep "avg_duration" | grep -oE "[0-9]+")
  local success=$(echo "$stats" | grep "success_rate" | grep -oE "[0-9]+")
  local parallel=$(echo "$stats" | grep "max_parallel" | grep -oE "[0-9]+")
  local diversity=$(echo "$stats" | grep "thread_diversity" | head -1 | grep -oE "[0-9]+")
  
  echo "$today,$sessions,$tools,$duration,$success,$parallel,$diversity" >> "$TRENDS_FILE"
}

#===============================================================================
# REPORT GENERATION
#===============================================================================

generate_report() {
  echo "Generating metrics report..."
  
  local stats=$(calculate_stats "all")
  local week_stats=$(calculate_stats "week")
  
  # Extract values
  local total_sessions=$(echo "$stats" | grep '"total_sessions"' | grep -oE "[0-9]+")
  local total_tool_calls=$(echo "$stats" | grep '"total_tool_calls"' | grep -oE "[0-9]+")
  local avg_duration=$(echo "$stats" | grep '"avg_duration"' | grep -oE "[0-9]+")
  local success_rate=$(echo "$stats" | grep '"success_rate"' | grep -oE "[0-9]+")
  local max_parallel=$(echo "$stats" | grep '"max_parallel"' | grep -oE "[0-9]+")
  local thread_diversity=$(echo "$stats" | grep '"thread_diversity"' | head -1 | grep -oE "[0-9]+")
  
  local base_count=$(echo "$stats" | grep '"base"' | grep -oE "[0-9]+")
  local p_count=$(echo "$stats" | grep '"p_thread"' | grep -oE "[0-9]+")
  local c_count=$(echo "$stats" | grep '"c_thread"' | grep -oE "[0-9]+")
  local f_count=$(echo "$stats" | grep '"f_thread"' | grep -oE "[0-9]+")
  local b_count=$(echo "$stats" | grep '"b_thread"' | grep -oE "[0-9]+")
  local l_count=$(echo "$stats" | grep '"l_thread"' | grep -oE "[0-9]+")
  
  cat > "$REPORT_FILE" << EOF
# Thread Metrics Report

Generated: $(date)

## Executive Summary

| Metric | Value | Trend |
|--------|-------|-------|
| Total Sessions | ${total_sessions:-0} | - |
| Total Tool Calls | ${total_tool_calls:-0} | - |
| Average Duration | ${avg_duration:-0}s | - |
| Success Rate | ${success_rate:-0}% | - |
| Max Parallel Agents | ${max_parallel:-0} | - |
| Thread Diversity | ${thread_diversity:-0}/6 | - |

## Sessions by Thread Type

| Thread Type | Count | Percentage |
|-------------|-------|------------|
| Base Thread | ${base_count:-0} | - |
| P-Thread (Parallel) | ${p_count:-0} | - |
| C-Thread (Chained) | ${c_count:-0} | - |
| F-Thread (Fusion) | ${f_count:-0} | - |
| B-Thread (Big/Meta) | ${b_count:-0} | - |
| L-Thread (Long-running) | ${l_count:-0} | - |

## Thread-Based Engineering Metrics

### The Four Ways to Improve

1. **More Threads**: Total sessions = ${total_sessions:-0}
   - Goal: Increase parallel work capacity
   - Track: Sessions per week

2. **Longer Threads**: Average duration = ${avg_duration:-0}s
   - Goal: Extend autonomous execution time
   - Track: Duration trend over time

3. **Thicker Threads**: Max parallel = ${max_parallel:-0}
   - Goal: Nest more sub-threads
   - Track: B-thread composition depth

4. **Fewer Checkpoints**: Success rate = ${success_rate:-0}%
   - Goal: Increase trust in agents
   - Track: Human interventions per session

### Thread Type Distribution

\`\`\`
Base:     ${"#" * ${base_count:-0}} (${base_count:-0})
P-Thread: ${"#" * ${p_count:-0}} (${p_count:-0})
C-Thread: ${"#" * ${c_count:-0}} (${c_count:-0})
F-Thread: ${"#" * ${f_count:-0}} (${f_count:-0})
B-Thread: ${"#" * ${b_count:-0}} (${b_count:-0})
L-Thread: ${"#" * ${l_count:-0}} (${l_count:-0})
\`\`\`

## Recent Activity

### Last 10 Sessions
\`\`\`
$(grep "session_start" "$METRICS_FILE" | tail -10 | awk -F',' '{print $1, $4, "(session: "$5")"}')
\`\`\`

### Recent Tool Calls
\`\`\`
$(grep "tool_calls" "$METRICS_FILE" | tail -5)
\`\`\`

## Recommendations

Based on current metrics:

$(if [ "${total_sessions:-0}" -lt 10 ]; then echo "- **Start More Threads**: You have fewer than 10 sessions. Try running parallel agents."; fi)
$(if [ "${avg_duration:-0}" -lt 300 ]; then echo "- **Extend Thread Duration**: Average duration is under 5 minutes. Try L-threads for longer work."; fi)
$(if [ "${max_parallel:-0}" -lt 3 ]; then echo "- **Increase Parallelism**: Max parallel is low. Try running 5+ agents with P-threads."; fi)
$(if [ "${thread_diversity:-0}" -lt 3 ]; then echo "- **Diversify Thread Types**: You're using fewer than 3 thread types. Try F-threads for fusion."; fi)

---

*Generated by metrics-tracker.sh | Run \`./metrics-tracker.sh report\` to regenerate*
EOF

  echo "Report generated: $REPORT_FILE"
}

generate_dashboard() {
  echo "Generating metrics dashboard..."
  
  record_trend
  
  cat > "$DASHBOARD_FILE" << EOF
# Thread Metrics Dashboard

Last Updated: $(date)

## Quick Stats (Last 7 Days)

$(calculate_stats "week" | grep -E "total_sessions|total_tool_calls|success_rate" | head -5)

## Daily Trends

\`\`\`
Date       | Sessions | Tool Calls | Avg Duration | Success Rate | Max Parallel
-----------|----------|------------|--------------|--------------|-------------
$(tail -7 "$TRENDS_FILE" 2>/dev/null | awk -F',' 'NR>1 {printf "%-10s | %8s | %10s | %12s | %12s%% | %12s\n", $1, $2, $3, $4"s", $5, $6}')
\`\`\`

## Thread Type Activity (All Time)

\`\`\`
$(grep "session_start" "$METRICS_FILE" 2>/dev/null | awk -F',' '{types[$4]++} END {for(t in types) printf "%s: %d sessions\n", t, types[t]}' | sort -t: -k2 -rn)
\`\`\`

## Active Improvement Targets

- [ ] Run 10+ sessions per week
- [ ] Achieve 90%+ success rate
- [ ] Use 5+ parallel agents
- [ ] Try all 6 thread types
- [ ] Complete an L-thread (4+ hours)

---

*Dashboard auto-refreshes on metrics-tracker.sh calls*
EOF

  echo "Dashboard generated: $DASHBOARD_FILE"
}

#===============================================================================
# COMMAND LINE INTERFACE
#===============================================================================

show_help() {
  cat << EOF
Usage: metrics-tracker.sh <command> [args]

Thread performance metrics tracker for the Kiro Orchestrator.

COMMANDS:
  init                      Initialize metrics files
  start <type> [desc]       Start a session (base, p-thread, c-thread, f-thread, b-thread, l-thread)
  end <type> <tools> <ok>   End session with stats (tools=count, ok=1/0)
  log <metric> <value> [type] [tags]  Log a custom metric
  
THREAD-SPECIFIC LOGGING:
  parallel <count>          Log parallel agent count (P-thread)
  fusion <count> <mode> <conf>  Log fusion result (F-thread)
  phase <name> <status>     Log chain phase (C-thread)
  composition <type> <children>  Log B-thread composition
  autonomy <iters> <hours> <checks>  Log L-thread autonomy
  
REPORTING:
  report                    Generate detailed metrics report
  dashboard                 Generate metrics dashboard
  stats [period]            Show statistics (all, today, week, month)
  trends                    Show trend data

EXAMPLES:
  # Start and end a P-thread session
  SESSION=\$(./metrics-tracker.sh start p-thread "Code review")
  ./metrics-tracker.sh parallel 5
  ./metrics-tracker.sh end p-thread 150 1
  
  # Generate reports
  ./metrics-tracker.sh report
  ./metrics-tracker.sh dashboard
  
  # View statistics
  ./metrics-tracker.sh stats week

EOF
}

case "${1:-help}" in
  init)
    init_metrics
    ;;
  start)
    init_metrics
    start_session "${2:-base}" "${3:-}"
    ;;
  end)
    end_session "${2:-base}" "${3:-0}" "${4:-1}"
    ;;
  log)
    log_metric "$2" "$3" "${4:-base}" "$SESSION_ID" "${5:-}"
    ;;
  parallel)
    log_parallel "$2"
    ;;
  fusion)
    log_fusion "$2" "$3" "$4"
    ;;
  phase)
    log_chain_phase "$2" "$3"
    ;;
  composition)
    log_composition "$2" "$3"
    ;;
  autonomy)
    log_autonomy "$2" "$3" "$4"
    ;;
  report)
    generate_report
    ;;
  dashboard)
    generate_dashboard
    ;;
  stats)
    calculate_stats "${2:-all}"
    ;;
  trends)
    record_trend
    echo "Daily Trends:"
    cat "$TRENDS_FILE"
    ;;
  help|--help|-h|*)
    show_help
    ;;
esac
