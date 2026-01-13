#!/bin/bash
"""
Ralph Loop Multi-Agent System Startup Script

This script starts all agents in parallel Ralph loops and monitors progress.
"""

set -e

echo "🚀 Starting Ralph Loop Multi-Agent System"
echo "=========================================="

# Check if required files exist
if [ ! -f "PLAN.md" ]; then
    echo "❌ PLAN.md not found. Please ensure the plan file exists."
    exit 1
fi

if [ ! -f "PROGRESS.md" ]; then
    echo "❌ PROGRESS.md not found. Please ensure the progress file exists."
    exit 1
fi

# Check if agent configurations exist
AGENT_DIR=".kiro/agents"
RALPH_AGENTS=(
    "devops-automator-ralph.json"
    "agent-creator-ralph.json"
    "code-surgeon-ralph.json"
    "db-wizard-ralph.json"
    "frontend-designer-ralph.json"
    "test-architect-ralph.json"
    "doc-smith-ralph.json"
)

echo "🔍 Checking agent configurations..."
for agent in "${RALPH_AGENTS[@]}"; do
    if [ ! -f "$AGENT_DIR/$agent" ]; then
        echo "❌ Agent configuration not found: $agent"
        exit 1
    fi
    echo "✅ Found: $agent"
done

# Create logs directory
mkdir -p logs

echo ""
echo "📋 Initial System Status:"
python3 progress-tracker.py

echo ""
echo "🎯 Starting Ralph Loop Coordinator..."

# Start the main coordinator in background
python3 ralph-runner.py > logs/coordinator.log 2>&1 &
COORDINATOR_PID=$!

echo "📊 Coordinator started (PID: $COORDINATOR_PID)"
echo "📈 Starting progress monitor..."

# Start progress monitor
python3 progress-tracker.py monitor &
MONITOR_PID=$!

echo "🔄 Progress monitor started (PID: $MONITOR_PID)"
echo ""
echo "🎮 Ralph Loop System is now running!"
echo ""
echo "Commands:"
echo "  - View logs: tail -f logs/coordinator.log"
echo "  - Check status: python3 progress-tracker.py"
echo "  - Stop system: ./stop-ralph.sh"
echo ""
echo "The system will run until all tasks are complete or you stop it."
echo "Watch the progress monitor for real-time updates."

# Save PIDs for cleanup
echo "$COORDINATOR_PID" > .coordinator.pid
echo "$MONITOR_PID" > .monitor.pid

# Wait for coordinator to finish or user interrupt
wait $COORDINATOR_PID

echo ""
echo "🏁 Ralph Loop Coordinator finished"
echo "🛑 Stopping progress monitor..."

kill $MONITOR_PID 2>/dev/null || true
rm -f .coordinator.pid .monitor.pid

echo "✅ Ralph Loop System shutdown complete"