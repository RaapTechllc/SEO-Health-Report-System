#!/usr/bin/env python3
"""
Task Picker Utility for Ralph Loop Agents

This utility helps agents pick and claim tasks from the shared PLAN.md
and update PROGRESS.md atomically to prevent conflicts.
"""

import fcntl
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class TaskPicker:
    """Handles task selection and claiming for Ralph Loop agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.plan_file = Path("PLAN.md")
        self.progress_file = Path("PROGRESS.md")
        self.lock_file = Path(".progress.lock")
        
    def get_available_tasks(self) -> List[Dict]:
        """Get all tasks available for this agent"""
        if not self.plan_file.exists():
            return []
            
        tasks = []
        with open(self.plan_file) as f:
            content = f.read()
            
        # Parse tasks from PLAN.md (simplified parser)
        lines = content.split('\n')
        current_task = None
        
        for line in lines:
            if line.startswith('#### Task '):
                if current_task:
                    tasks.append(current_task)
                    
                task_id = line.split(':')[0].replace('#### Task ', '')
                title = line.split(':', 1)[1].strip() if ':' in line else ''
                
                current_task = {
                    'id': task_id,
                    'title': title,
                    'agent': None,
                    'status': 'PENDING',
                    'dependencies': [],
                    'acceptance_criteria': []
                }
                
            elif current_task and line.startswith('- **Agent:**'):
                current_task['agent'] = line.replace('- **Agent:**', '').strip()
                
            elif current_task and line.strip().startswith('- [ ]'):
                current_task['acceptance_criteria'].append(line.strip())
                
        if current_task:
            tasks.append(current_task)
            
        # Filter for this agent's tasks
        agent_tasks = [t for t in tasks if t['agent'] == self.agent_name]
        return agent_tasks
    
    def get_task_status(self, task_id: str) -> str:
        """Get current status of a task from PROGRESS.md"""
        if not self.progress_file.exists():
            return 'PENDING'
            
        with open(self.progress_file) as f:
            content = f.read()
            
        # Look for task status in progress file
        # This is simplified - production would use proper parsing
        for line in content.split('\n'):
            if task_id in line and '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    return parts[3]  # Status column
                    
        return 'PENDING'
    
    def check_dependencies(self, task: Dict) -> bool:
        """Check if task dependencies are satisfied"""
        task_phase = int(task['id'].split('.')[0])
        
        if task_phase == 1:
            return True  # Phase 1 has no dependencies
            
        # Check if previous phase tasks are complete
        # Simplified dependency checking
        if task_phase > 1:
            # For now, just check if any Phase 1 tasks are still pending
            phase1_tasks = self.get_available_tasks()
            phase1_pending = [t for t in phase1_tasks if t['id'].startswith('1.') and self.get_task_status(t['id']) != 'DONE']
            
            if phase1_pending and task_phase > 1:
                return False
                
        return True
    
    def claim_task(self, task_id: str) -> bool:
        """Atomically claim a task by updating PROGRESS.md"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Use file locking to prevent race conditions
                with open(self.lock_file, 'w') as lock:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    
                    # Check if task is still available
                    current_status = self.get_task_status(task_id)
                    if current_status != 'PENDING':
                        return False
                        
                    # Update progress file
                    self.update_task_status(task_id, 'IN_PROGRESS', f"Claimed by {self.agent_name}")
                    
                    return True
                    
            except (IOError, OSError) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    print(f"Failed to claim task {task_id} after {max_retries} attempts: {e}")
                    return False
                    
        return False
    
    def update_task_status(self, task_id: str, status: str, notes: str = ""):
        """Update task status in PROGRESS.md"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Read current progress
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                content = f.read()
        else:
            content = ""
            
        # Update the progress file (simplified implementation)
        # In production, this would use proper markdown parsing and updating
        
        # For now, append a log entry
        log_entry = f"\n[{timestamp}] {self.agent_name}: Task {task_id} -> {status}"
        if notes:
            log_entry += f" ({notes})"
            
        with open(self.progress_file, 'a') as f:
            f.write(log_entry)
            
        print(f"Updated task {task_id}: {status}")
    
    def complete_task(self, task_id: str, notes: str = ""):
        """Mark task as complete"""
        self.update_task_status(task_id, 'DONE', notes)
    
    def pick_next_task(self) -> Optional[Dict]:
        """Pick the next available task for this agent"""
        available_tasks = self.get_available_tasks()
        
        for task in available_tasks:
            # Check if task is still pending
            if self.get_task_status(task['id']) != 'PENDING':
                continue
                
            # Check dependencies
            if not self.check_dependencies(task):
                continue
                
            # Try to claim the task
            if self.claim_task(task['id']):
                return task
                
        return None
    
    def get_agent_completion_status(self) -> Tuple[int, int]:
        """Get completion status for this agent (completed, total)"""
        all_tasks = self.get_available_tasks()
        completed = sum(1 for task in all_tasks if self.get_task_status(task['id']) == 'DONE')
        total = len(all_tasks)
        return completed, total

def main():
    """Test the task picker"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python task-picker.py <agent_name>")
        sys.exit(1)
        
    agent_name = sys.argv[1]
    picker = TaskPicker(agent_name)
    
    print(f"Task picker for agent: {agent_name}")
    
    # Show available tasks
    tasks = picker.get_available_tasks()
    print(f"Available tasks: {len(tasks)}")
    
    for task in tasks:
        status = picker.get_task_status(task['id'])
        deps_ok = picker.check_dependencies(task)
        print(f"  {task['id']}: {task['title']} (Status: {status}, Deps: {'OK' if deps_ok else 'BLOCKED'})")
    
    # Try to pick next task
    next_task = picker.pick_next_task()
    if next_task:
        print(f"Picked task: {next_task['id']} - {next_task['title']}")
    else:
        print("No tasks available to pick")

if __name__ == "__main__":
    main()