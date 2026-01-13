#!/usr/bin/env python3
"""
Progress Tracker Utility for Ralph Loop System

This utility monitors progress across all agents and provides
system-wide status reporting and coordination.
"""

import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set


class ProgressTracker:
    """Tracks progress across all Ralph Loop agents"""
    
    def __init__(self):
        self.plan_file = Path("PLAN.md")
        self.progress_file = Path("PROGRESS.md")
        self.state_file = Path(".ralph-state.json")
        self.log_file = Path("ralph-loop.log")
        self.agents = [
            "devops-automator",
            "agent-creator", 
            "db-wizard",
            "code-surgeon",
            "frontend-designer",
            "test-architect",
            "doc-smith"
        ]
    
    def load_state(self) -> Dict:
        """Load state from JSON file"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"tasks": {}, "promises": []}
    
    def parse_tasks_from_plan(self) -> List[Dict]:
        """Get all tasks from PLAN.md"""
        if not self.plan_file.exists():
            return []
            
        tasks = []
        with open(self.plan_file) as f:
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
                    'phase': int(task_id.split('.')[0]) if '.' in task_id else 1,
                    'acceptance_criteria': []
                }
                
            elif current_task and line.startswith('- **Agent:**'):
                current_task['agent'] = line.replace('- **Agent:**', '').strip()
                
            elif current_task and line.strip().startswith('- [ ]'):
                current_task['acceptance_criteria'].append(line.strip())
                
        if current_task:
            tasks.append(current_task)
            
        return tasks
    
    def get_task_status(self, task_id: str) -> str:
        """Get task status from state file"""
        state = self.load_state()
        return state.get("tasks", {}).get(task_id, {}).get("status", "PENDING")
    
    def get_agent_last_activity(self, agent_name: str) -> Optional[datetime]:
        """Get last activity timestamp for an agent from state"""
        state = self.load_state()
        
        last_activity = None
        for task_id, task_data in state.get("tasks", {}).items():
            if task_data.get("agent") == agent_name:
                updated_at = task_data.get("updated_at")
                if updated_at:
                    try:
                        timestamp = datetime.fromisoformat(updated_at)
                        if last_activity is None or timestamp > last_activity:
                            last_activity = timestamp
                    except ValueError:
                        continue
        
        return last_activity

    def get_system_status(self) -> Dict:
        """Get overall system status"""
        all_tasks = self.parse_tasks_from_plan()
        state = self.load_state()
        
        # Count tasks by status
        status_counts = {'PENDING': 0, 'IN_PROGRESS': 0, 'DONE': 0, 'BLOCKED': 0}
        phase_progress = {}
        
        for task in all_tasks:
            status = self.get_task_status(task['id'])
            status_counts[status] = status_counts.get(status, 0) + 1
            
            phase = task['phase']
            if phase not in phase_progress:
                phase_progress[phase] = {'total': 0, 'done': 0}
            phase_progress[phase]['total'] += 1
            if status == 'DONE':
                phase_progress[phase]['done'] += 1
        
        # Calculate overall progress
        total_tasks = len(all_tasks)
        completed_tasks = status_counts['DONE']
        progress_percent = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Check agent activity
        agent_status = {}
        stuck_agents = []
        
        for agent in self.agents:
            last_activity = self.get_agent_last_activity(agent)
            is_active = last_activity and (datetime.now() - last_activity) < timedelta(minutes=30)
            
            agent_status[agent] = {
                'last_activity': last_activity,
                'status': 'ACTIVE' if is_active else 'IDLE'
            }
            
            if last_activity and not is_active:
                # Check if agent has incomplete tasks
                agent_tasks = [t for t in all_tasks if t['agent'] == agent]
                incomplete = [t for t in agent_tasks if self.get_task_status(t['id']) == 'IN_PROGRESS']
                if incomplete:
                    stuck_agents.append(agent)
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress_percent': progress_percent,
            'status_counts': status_counts,
            'phase_progress': phase_progress,
            'agent_status': agent_status,
            'stuck_agents': stuck_agents,
            'promises': state.get("promises", []),
            'timestamp': datetime.now()
        }
    
    def generate_status_report(self) -> str:
        """Generate a comprehensive status report"""
        status = self.get_system_status()
        
        report = f"""
