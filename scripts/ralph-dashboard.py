#!/usr/bin/env python3
"""
Ralph Loop Dashboard - Real-time monitoring web interface

Run with: python ralph-dashboard.py
Then open: http://localhost:5050
"""

import json
import os
import re
import subprocess
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Track the Ralph Loop process
ralph_process = None

# Configuration
STATE_FILE = Path(".ralph-state.json")
PLAN_FILE = Path("PLAN.md")
LOG_FILE = Path("ralph-loop.log")
COORDINATOR_PID_FILE = Path(".coordinator.pid")
MONITOR_PID_FILE = Path(".monitor.pid")

AGENTS = [
    "devops-automator",
    "agent-creator",
    "db-wizard",
    "code-surgeon",
    "frontend-designer",
    "test-architect",
    "doc-smith"
]

AGENT_COLORS = {
    "devops-automator": "#3b82f6",
    "agent-creator": "#8b5cf6",
    "db-wizard": "#06b6d4",
    "code-surgeon": "#ef4444",
    "frontend-designer": "#f59e0b",
    "test-architect": "#10b981",
    "doc-smith": "#ec4899"
}


def load_state():
    """Load state from JSON file"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"tasks": {}, "promises": []}


def parse_tasks_from_plan():
    """Parse tasks from PLAN.md"""
    if not PLAN_FILE.exists():
        return []
    
    tasks = []
    with open(PLAN_FILE) as f:
        content = f.read()
    
    lines = content.split('\n')
    current_task = None
    
    for line in lines:
        if line.startswith('#### Task '):
            if current_task:
                tasks.append(current_task)
            
            match = re.match(r'#### Task (\d+\.\d+):\s*(.+)', line)
            if match:
                task_id = match.group(1)
                title = match.group(2)
            else:
                task_id = line.split(':')[0].replace('#### Task ', '').strip()
                title = line.split(':', 1)[1].strip() if ':' in line else ''
            
            current_task = {
                'id': task_id,
                'title': title,
                'agent': None,
                'phase': int(task_id.split('.')[0]) if '.' in task_id else 1
            }
        elif current_task and line.startswith('- **Agent:**'):
            current_task['agent'] = line.replace('- **Agent:**', '').strip()
    
    if current_task:
        tasks.append(current_task)
    
    return tasks


def get_recent_logs(lines=20):
    """Get recent log entries"""
    if not LOG_FILE.exists():
        return []
    
    try:
        with open(LOG_FILE) as f:
            all_lines = f.readlines()
        return all_lines[-lines:]
    except IOError:
        return []


def get_dashboard_data():
    """Get all data for dashboard"""
    state = load_state()
    tasks = parse_tasks_from_plan()
    
    # Enrich tasks with status
    for task in tasks:
        task_data = state.get("tasks", {}).get(task['id'], {})
        task['status'] = task_data.get("status", "PENDING")
        task['updated_at'] = task_data.get("updated_at")
        task['color'] = AGENT_COLORS.get(task['agent'], '#6b7280')
    
    # Calculate stats
    total = len(tasks)
    done = sum(1 for t in tasks if t['status'] == 'DONE')
    in_progress = sum(1 for t in tasks if t['status'] == 'IN_PROGRESS')
    pending = total - done - in_progress
    
    # Phase progress
    phases = {}
    for task in tasks:
        phase = task['phase']
        if phase not in phases:
            phases[phase] = {'total': 0, 'done': 0}
        phases[phase]['total'] += 1
        if task['status'] == 'DONE':
            phases[phase]['done'] += 1
    
    # Agent status
    agents_data = []
    for agent in AGENTS:
        agent_tasks = [t for t in tasks if t['agent'] == agent]
        agent_done = sum(1 for t in agent_tasks if t['status'] == 'DONE')
        agent_total = len(agent_tasks)
        
        # Get last activity
        last_activity = None
        for t in agent_tasks:
            if t.get('updated_at'):
                try:
                    ts = datetime.fromisoformat(t['updated_at'])
                    if last_activity is None or ts > last_activity:
                        last_activity = ts
                except ValueError:
                    pass
        
        is_active = last_activity and (datetime.now() - last_activity) < timedelta(minutes=5)
        has_promise = agent in state.get("promises", [])
        
        agents_data.append({
            'name': agent,
            'color': AGENT_COLORS.get(agent, '#6b7280'),
            'done': agent_done,
            'total': agent_total,
            'progress': (agent_done / agent_total * 100) if agent_total > 0 else 0,
            'status': 'complete' if has_promise else ('active' if is_active else 'idle'),
            'last_activity': last_activity.strftime('%H:%M:%S') if last_activity else 'Never'
        })
    
    return {
        'total': total,
        'done': done,
        'in_progress': in_progress,
        'pending': pending,
        'progress_percent': (done / total * 100) if total > 0 else 0,
        'phases': phases,
        'agents': agents_data,
        'tasks': tasks,
        'promises': state.get("promises", []),
        'logs': get_recent_logs(15),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'is_running': is_ralph_running(),
        'all_done': done == total and total > 0
    }


DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ralph Loop Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .pulse-dot { animation: pulse-dot 1.5s ease-in-out infinite; }
        .spin { animation: spin 1s linear infinite; }
        .toast { transform: translateX(100%); transition: transform 0.3s ease; }
        .toast.show { transform: translateX(0); }
    </style>
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <!-- Toast Notification -->
    <div id="toast" class="toast fixed top-4 right-4 bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-lg z-50 max-w-sm">
        <div id="toast-message" class="text-sm"></div>
    </div>

    <div class="container mx-auto px-4 py-8">
        <!-- Header with Controls -->
        <div class="flex items-center justify-between mb-8 flex-wrap gap-4">
            <div>
                <h1 class="text-3xl font-bold flex items-center gap-3">
                    Ralph Loop Dashboard
                    <span id="status-indicator" class="w-3 h-3 rounded-full {% if data.is_running %}bg-green-500 pulse-dot{% else %}bg-gray-500{% endif %}"></span>
                </h1>
                <p class="text-gray-400">Multi-Agent System Monitor</p>
            </div>
            <div class="flex items-center gap-4 flex-wrap">
                <!-- Control Buttons -->
                <div class="flex gap-2">
                    <button id="btn-start" onclick="startRalph()" 
                            class="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium transition flex items-center gap-2 {% if data.is_running %}opacity-50 cursor-not-allowed{% endif %}"
                            {% if data.is_running %}disabled{% endif %}>
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"/>
                        </svg>
                        Start
                    </button>
                    <button id="btn-stop" onclick="stopRalph()" 
                            class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium transition flex items-center gap-2 {% if not data.is_running %}opacity-50 cursor-not-allowed{% endif %}"
                            {% if not data.is_running %}disabled{% endif %}>
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M5.25 3A2.25 2.25 0 003 5.25v9.5A2.25 2.25 0 005.25 17h9.5A2.25 2.25 0 0017 14.75v-9.5A2.25 2.25 0 0014.75 3h-9.5z"/>
                        </svg>
                        Stop
                    </button>
                </div>
                <!-- More Actions Dropdown -->
                <div class="relative">
                    <button onclick="toggleDropdown()" class="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/>
                        </svg>
                    </button>
                    <div id="dropdown" class="hidden absolute right-0 mt-2 w-48 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-40">
                        <button onclick="resetTasks()" class="w-full px-4 py-2 text-left hover:bg-gray-700 rounded-t-lg flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                            </svg>
                            Reset All Tasks
                        </button>
                        <button onclick="clearLogs()" class="w-full px-4 py-2 text-left hover:bg-gray-700 flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                            Clear Logs
                        </button>
                        <button onclick="toggleAutoRefresh()" class="w-full px-4 py-2 text-left hover:bg-gray-700 rounded-b-lg flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            </svg>
                            <span id="auto-refresh-text">Pause Auto-Refresh</span>
                        </button>
                    </div>
                </div>
                <!-- Timestamp -->
                <div class="text-right">
                    <div class="text-sm text-gray-400">Last updated</div>
                    <div id="timestamp" class="text-lg font-mono">{{ data.timestamp }}</div>
                </div>
            </div>
        </div>
        
        <!-- Status Banner -->
        {% if data.all_done %}
        <div class="bg-green-900/50 border border-green-500 rounded-lg p-4 mb-8 flex items-center gap-3">
            <svg class="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span class="text-green-400 font-medium">All tasks completed! Ralph Loop has finished.</span>
        </div>
        {% elif data.is_running %}
        <div class="bg-blue-900/50 border border-blue-500 rounded-lg p-4 mb-8 flex items-center gap-3">
            <svg class="w-6 h-6 text-blue-400 spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            <span class="text-blue-400 font-medium">Ralph Loop is running...</span>
        </div>
        {% endif %}
        
        <!-- Progress Overview -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-gray-800 rounded-lg p-6">
                <div class="text-4xl font-bold text-green-400">{{ data.done }}</div>
                <div class="text-gray-400">Completed</div>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <div class="text-4xl font-bold text-yellow-400">{{ data.in_progress }}</div>
                <div class="text-gray-400">In Progress</div>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <div class="text-4xl font-bold text-gray-400">{{ data.pending }}</div>
                <div class="text-gray-400">Pending</div>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <div class="text-4xl font-bold text-blue-400">{{ "%.1f"|format(data.progress_percent) }}%</div>
                <div class="text-gray-400">Overall Progress</div>
            </div>
        </div>
        
        <!-- Main Progress Bar -->
        <div class="bg-gray-800 rounded-lg p-6 mb-8">
            <div class="flex justify-between mb-2">
                <span class="font-semibold">Overall Progress</span>
                <span>{{ data.done }}/{{ data.total }} tasks</span>
            </div>
            <div class="w-full bg-gray-700 rounded-full h-4">
                <div class="bg-green-500 h-4 rounded-full transition-all duration-500" 
                     style="width: {{ data.progress_percent }}%"></div>
            </div>
        </div>
        
        <!-- Two Column Layout -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <!-- Agents -->
            <div class="bg-gray-800 rounded-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Agents</h2>
                <div class="space-y-4">
                    {% for agent in data.agents %}
                    <div class="flex items-center gap-4">
                        <div class="w-3 h-3 rounded-full {% if agent.status == 'active' %}pulse-dot{% endif %}"
                             style="background-color: {{ agent.color }}"></div>
                        <div class="flex-1">
                            <div class="flex justify-between">
                                <span class="font-medium">{{ agent.name }}</span>
                                <span class="text-sm">
                                    {% if agent.status == 'complete' %}
                                    <span class="text-green-400">[DONE]</span>
                                    {% elif agent.status == 'active' %}
                                    <span class="text-yellow-400">[ACTIVE]</span>
                                    {% else %}
                                    <span class="text-gray-500">[IDLE]</span>
                                    {% endif %}
                                </span>
                            </div>
                            <div class="w-full bg-gray-700 rounded-full h-2 mt-1">
                                <div class="h-2 rounded-full transition-all duration-500"
                                     style="width: {{ agent.progress }}%; background-color: {{ agent.color }}"></div>
                            </div>
                            <div class="text-xs text-gray-500 mt-1">
                                {{ agent.done }}/{{ agent.total }} tasks | Last: {{ agent.last_activity }}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Phases -->
            <div class="bg-gray-800 rounded-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Phases</h2>
                <div class="space-y-4">
                    {% for phase, progress in data.phases.items()|sort %}
                    <div>
                        <div class="flex justify-between mb-1">
                            <span>Phase {{ phase }}</span>
                            <span class="{% if progress.done == progress.total %}text-green-400{% endif %}">
                                {{ progress.done }}/{{ progress.total }}
                            </span>
                        </div>
                        <div class="w-full bg-gray-700 rounded-full h-3">
                            <div class="bg-blue-500 h-3 rounded-full transition-all duration-500"
                                 style="width: {{ (progress.done / progress.total * 100) if progress.total > 0 else 0 }}%"></div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <!-- Promises Section -->
                {% if data.promises %}
                <div class="mt-6 pt-4 border-t border-gray-700">
                    <h3 class="text-lg font-semibold mb-3 flex items-center gap-2">
                        <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        Agent Promises
                    </h3>
                    <div class="flex flex-wrap gap-2">
                        {% for agent in data.promises %}
                        <span class="px-3 py-1 bg-green-900/50 text-green-400 rounded-full text-sm">{{ agent }}</span>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
            </div>
        </div>
        
        <!-- Task List -->
        <div class="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4">Tasks</h2>
            <div class="space-y-2">
                {% for task in data.tasks %}
                <div class="flex items-center gap-3 p-2 rounded {% if task.status == 'DONE' %}bg-green-900/30{% elif task.status == 'IN_PROGRESS' %}bg-yellow-900/30{% else %}bg-gray-700/30{% endif %}">
                    <div class="w-2 h-2 rounded-full" style="background-color: {{ task.color }}"></div>
                    <span class="font-mono text-sm w-10">{{ task.id }}</span>
                    <span class="flex-1">{{ task.title }}</span>
                    <span class="text-xs text-gray-500 hidden sm:inline">{{ task.agent }}</span>
                    <span class="text-xs px-2 py-1 rounded {% if task.status == 'DONE' %}bg-green-600{% elif task.status == 'IN_PROGRESS' %}bg-yellow-600{% else %}bg-gray-600{% endif %}">
                        {{ task.status }}
                    </span>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <!-- Logs -->
        <div class="bg-gray-800 rounded-lg p-6">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold">Recent Logs</h2>
                <button onclick="clearLogs()" class="text-sm text-gray-400 hover:text-white transition">Clear</button>
            </div>
            <div class="bg-black rounded p-4 font-mono text-xs overflow-x-auto max-h-64 overflow-y-auto">
                {% for log in data.logs %}
                <div class="text-gray-300 {% if 'ERROR' in log %}text-red-400{% elif 'WARNING' in log %}text-yellow-400{% elif 'SUCCESS' in log or 'DONE' in log %}text-green-400{% endif %}">{{ log }}</div>
                {% endfor %}
                {% if not data.logs %}
                <div class="text-gray-500">No logs yet...</div>
                {% endif %}
            </div>
        </div>
        
        <!-- Footer -->
        <div class="mt-8 text-center text-gray-500 text-sm">
            Ralph Loop Dashboard v1.0 | Auto-refresh: <span id="refresh-status">ON</span>
        </div>
    </div>
    
    <script>
        let autoRefresh = true;
        let refreshTimer = null;
        
        function showToast(message, isError = false) {
            const toast = document.getElementById('toast');
            const toastMsg = document.getElementById('toast-message');
            toastMsg.textContent = message;
            toast.className = 'toast fixed top-4 right-4 rounded-lg p-4 shadow-lg z-50 max-w-sm show ' + 
                (isError ? 'bg-red-900 border border-red-700' : 'bg-gray-800 border border-gray-700');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }
        
        function toggleDropdown() {
            document.getElementById('dropdown').classList.toggle('hidden');
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            const dropdown = document.getElementById('dropdown');
            if (!e.target.closest('.relative')) {
                dropdown.classList.add('hidden');
            }
        });
        
        async function startRalph() {
            try {
                const resp = await fetch('/api/start', { method: 'POST' });
                const data = await resp.json();
                showToast(data.message, !data.success);
                if (data.success) setTimeout(() => location.reload(), 1000);
            } catch (e) {
                showToast('Failed to start: ' + e.message, true);
            }
        }
        
        async function stopRalph() {
            try {
                const resp = await fetch('/api/stop', { method: 'POST' });
                const data = await resp.json();
                showToast(data.message, !data.success);
                if (data.success) setTimeout(() => location.reload(), 1000);
            } catch (e) {
                showToast('Failed to stop: ' + e.message, true);
            }
        }
        
        async function resetTasks() {
            if (!confirm('Reset all tasks to PENDING? This cannot be undone.')) return;
            try {
                const resp = await fetch('/api/reset', { method: 'POST' });
                const data = await resp.json();
                showToast(data.message, !data.success);
                document.getElementById('dropdown').classList.add('hidden');
                if (data.success) setTimeout(() => location.reload(), 1000);
            } catch (e) {
                showToast('Failed to reset: ' + e.message, true);
            }
        }
        
        async function clearLogs() {
            try {
                const resp = await fetch('/api/clear-logs', { method: 'POST' });
                const data = await resp.json();
                showToast(data.message, !data.success);
                document.getElementById('dropdown').classList.add('hidden');
                if (data.success) setTimeout(() => location.reload(), 500);
            } catch (e) {
                showToast('Failed to clear logs: ' + e.message, true);
            }
        }
        
        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            document.getElementById('auto-refresh-text').textContent = autoRefresh ? 'Pause Auto-Refresh' : 'Resume Auto-Refresh';
            document.getElementById('refresh-status').textContent = autoRefresh ? 'ON' : 'OFF';
            document.getElementById('dropdown').classList.add('hidden');
            
            if (autoRefresh) {
                scheduleRefresh();
                showToast('Auto-refresh enabled');
            } else {
                if (refreshTimer) clearTimeout(refreshTimer);
                showToast('Auto-refresh paused');
            }
        }
        
        function scheduleRefresh() {
            if (autoRefresh) {
                refreshTimer = setTimeout(() => location.reload(), 3000);
            }
        }
        
        // Start auto-refresh
        scheduleRefresh();
    </script>
</body>
</html>
'''


@app.route('/')
def dashboard():
    """Main dashboard page"""
    data = get_dashboard_data()
    return render_template_string(DASHBOARD_HTML, data=data)


@app.route('/api/status')
def api_status():
    """JSON API endpoint for status"""
    return jsonify(get_dashboard_data())


@app.route('/api/start', methods=['POST'])
def api_start():
    """Start the Ralph Loop"""
    global ralph_process
    
    # Check if already running
    if is_ralph_running():
        return jsonify({'success': False, 'message': 'Ralph Loop is already running'})
    
    try:
        # Start ralph-runner.py as a subprocess
        ralph_process = subprocess.Popen(
            [sys.executable, 'ralph-runner.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        # Write PID file
        with open(COORDINATOR_PID_FILE, 'w') as f:
            f.write(str(ralph_process.pid))
        
        return jsonify({'success': True, 'message': f'Ralph Loop started (PID: {ralph_process.pid})'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to start: {str(e)}'})


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop the Ralph Loop"""
    global ralph_process
    
    stopped = False
    message = []
    
    # Try to stop via PID file
    if COORDINATOR_PID_FILE.exists():
        try:
            with open(COORDINATOR_PID_FILE) as f:
                pid = int(f.read().strip())
            
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
            
            COORDINATOR_PID_FILE.unlink(missing_ok=True)
            stopped = True
            message.append(f'Stopped coordinator (PID: {pid})')
        except (ProcessLookupError, ValueError, PermissionError) as e:
            message.append(f'Coordinator cleanup: {e}')
            COORDINATOR_PID_FILE.unlink(missing_ok=True)
    
    # Also try to stop monitor if running
    if MONITOR_PID_FILE.exists():
        try:
            with open(MONITOR_PID_FILE) as f:
                pid = int(f.read().strip())
            
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
            
            MONITOR_PID_FILE.unlink(missing_ok=True)
            message.append(f'Stopped monitor (PID: {pid})')
        except (ProcessLookupError, ValueError, PermissionError) as e:
            message.append(f'Monitor cleanup: {e}')
            MONITOR_PID_FILE.unlink(missing_ok=True)
    
    # Stop our tracked process if any
    if ralph_process and ralph_process.poll() is None:
        ralph_process.terminate()
        ralph_process = None
        stopped = True
        message.append('Stopped tracked process')
    
    if stopped or message:
        return jsonify({'success': True, 'message': ' | '.join(message) if message else 'Ralph Loop stopped'})
    else:
        return jsonify({'success': False, 'message': 'Ralph Loop is not running'})


