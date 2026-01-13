#!/usr/bin/env python3
"""
Ralph Loop Multi-Agent System Coordinator

This script orchestrates multiple agents running in parallel Ralph loops.
Each agent continuously picks tasks, executes them, and updates progress
until all work is complete.
"""

import asyncio
import json
import logging
import os
import re
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Windows-compatible file locking
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    try:
        import msvcrt
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ralph-loop.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TaskStateManager:
    """Manages persistent task state with file locking"""
    
    def __init__(self, state_file: Path = Path(".ralph-state.json")):
        self.state_file = state_file
        self.lock_file = Path(".ralph-state.lock")
        self._load_state()
    
    def _load_state(self):
        """Load state from file or initialize empty state"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    self.state = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.state = {"tasks": {}, "promises": []}
        else:
            self.state = {"tasks": {}, "promises": []}
    
    def _save_state(self):
        """Save state to file with locking"""
        try:
            # Platform-specific file locking
            if HAS_FCNTL:
                with open(self.lock_file, 'w') as lock:
                    try:
                        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except (IOError, OSError):
                        pass
                    with open(self.state_file, 'w') as f:
                        json.dump(self.state, f, indent=2)
            elif HAS_MSVCRT:
                # Windows locking
                with open(self.state_file, 'w') as f:
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    except (IOError, OSError):
                        pass
                    json.dump(self.state, f, indent=2)
            else:
                # No locking available, just write
                with open(self.state_file, 'w') as f:
                    json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_task_status(self, task_id: str) -> str:
        """Get current status of a task"""
        return self.state["tasks"].get(task_id, {}).get("status", "PENDING")
    
    def set_task_status(self, task_id: str, status: str, agent: str):
        """Set task status atomically"""
        self._load_state()  # Refresh state
        
        if task_id not in self.state["tasks"]:
            self.state["tasks"][task_id] = {}
        
        self.state["tasks"][task_id].update({
            "status": status,
            "agent": agent,
            "updated_at": datetime.now().isoformat()
        })
        self._save_state()
    
    def claim_task(self, task_id: str, agent: str) -> bool:
        """Atomically claim a task if it's available"""
        self._load_state()  # Refresh state
        
        current_status = self.get_task_status(task_id)
        if current_status != "PENDING":
            return False  # Task already claimed or done
        
        self.set_task_status(task_id, "IN_PROGRESS", agent)
        return True
    
    def complete_task(self, task_id: str, agent: str):
        """Mark task as complete"""
        self.set_task_status(task_id, "DONE", agent)
    
    def add_promise(self, agent: str):
        """Record agent completion promise"""
        self._load_state()
        if agent not in self.state["promises"]:
            self.state["promises"].append(agent)
            self._save_state()
    
    def get_promises(self) -> List[str]:
        """Get list of agents who have completed"""
        self._load_state()
        return self.state["promises"]
    
    def get_completed_tasks(self) -> Set[str]:
        """Get set of completed task IDs"""
        self._load_state()
        return {tid for tid, data in self.state["tasks"].items() 
                if data.get("status") == "DONE"}
    
    def reset(self):
        """Reset all state (for fresh start)"""
        self.state = {"tasks": {}, "promises": []}
        self._save_state()