# Ralph Loop System Status Report
Generated: {status['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

## Overall Progress
- Total Tasks: {status['total_tasks']}
- Completed: {status['completed_tasks']}
- Progress: {status['progress_percent']:.1f}%

## Task Status Breakdown
- PENDING: {status['status_counts'].get('PENDING', 0)}
- IN_PROGRESS: {status['status_counts'].get('IN_PROGRESS', 0)}
- DONE: {status['status_counts'].get('DONE', 0)}
- BLOCKED: {status['status_counts'].get('BLOCKED', 0)}

## Phase Progress
"""
        
        for phase in sorted(status['phase_progress'].keys()):
            progress = status['phase_progress'][phase]
            percent = (progress['done'] / progress['total'] * 100) if progress['total'] > 0 else 0
            report += f"- Phase {phase}: {progress['done']}/{progress['total']} ({percent:.1f}%)\n"
        
        report += "\n## Agent Status\n"
        for agent, info in status['agent_status'].items():
            last_activity = info['last_activity'].strftime('%H:%M:%S') if info['last_activity'] else 'Never'
            report += f"- {agent}: {info['status']} (Last: {last_activity})\n"
        
        if status['stuck_agents']:
            report += f"\n## [WARNING] Stuck Agents\n"
            for agent in status['stuck_agents']:
                report += f"- {agent}: Has IN_PROGRESS tasks but no recent activity\n"
        
        report += f"\n## Completion Promises ({len(status['promises'])}/{len(self.agents)})\n"
        for agent in self.agents:
            status_icon = "[OK]" if agent in status['promises'] else "[  ]"
            report += f"- {status_icon} {agent}\n"
        
        # Check if system is complete
        if status['completed_tasks'] == status['total_tasks'] and len(status['promises']) == len(self.agents):
            report += "\n## [SUCCESS] SYSTEM COMPLETE!\n"
            report += "All tasks done and all agents have emitted completion promises.\n"
        
        return report
    
    def get_task_details(self) -> str:
        """Get detailed task list with status"""
        all_tasks = self.parse_tasks_from_plan()
        
        report = "\n## Task Details\n\n"
        current_phase = 0
        
        for task in all_tasks:
            if task['phase'] != current_phase:
                current_phase = task['phase']
                report += f"\n### Phase {current_phase}\n"
            
            status = self.get_task_status(task['id'])
            status_icon = {"PENDING": "[ ]", "IN_PROGRESS": "[~]", "DONE": "[x]"}.get(status, "[?]")
            
            report += f"- {status_icon} {task['id']}: {task['title']}\n"
            report += f"      Agent: {task['agent']} | Status: {status}\n"
        
        return report
    
    def monitor_loop(self, interval: int = 60):
        """Run continuous monitoring loop"""
        print("Starting Ralph Loop Progress Monitor...")
        print("Press Ctrl+C to stop\n")
        
        while True:
            try:
                # Generate status report
                report = self.generate_status_report()
                
                # Clear screen and show report
                os.system('cls' if os.name == 'nt' else 'clear')
                print(report)
                
                # Check if system is complete
                status = self.get_system_status()
                if (status['completed_tasks'] == status['total_tasks'] and 
                    len(status['promises']) == len(self.agents)):
                    print("\n[SUCCESS] SYSTEM COMPLETE!")
                    break
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\nMonitoring stopped by user")
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(interval)


def main():
    """Main entry point"""
    import sys
    
    tracker = ProgressTracker()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'monitor':
            tracker.monitor_loop()
        elif cmd == 'details':
            print(tracker.generate_status_report())
            print(tracker.get_task_details())
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python progress-tracker.py [monitor|details]")
    else:
        # Just show current status
        report = tracker.generate_status_report()
        print(report)


if __name__ == "__main__":
    main()
