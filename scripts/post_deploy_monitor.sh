#!/bin/bash
# post_deploy_monitor.sh - Post-deployment monitoring and alerting
# Usage:
#   ./post_deploy_monitor.sh check <url>           - Run health check once
#   ./post_deploy_monitor.sh monitor <url> [mins]  - Monitor for N minutes (default: 5)
#   ./post_deploy_monitor.sh metrics <url>         - Check error rates from metrics
#   ./post_deploy_monitor.sh full <url>            - Full post-deploy check suite
#
# Environment Variables:
#   SLACK_WEBHOOK_URL    - Slack webhook for notifications
#   DISCORD_WEBHOOK_URL  - Discord webhook for notifications
#   ALERT_EMAIL          - Email for alerts (requires configured mail)
#   MONITORING_INTERVAL  - Seconds between checks (default: 30)
#   ERROR_RATE_THRESHOLD - Max error rate % before alert (default: 5)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
MONITORING_INTERVAL="${MONITORING_INTERVAL:-30}"
ERROR_RATE_THRESHOLD="${ERROR_RATE_THRESHOLD:-5}"
MAX_RESPONSE_TIME="${MAX_RESPONSE_TIME:-5000}"  # ms
RETRY_ATTEMPTS="${RETRY_ATTEMPTS:-3}"
RETRY_DELAY="${RETRY_DELAY:-5}"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_header() {
    echo ""
    echo -e "${BLUE}=========================================="
    echo -e " $1"
    echo -e "==========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

print_info() {
    echo -e "${BLUE}→ $1${NC}"
}

# Send notification to Slack
send_slack_alert() {
    local message="$1"
    local severity="${2:-warning}"
    
    if [ -z "$SLACK_WEBHOOK_URL" ]; then
        return 0
    fi
    
    local color="#ffcc00"  # yellow - warning
    if [ "$severity" = "critical" ]; then
        color="#ff0000"  # red
    elif [ "$severity" = "success" ]; then
        color="#00ff00"  # green
    fi
    
    local payload=$(cat <<EOF
{
    "attachments": [{
        "color": "$color",
        "title": "SEO Health Report - Deployment Alert",
        "text": "$message",
        "fields": [
            {"title": "Environment", "value": "${APP_ENV:-unknown}", "short": true},
            {"title": "Timestamp", "value": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "short": true}
        ],
        "footer": "Post-Deploy Monitor"
    }]
}
EOF
)
    
    curl -s -X POST -H 'Content-type: application/json' \
        --data "$payload" "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 || true
}

# Send notification to Discord
send_discord_alert() {
    local message="$1"
    local severity="${2:-warning}"
    
    if [ -z "$DISCORD_WEBHOOK_URL" ]; then
        return 0
    fi
    
    local color=16776960  # yellow
    if [ "$severity" = "critical" ]; then
        color=16711680  # red
    elif [ "$severity" = "success" ]; then
        color=65280  # green
    fi
    
    local payload=$(cat <<EOF
{
    "embeds": [{
        "title": "SEO Health Report - Deployment Alert",
        "description": "$message",
        "color": $color,
        "fields": [
            {"name": "Environment", "value": "${APP_ENV:-unknown}", "inline": true},
            {"name": "Timestamp", "value": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "inline": true}
        ],
        "footer": {"text": "Post-Deploy Monitor"}
    }]
}
EOF
)
    
    curl -s -X POST -H 'Content-type: application/json' \
        --data "$payload" "$DISCORD_WEBHOOK_URL" > /dev/null 2>&1 || true
}

# Send alert to all configured channels
send_alert() {
    local message="$1"
    local severity="${2:-warning}"
    
    print_info "Sending alert: $message"
    
    send_slack_alert "$message" "$severity"
    send_discord_alert "$message" "$severity"
    
    # Email alert (if configured)
    if [ -n "$ALERT_EMAIL" ] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "Deployment Alert: $severity" "$ALERT_EMAIL" 2>/dev/null || true
    fi
}

# Health check with retries
check_health() {
    local url="$1"
    local attempt=1
    
    while [ $attempt -le $RETRY_ATTEMPTS ]; do
        local start_time=$(date +%s%N)
        local response=$(curl -s -w "\n%{http_code}\n%{time_total}" -o /tmp/health_response.txt "$url/health" 2>&1)
        local end_time=$(date +%s%N)
        
        local http_code=$(echo "$response" | tail -2 | head -1)
        local response_time=$(echo "$response" | tail -1)
        local response_time_ms=$(echo "$response_time * 1000" | bc 2>/dev/null || echo "0")
        
        if [ "$http_code" = "200" ]; then
            local body=$(cat /tmp/health_response.txt 2>/dev/null)
            local status=$(echo "$body" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            
            if [ "$status" = "healthy" ]; then
                echo "$response_time_ms"
                return 0
            fi
        fi
        
        if [ $attempt -lt $RETRY_ATTEMPTS ]; then
            sleep $RETRY_DELAY
        fi
        ((attempt++))
    done
    
    return 1
}

# Check API root endpoint
check_api_root() {
    local url="$1"
    
    local response=$(curl -s -w "\n%{http_code}" "$url/" 2>&1)
    local http_code=$(echo "$response" | tail -1)
    
    if [ "$http_code" = "200" ]; then
        return 0
    fi
    return 1
}

# Get metrics and parse error rate
check_error_rate() {
    local url="$1"
    
    local metrics_response=$(curl -s "$url/metrics" 2>&1)
    
    if [ -z "$metrics_response" ]; then
        print_warning "Could not fetch metrics"
        return 1
    fi
    
    # Parse HTTP request counts
    local total_requests=0
    local error_requests=0
    
    # Count total requests
    while IFS= read -r line; do
        if [[ "$line" =~ http_requests_total\{.*status=\"([0-9]+)\".*\}\ ([0-9.]+) ]]; then
            local status="${BASH_REMATCH[1]}"
            local count="${BASH_REMATCH[2]}"
            count=${count%.*}  # Remove decimal
            
            total_requests=$((total_requests + count))
            
            # Count 5xx errors
            if [[ "$status" =~ ^5[0-9][0-9]$ ]]; then
                error_requests=$((error_requests + count))
            fi
        fi
    done <<< "$metrics_response"
    
    if [ $total_requests -eq 0 ]; then
        echo "0.00|0|0"
        return 0
    fi
    
    local error_rate=$(echo "scale=2; $error_requests * 100 / $total_requests" | bc 2>/dev/null || echo "0")
    echo "${error_rate}|${error_requests}|${total_requests}"
    return 0
}

# Get active audits count
check_active_audits() {
    local url="$1"
    
    local metrics_response=$(curl -s "$url/metrics" 2>&1)
    
    local active=$(echo "$metrics_response" | grep -E "^active_audits " | awk '{print $2}')
    echo "${active:-0}"
}

# Run single health check
run_check() {
    local url="$1"
    
    print_header "Health Check: $url"
    
    local passed=0
    local failed=0
    
    # Check health endpoint
    echo -n "  Health endpoint... "
    local response_time=$(check_health "$url")
    if [ $? -eq 0 ]; then
        print_success "OK (${response_time}ms)"
        ((passed++))
        
        # Check response time threshold
        if [ "${response_time%.*}" -gt "$MAX_RESPONSE_TIME" ]; then
            print_warning "Response time ${response_time}ms exceeds threshold ${MAX_RESPONSE_TIME}ms"
        fi
    else
        print_error "FAILED"
        ((failed++))
    fi
    
    # Check API root
    echo -n "  API root... "
    if check_api_root "$url"; then
        print_success "OK"
        ((passed++))
    else
        print_error "FAILED"
        ((failed++))
    fi
    
    # Check error rate
    echo -n "  Error rate... "
    local error_info=$(check_error_rate "$url")
    if [ $? -eq 0 ]; then
        local error_rate=$(echo "$error_info" | cut -d'|' -f1)
        local error_count=$(echo "$error_info" | cut -d'|' -f2)
        local total_count=$(echo "$error_info" | cut -d'|' -f3)
        
        if (( $(echo "$error_rate > $ERROR_RATE_THRESHOLD" | bc -l 2>/dev/null || echo 0) )); then
            print_error "${error_rate}% (${error_count}/${total_count} requests) - EXCEEDS THRESHOLD"
            ((failed++))
        else
            print_success "${error_rate}% (${error_count}/${total_count} requests)"
            ((passed++))
        fi
    else
        print_warning "Could not check"
    fi
    
    # Check active audits
    echo -n "  Active audits... "
    local active_audits=$(check_active_audits "$url")
    print_info "$active_audits running"
    
    # Summary
    print_header "Summary"
    echo -e "  Passed: ${GREEN}${passed}${NC}"
    echo -e "  Failed: ${RED}${failed}${NC}"
    
    if [ $failed -gt 0 ]; then
        return 1
    fi
    return 0
}

# Monitor for specified duration
run_monitor() {
    local url="$1"
    local duration_mins="${2:-5}"
    local duration_secs=$((duration_mins * 60))
    local end_time=$(($(date +%s) + duration_secs))
    local check_count=0
    local fail_count=0
    
    print_header "Monitoring: $url for ${duration_mins} minutes"
    print_info "Check interval: ${MONITORING_INTERVAL}s"
    print_info "Error threshold: ${ERROR_RATE_THRESHOLD}%"
    
    while [ $(date +%s) -lt $end_time ]; do
        ((check_count++))
        local timestamp=$(date +%H:%M:%S)
        
        echo -n "[$timestamp] Check #$check_count: "
        
        local response_time=$(check_health "$url")
        if [ $? -eq 0 ]; then
            # Check error rate
            local error_info=$(check_error_rate "$url")
            local error_rate=$(echo "$error_info" | cut -d'|' -f1)
            
            if (( $(echo "$error_rate > $ERROR_RATE_THRESHOLD" | bc -l 2>/dev/null || echo 0) )); then
                print_warning "Healthy but error rate high: ${error_rate}%"
                ((fail_count++))
                
                if [ $fail_count -ge 3 ]; then
                    send_alert "Elevated error rate detected: ${error_rate}% (threshold: ${ERROR_RATE_THRESHOLD}%)" "warning"
                fi
            else
                print_success "Healthy (${response_time}ms, ${error_rate}% errors)"
                fail_count=0  # Reset consecutive failures
            fi
        else
            print_error "UNHEALTHY"
            ((fail_count++))
            
            if [ $fail_count -ge 2 ]; then
                send_alert "Health check failed $fail_count consecutive times" "critical"
            fi
        fi
        
        # Sleep until next check
        local remaining=$((end_time - $(date +%s)))
        if [ $remaining -gt $MONITORING_INTERVAL ]; then
            sleep $MONITORING_INTERVAL
        elif [ $remaining -gt 0 ]; then
            sleep $remaining
        fi
    done
    
    print_header "Monitoring Complete"
    print_info "Total checks: $check_count"
    
    if [ $fail_count -gt 0 ]; then
        print_warning "Ended with $fail_count consecutive failures"
        return 1
    fi
    
    print_success "All checks passed"
    send_alert "Post-deployment monitoring completed successfully" "success"
    return 0
}

# Check metrics endpoint in detail
run_metrics_check() {
    local url="$1"
    
    print_header "Metrics Analysis: $url"
    
    local metrics_response=$(curl -s "$url/metrics" 2>&1)
    
    if [ -z "$metrics_response" ]; then
        print_error "Could not fetch metrics from $url/metrics"
        return 1
    fi
    
    print_success "Metrics endpoint accessible"
    echo ""
    
    # Parse and display key metrics
    print_info "HTTP Request Summary:"
    echo "$metrics_response" | grep -E "^http_requests_total" | while read -r line; do
        echo "    $line"
    done
    
    echo ""
    print_info "Audit Metrics:"
    echo "$metrics_response" | grep -E "^(active_audits|audit_total)" | while read -r line; do
        echo "    $line"
    done
    
    echo ""
    print_info "Webhook Metrics:"
    echo "$metrics_response" | grep -E "^webhook_deliveries_total" | while read -r line; do
        echo "    $line"
    done
    
    # Calculate error rate
    local error_info=$(check_error_rate "$url")
    local error_rate=$(echo "$error_info" | cut -d'|' -f1)
    local error_count=$(echo "$error_info" | cut -d'|' -f2)
    local total_count=$(echo "$error_info" | cut -d'|' -f3)
    
    echo ""
    print_header "Error Rate Analysis"
    print_info "Total requests: $total_count"
    print_info "Error requests (5xx): $error_count"
    
    if (( $(echo "$error_rate > $ERROR_RATE_THRESHOLD" | bc -l 2>/dev/null || echo 0) )); then
        print_error "Error rate: ${error_rate}% - EXCEEDS THRESHOLD (${ERROR_RATE_THRESHOLD}%)"
        return 1
    else
        print_success "Error rate: ${error_rate}% - Within threshold"
    fi
    
    return 0
}

# Full post-deployment check
run_full_check() {
    local url="$1"
    
    print_header "Full Post-Deployment Check"
    print_info "Target: $url"
    print_info "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    
    local passed=0
    local failed=0
    
    # 1. Health check
    echo ""
    echo "=== Phase 1: Health Check ==="
    if run_check "$url"; then
        ((passed++))
    else
        ((failed++))
        send_alert "Post-deployment health check failed for $url" "critical"
    fi
    
    # 2. Metrics check
    echo ""
    echo "=== Phase 2: Metrics Analysis ==="
    if run_metrics_check "$url"; then
        ((passed++))
    else
        ((failed++))
        send_alert "Post-deployment metrics check shows elevated error rate" "warning"
    fi
    
    # 3. Brief monitoring (2 minutes)
    echo ""
    echo "=== Phase 3: Brief Monitoring (2 min) ==="
    if run_monitor "$url" 2; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # Summary
    print_header "Full Check Summary"
    echo -e "  Phases passed: ${GREEN}${passed}${NC}/3"
    echo -e "  Phases failed: ${RED}${failed}${NC}/3"
    echo -e "  Completed: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    
    if [ $failed -gt 0 ]; then
        print_error "Post-deployment check FAILED"
        return 1
    fi
    
    print_success "Post-deployment check PASSED"
    return 0
}

# Main
case "${1:-help}" in
    check)
        if [ -z "$2" ]; then
            print_error "URL required"
            echo "Usage: $0 check <url>"
            exit 1
        fi
        run_check "$2"
        ;;
    monitor)
        if [ -z "$2" ]; then
            print_error "URL required"
            echo "Usage: $0 monitor <url> [minutes]"
            exit 1
        fi
        run_monitor "$2" "${3:-5}"
        ;;
    metrics)
        if [ -z "$2" ]; then
            print_error "URL required"
            echo "Usage: $0 metrics <url>"
            exit 1
        fi
        run_metrics_check "$2"
        ;;
    full)
        if [ -z "$2" ]; then
            print_error "URL required"
            echo "Usage: $0 full <url>"
            exit 1
        fi
        run_full_check "$2"
        ;;
    help|--help|-h)
        echo "Post-Deployment Monitoring Script"
        echo ""
        echo "Usage: $0 <command> <url> [options]"
        echo ""
        echo "Commands:"
        echo "  check <url>              Run single health check"
        echo "  monitor <url> [mins]     Monitor for N minutes (default: 5)"
        echo "  metrics <url>            Analyze metrics endpoint"
        echo "  full <url>               Full post-deployment check suite"
        echo ""
        echo "Environment Variables:"
        echo "  SLACK_WEBHOOK_URL        Slack webhook for notifications"
        echo "  DISCORD_WEBHOOK_URL      Discord webhook for notifications"
        echo "  ALERT_EMAIL              Email for alerts"
        echo "  MONITORING_INTERVAL      Seconds between checks (default: 30)"
        echo "  ERROR_RATE_THRESHOLD     Max error rate % (default: 5)"
        echo "  MAX_RESPONSE_TIME        Max response time in ms (default: 5000)"
        echo ""
        echo "Examples:"
        echo "  $0 check https://api.example.com"
        echo "  $0 monitor https://api.example.com 10"
        echo "  $0 full https://api.example.com"
        echo ""
        echo "  SLACK_WEBHOOK_URL=https://hooks.slack.com/... $0 full https://api.example.com"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Run '$0 help' for usage"
        exit 1
        ;;
esac