@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset task state (mark all as PENDING)"""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                state = json.load(f)
            
            # Reset all tasks to PENDING
            for task_id in state.get('tasks', {}):
                state['tasks'][task_id]['status'] = 'PENDING'
                state['tasks'][task_id]['updated_at'] = datetime.now().isoformat()
            
            # Clear promises
            state['promises'] = []
            
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            
            return jsonify({'success': True, 'message': 'All tasks reset to PENDING'})
        else:
            return jsonify({'success': False, 'message': 'No state file found'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Reset failed: {str(e)}'})


@app.route('/api/clear-logs', methods=['POST'])
def api_clear_logs():
    """Clear the log file"""
    try:
        if LOG_FILE.exists():
            with open(LOG_FILE, 'w') as f:
                f.write(f"[{datetime.now().isoformat()}] Logs cleared from dashboard\n")
            return jsonify({'success': True, 'message': 'Logs cleared'})
        return jsonify({'success': False, 'message': 'No log file found'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to clear logs: {str(e)}'})


def is_ralph_running():
    """Check if Ralph Loop is currently running"""
    global ralph_process
    
    # Check our tracked process
    if ralph_process and ralph_process.poll() is None:
        return True
    
    # Check PID file
    if COORDINATOR_PID_FILE.exists():
        try:
            with open(COORDINATOR_PID_FILE) as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            if os.name == 'nt':
                result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], capture_output=True, text=True)
                return str(pid) in result.stdout
            else:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                return True
        except (ProcessLookupError, ValueError, PermissionError, FileNotFoundError):
            pass
    
    return False


if __name__ == '__main__':
    print("=" * 50)
    print("Ralph Loop Dashboard")
    print("=" * 50)
    print("Open in browser: http://localhost:5050")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5050, debug=False)