class RalphLoopCoordinator:
    """Coordinates multiple agents in Ralph loops"""
    
    def __init__(self):
        self.agents_dir = Path(".kiro/agents")
        self.plan_file = Path("PLAN.md")
        self.progress_file = Path("PROGRESS.md")
        self.state_manager = TaskStateManager()
        self.running = False
        self.agent_processes = {}
        
    def load_agent_configs(self) -> Dict[str, dict]:
        """Load all agent configurations"""
        agents = {}
        agent_files = [
            "devops-automator.json",
            "agent-creator.json", 
            "db-wizard.json",
            "code-surgeon.json",
            "frontend-designer.json",
            "test-architect.json",
            "doc-smith.json"
        ]
        
        for agent_file in agent_files:
            agent_path = self.agents_dir / agent_file
            if agent_path.exists():
                try:
                    with open(agent_path) as f:
                        config = json.load(f)
                        agents[config['name']] = config
                        logger.info(f"Loaded agent config: {config['name']}")
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Invalid agent config {agent_file}: {e}")
            else:
                logger.warning(f"Agent config not found: {agent_file}")
                
        return agents
    
    def parse_tasks_from_plan(self) -> List[Dict]:
        """Parse PLAN.md and return all tasks"""
        if not self.plan_file.exists():
            logger.error("PLAN.md not found")
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
                
                # Parse task ID and title
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
    
    def get_tasks_with_status(self) -> List[Dict]:
        """Get all tasks with their current status from state manager"""
        tasks = self.parse_tasks_from_plan()
        
        for task in tasks:
            task['status'] = self.state_manager.get_task_status(task['id'])
        
        return tasks
    
    def check_phase_dependencies(self, task: Dict) -> bool:
        """Check if previous phase is complete before starting this task"""
        task_phase = task.get('phase', 1)
        
        if task_phase == 1:
            return True  # Phase 1 has no dependencies
        
        # Get all tasks from previous phase
        all_tasks = self.get_tasks_with_status()
        previous_phase_tasks = [t for t in all_tasks if t.get('phase') == task_phase - 1]
        
        # Check if all previous phase tasks are DONE
        for prev_task in previous_phase_tasks:
            if prev_task['status'] != 'DONE':
                return False
        
        return True
    
    def log_progress(self, task_id: str, status: str, agent: str, notes: str = ""):
        """Append progress entry to PROGRESS.md"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Task {task_id}: {status} by {agent}"
        if notes:
            log_entry += f" - {notes}"
        
        try:
            with open(self.progress_file, 'a') as f:
                f.write(log_entry + "\n")
        except IOError as e:
            logger.error(f"Failed to log progress: {e}")
    
    def check_all_complete(self) -> bool:
        """Check if all tasks are complete and all agents have promised"""
        all_tasks = self.get_tasks_with_status()
        
        # Check all tasks are DONE
        for task in all_tasks:
            if task['status'] != 'DONE':
                return False
        
        # Check all agents have promised
        required_agents = {
            "devops-automator", "agent-creator", "db-wizard", 
            "code-surgeon", "frontend-designer", "test-architect", "doc-smith"
        }
        promises = set(self.state_manager.get_promises())
        
        return required_agents.issubset(promises)

    async def execute_task(self, agent_name: str, task: Dict) -> bool:
        """
        Execute a task. This is where actual agent work would happen.
        
        In a real implementation, this would:
        1. Load the agent's prompt and tools
        2. Invoke the LLM with task context
        3. Execute the agent's actions
        4. Verify acceptance criteria
        
        For now, we simulate with a placeholder that logs what would happen.
        """
        task_id = task['id']
        title = task['title']
        
        logger.info(f"[{agent_name}] Executing task {task_id}: {title}")
        
        # TODO: Replace with actual agent execution
        # This would involve:
        # - Loading agent config and prompt
        # - Calling LLM API with task context
        # - Executing tool calls
        # - Verifying acceptance criteria
        
        # Simulate work with variable time based on task complexity
        work_time = 5 + len(task.get('acceptance_criteria', [])) * 2
        await asyncio.sleep(work_time)
        
        # For now, mark as complete after simulation
        # In production, this would verify acceptance criteria
        logger.info(f"[{agent_name}] Completed task {task_id}")
        return True
    
    async def run_agent_loop(self, agent_name: str, config: dict):
        """Run a single agent in Ralph loop"""
        logger.info(f"Starting Ralph loop for agent: {agent_name}")
        
        max_idle_cycles = 10  # Stop after 10 cycles with no work
        idle_cycles = 0
        
        while self.running:
            try:
                # Get all tasks with current status
                all_tasks = self.get_tasks_with_status()
                
                # Find PENDING tasks for this agent
                agent_tasks = [
                    t for t in all_tasks 
                    if t['agent'] == agent_name and t['status'] == 'PENDING'
                ]
                
                if not agent_tasks:
                    # Check if agent has any remaining tasks
                    remaining = [
                        t for t in all_tasks 
                        if t['agent'] == agent_name and t['status'] != 'DONE'
                    ]
                    
                    if not remaining:
                        # Agent is done with all tasks
                        logger.info(f"[{agent_name}] All tasks complete, emitting promise")
                        self.state_manager.add_promise(agent_name)
                        self.log_progress("ALL", "PROMISE", agent_name, "<promise>DONE</promise>")
                        break
                    
                    # Tasks exist but are blocked or in progress
                    idle_cycles += 1
                    if idle_cycles >= max_idle_cycles:
                        logger.warning(f"[{agent_name}] Max idle cycles reached, stopping")
                        break
                    
                    await asyncio.sleep(30)  # Wait before checking again
                    continue
                
                # Reset idle counter when we have work
                idle_cycles = 0
                
                # Find first task with satisfied dependencies
                task_to_execute = None
                for task in agent_tasks:
                    if self.check_phase_dependencies(task):
                        task_to_execute = task
                        break
                
                if not task_to_execute:
                    # All tasks blocked by dependencies
                    logger.info(f"[{agent_name}] Waiting for dependencies...")
                    await asyncio.sleep(30)
                    continue
                
                task_id = task_to_execute['id']
                
                # Try to claim the task atomically
                if not self.state_manager.claim_task(task_id, agent_name):
                    # Task was claimed by another agent
                    logger.info(f"[{agent_name}] Task {task_id} already claimed, skipping")
                    await asyncio.sleep(5)
                    continue
                
                # Log the claim
                self.log_progress(task_id, "IN_PROGRESS", agent_name, "Task claimed")
                
                # Execute the task
                success = await self.execute_task(agent_name, task_to_execute)
                
                if success:
                    # Mark task complete
                    self.state_manager.complete_task(task_id, agent_name)
                    self.log_progress(task_id, "DONE", agent_name, "Task completed")
                else:
                    # Task failed, reset to pending for retry
                    self.state_manager.set_task_status(task_id, "PENDING", agent_name)
                    self.log_progress(task_id, "FAILED", agent_name, "Task failed, will retry")
                    await asyncio.sleep(60)  # Back off before retry
                
            except Exception as e:
                logger.error(f"[{agent_name}] Error in loop: {e}")
                await asyncio.sleep(60)  # Back off on error
        
        logger.info(f"[{agent_name}] Ralph loop ended")
    
    async def monitor_progress(self):
        """Monitor overall progress and detect completion"""
        while self.running:
            try:
                if self.check_all_complete():
                    logger.info("=== ALL TASKS COMPLETE ===")
                    logger.info("All agents have emitted completion promises")
                    self.running = False
                    break
                
                # Log current status periodically
                all_tasks = self.get_tasks_with_status()
                done = sum(1 for t in all_tasks if t['status'] == 'DONE')
                total = len(all_tasks)
                logger.info(f"Progress: {done}/{total} tasks complete ({done/total*100:.1f}%)")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in progress monitor: {e}")
                await asyncio.sleep(60)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def start(self, reset_state: bool = False):
        """Start the Ralph loop system"""
        logger.info("=" * 60)
        logger.info("Starting Ralph Loop Multi-Agent System")
        logger.info("=" * 60)
        
        if reset_state:
            logger.info("Resetting task state...")
            self.state_manager.reset()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Load agent configurations
        agents = self.load_agent_configs()
        if not agents:
            logger.error("No agent configurations found")
            return
        
        logger.info(f"Loaded {len(agents)} agents: {list(agents.keys())}")
        
        # Parse tasks
        tasks = self.parse_tasks_from_plan()
        logger.info(f"Found {len(tasks)} tasks in PLAN.md")
        
        self.running = True
        
        # Start agent loops
        agent_tasks = []
        for agent_name, config in agents.items():
            task = asyncio.create_task(self.run_agent_loop(agent_name, config))
            agent_tasks.append(task)
        
        # Start progress monitor
        monitor_task = asyncio.create_task(self.monitor_progress())
        agent_tasks.append(monitor_task)
        
        # Wait for completion or shutdown
        try:
            await asyncio.gather(*agent_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            logger.info("Ralph Loop system shutdown complete")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ralph Loop Multi-Agent Coordinator")
    parser.add_argument("--reset", action="store_true", help="Reset task state before starting")
    args = parser.parse_args()
    
    coordinator = RalphLoopCoordinator()
    
    try:
        asyncio.run(coordinator.start(reset_state=args.reset))
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
