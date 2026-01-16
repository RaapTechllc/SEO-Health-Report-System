#!/bin/bash
# session-manager.sh - Track agent sessions with audit trail
set -e

STATE_DIR=".kiro/state/sessions"
mkdir -p "$STATE_DIR"

start_session() {
  local agent=$1 task="${2:-Unspecified task}"
  local ts=$(date +%s) file="$STATE_DIR/$agent-$ts.json"
  cat > "$file" << EOF
{"session_id":"$agent-$ts","agent":"$agent","task":"$task","started_at":"$(date -Iseconds)","status":"running","iterations":0,"errors":[]}
EOF
  ln -sf "$file" "$STATE_DIR/$agent-current.json"
  echo "$agent-$ts"
}

update_session() {
  local agent=$1 field=$2 value=$3
  local file="$STATE_DIR/$agent-current.json"
  [ -f "$file" ] || return 1
  local tmp=$(mktemp)
  jq ".$field = $value" "$file" > "$tmp" && mv "$tmp" "$file"
}

end_session() {
  local agent=$1 status=${2:-complete}
  local file="$STATE_DIR/$agent-current.json"
  [ -f "$file" ] || return 1
  local tmp=$(mktemp)
  jq ".status=\"$status\" | .ended_at=\"$(date -Iseconds)\"" "$file" > "$tmp" && mv "$tmp" "$file"
  rm -f "$STATE_DIR/$agent-current.json"
}

list_sessions() {
  local filter=${1:-all}
  for f in "$STATE_DIR"/*.json; do
    [ -f "$f" ] || continue
    [[ "$f" == *-current.json ]] && continue
    local status=$(jq -r '.status' "$f")
    case $filter in
      all) jq -c '{id:.session_id,agent:.agent,status:.status,started:.started_at}' "$f" ;;
      active) [ "$status" = "running" ] && jq -c '{id:.session_id,agent:.agent}' "$f" ;;
      *) [ "$status" = "$filter" ] && jq -c '{id:.session_id,agent:.agent}' "$f" ;;
    esac
  done
}

case "${1:-help}" in
  start) start_session "$2" "$3" ;;
  update) update_session "$2" "$3" "$4" ;;
  end) end_session "$2" "$3" ;;
  list) list_sessions "$2" ;;
  *) echo "Usage: session-manager.sh start|update|end|list <agent> [args]" ;;
esac
