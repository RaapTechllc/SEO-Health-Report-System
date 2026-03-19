#!/bin/bash
# health-monitor.sh - Agent health monitoring with stall detection
set -e

STATE_DIR=".kiro/state/health"
AGENTS_DIR="agents"
STALL_THRESHOLD=${STALL_THRESHOLD:-15}  # minutes

mkdir -p "$STATE_DIR"

get_status() {
  local agent=$1 output="$AGENTS_DIR/$agent/output.log"
  
  [ ! -f "$output" ] && echo "crashed" && return
  grep -q "<promise>DONE</promise>" "$output" 2>/dev/null && echo "complete" && return
  grep -qE "FATAL|PANIC|Traceback|Error:" "$output" 2>/dev/null && echo "failed" && return
  
  local mod=$(stat -c %Y "$output" 2>/dev/null || stat -f %m "$output" 2>/dev/null)
  local age=$(( ($(date +%s) - mod) / 60 ))
  [ "$age" -gt "$STALL_THRESHOLD" ] && echo "stalled" || echo "healthy"
}

check_agent() {
  local agent=$1 output="$AGENTS_DIR/$agent/output.log"
  local status=$(get_status "$agent")
  local last_line=$(tail -1 "$output" 2>/dev/null | cut -c1-60)
  local mod=$(stat -c %Y "$output" 2>/dev/null || stat -f %m "$output" 2>/dev/null || echo 0)
  local age=$(( ($(date +%s) - mod) / 60 ))
  local iter=$(grep -c "iteration\|Iteration" "$output" 2>/dev/null || echo 0)
  local existing="$STATE_DIR/$agent.json"
  local restarts=0
  [ -f "$existing" ] && restarts=$(grep -o '"restart_count":[0-9]*' "$existing" | cut -d: -f2 || echo 0)
  
  cat > "$STATE_DIR/$agent.json" << EOF
{"agent":"$agent","status":"$status","last_heartbeat":"$(date -Iseconds)","stall_minutes":$age,"iterations":$iter,"restart_count":$restarts,"last_output":"$last_line"}
EOF
}

case "${1:-check}" in
  check)
    [ -d "$AGENTS_DIR" ] && for d in "$AGENTS_DIR"/*/; do
      [ -d "$d" ] && check_agent "$(basename "$d")"
    done
    ;;
  status)
    for f in "$STATE_DIR"/*.json; do
      [ -f "$f" ] && cat "$f" && echo
    done
    ;;
  watch)
    while true; do $0 check; sleep "${2:-30}"; done
    ;;
  *)
    echo "Usage: health-monitor.sh [check|status|watch [interval]]"
    ;;
esac
