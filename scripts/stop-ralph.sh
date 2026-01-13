#!/bin/bash
"""
Ralph Loop Multi-Agent System Stop Script

This script gracefully stops all Ralph Loop processes.
"""

echo "🛑 Stopping Ralph Loop Multi-Agent System"
echo "========================================="

# Stop coordinator if running
if [ -f ".coordinator.pid" ]; then
    COORDINATOR_PID=$(cat .coordinator.pid)
    echo "🔄 Stopping coordinator (PID: $COORDINATOR_PID)..."
    kill -TERM $COORDINATOR_PID 2>/dev/null || echo "   Coordinator already stopped"
    rm -f .coordinator.pid
fi

# Stop monitor if running
if [ -f ".monitor.pid" ]; then
    MONITOR_PID=$(cat .monitor.pid)
    echo "📊 Stopping progress monitor (PID: $MONITOR_PID)..."
    kill -TERM $MONITOR_PID 2>/dev/null || echo "   Monitor already stopped"
    rm -f .monitor.pid
fi

# Clean up any remaining processes
echo "🧹 Cleaning up any remaining processes..."
pkill -f "ralph-runner.py" 2>/dev/null || true
pkill -f "progress-tracker.py monitor" 2>/dev/null || true

# Remove lock files
rm -f .progress.lock

echo "✅ Ralph Loop System stopped successfully"
echo ""
echo "📋 Final Status:"
python3 progress-tracker.py