#!/usr/bin/env python3
"""
Kiro CLI - Agent Chat Interface

Interactive CLI for chatting with Kiro agents defined in .kiro/agents/

Usage:
    python kiro_cli.py --agent orchestrator
    python kiro_cli.py --agent code-surgeon
    python kiro_cli.py --list
"""

import argparse
import json
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Check for required dependencies
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


class AgentDashboard:
    """Simple dashboard for agent activity tracking."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.start_time = datetime.now()
        self.messages_sent = 0
        self.messages_received = 0
        self.current_phase = "Ready"
        self.tasks_completed = 0
        self.delegations = []
    
    def update_phase(self, phase: str):
        self.current_phase = phase
    
    def log_delegation(self, target_agent: str, task: str):
        self.delegations.append({
            "agent": target_agent,
            "task": task,
            "time": datetime.now().strftime("%H:%M:%S")
        })
    
    def render(self) -> str:
        """Render dashboard as string."""
        elapsed = datetime.now() - self.start_time
        elapsed_str = f"{int(elapsed.total_seconds() // 60)}m {int(elapsed.total_seconds() % 60)}s"
        
        lines = [
            f"{Colors.DIM}{'─' * 60}{Colors.ENDC}",
            f"{Colors.CYAN}Agent:{Colors.ENDC} {self.agent_name} | "
            f"{Colors.CYAN}Phase:{Colors.ENDC} {self.current_phase} | "
            f"{Colors.CYAN}Time:{Colors.ENDC} {elapsed_str}",
            f"{Colors.CYAN}Messages:{Colors.ENDC} {self.messages_sent} sent / {self.messages_received} received",
        ]
        
        if self.delegations:
            lines.append(f"{Colors.CYAN}Recent Delegations:{Colors.ENDC}")
            for d in self.delegations[-3:]:
                lines.append(f"  {Colors.DIM}{d['time']}{Colors.ENDC} -> {d['agent']}: {d['task'][:40]}...")
        
        lines.append(f"{Colors.DIM}{'─' * 60}{Colors.ENDC}")
        return "\n".join(lines)


class KiroCLI:
    """Main CLI interface for Kiro agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.agents_dir = Path(".kiro/agents")
        self.agent_config = self._load_agent_config(agent_name)
        self.dashboard = AgentDashboard(agent_name)
        self.conversation_history: List[Dict[str, str]] = []
        self.client = None
        
        if HAS_ANTHROPIC:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)
    
    def _load_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Load agent configuration from JSON file."""
        agent_file = self.agents_dir / f"{agent_name}.json"
        
        if not agent_file.exists():
            print(f"{Colors.RED}[ERROR] Agent '{agent_name}' not found at {agent_file}{Colors.ENDC}")
            print(f"\nAvailable agents:")
            self._list_agents()
            sys.exit(1)
        
        with open(agent_file) as f:
            return json.load(f)
    
    def _list_agents(self):
        """List all available agents."""
        if not self.agents_dir.exists():
            print(f"{Colors.RED}No agents directory found at {self.agents_dir}{Colors.ENDC}")
            return
        
        agents = []
        for f in self.agents_dir.glob("*.json"):
            if f.name == ".gitkeep":
                continue
            try:
                with open(f) as file:
                    config = json.load(file)
                    agents.append({
                        "name": config.get("name", f.stem),
                        "description": config.get("description", "No description")[:60]
                    })
            except (json.JSONDecodeError, KeyError):
                continue
        
        for agent in sorted(agents, key=lambda x: x["name"]):
            print(f"  {Colors.GREEN}{agent['name']}{Colors.ENDC}: {agent['description']}")
    
    def _build_system_prompt(self) -> str:
        """Build system prompt from agent config and steering files."""
        base_prompt = self.agent_config.get("prompt", "You are a helpful assistant.")
        
        # Load steering files
        steering_dir = Path(".kiro/steering")
        steering_content = []
        
        if steering_dir.exists():
            for md_file in steering_dir.glob("*.md"):
                try:
                    content = md_file.read_text()
                    steering_content.append(f"## {md_file.stem}\n{content}")
                except Exception:
                    continue
        
        if steering_content:
            base_prompt += "\n\n# Project Context\n" + "\n\n".join(steering_content[:3])
        
        return base_prompt
    
    def _detect_phase(self, message: str) -> Optional[str]:
        """Detect workflow phase from message content."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["plan", "new feature", "prd", "spec"]):
            return "Requirements"
        elif "design" in message_lower and "approved" in message_lower:
            return "Design"
        elif "task" in message_lower:
            return "Implementation"
        elif any(word in message_lower for word in ["deploy", "ship"]):
            return "Deployment"
        
        return None
    
    def _detect_delegation(self, response: str) -> Optional[tuple]:
        """Detect if response mentions delegating to another agent."""
        agents = ["code-surgeon", "test-architect", "db-wizard", 
                  "frontend-designer", "devops-automator", "doc-smith"]
        
        response_lower = response.lower()
        for agent in agents:
            if agent in response_lower:
                # Try to extract task context
                return (agent, "Task delegation detected")
        
        return None
    
    async def chat(self, user_message: str) -> str:
        """Send message to agent and get response."""
        self.dashboard.messages_sent += 1
        
        # Detect phase changes
        phase = self._detect_phase(user_message)
        if phase:
            self.dashboard.update_phase(phase)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        if not self.client:
            return self._mock_response(user_message)
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.agent_config.get("model", "claude-sonnet-4-20250514"),
                max_tokens=4096,
                system=self._build_system_prompt(),
                messages=self.conversation_history
            )
            
            assistant_message = response.content[0].text
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant", 
                "content": assistant_message
            })
            
            self.dashboard.messages_received += 1
            
            # Check for delegations
            delegation = self._detect_delegation(assistant_message)
            if delegation:
                self.dashboard.log_delegation(delegation[0], delegation[1])
            
            return assistant_message
            
        except Exception as e:
            return f"{Colors.RED}[API Error] {e}{Colors.ENDC}"
    
    def _mock_response(self, user_message: str) -> str:
        """Mock response when API is not available."""
        self.dashboard.messages_received += 1
        
        responses = {
            "plan": f"""I'll help you plan this feature. Let me create the requirements document.

**Phase 1: Requirements**

I'll create `.kiro/specs/[feature-name]/requirements.md` with:
- User stories with EARS acceptance criteria
- Functional requirements
- Non-functional requirements

What feature would you like to plan?""",
            
            "help": f"""**{self.agent_config.get('name', 'Agent')} - Available Commands**

- `plan [feature]` - Start spec-driven development
- `design approved` - Move to design phase
- `start task X` - Begin implementation
- `status` - Show current progress
- `delegate [agent]` - Hand off to specialist

**Specialist Agents:**
- code-surgeon: Code review, refactoring
- test-architect: Testing, coverage
- db-wizard: Database design
- frontend-designer: UI/UX
- devops-automator: CI/CD, deployment
- doc-smith: Documentation""",
            
            "status": f"""**Current Status**

Phase: {self.dashboard.current_phase}
Messages: {self.dashboard.messages_sent} sent / {self.dashboard.messages_received} received
Tasks Completed: {self.dashboard.tasks_completed}

Ready for your next instruction."""
        }
        
        for key, response in responses.items():
            if key in user_message.lower():
                return response
        
        return f"""I understand. As the {self.agent_config.get('name', 'orchestrator')}, I'm ready to help.

Type `help` to see available commands, or describe what you'd like to accomplish."""
    
    def run_interactive(self):
        """Run interactive chat loop."""
        self._print_header()
        
        print(f"\n{Colors.GREEN}Agent loaded successfully!{Colors.ENDC}")
        print(f"Type {Colors.CYAN}help{Colors.ENDC} for commands, {Colors.CYAN}exit{Colors.ENDC} to quit.\n")
        
        if not HAS_ANTHROPIC:
            print(f"{Colors.YELLOW}[WARNING] anthropic package not installed. Running in mock mode.{Colors.ENDC}")
            print(f"Install with: pip install anthropic\n")
        elif not os.environ.get("ANTHROPIC_API_KEY"):
            print(f"{Colors.YELLOW}[WARNING] ANTHROPIC_API_KEY not set. Running in mock mode.{Colors.ENDC}\n")
        
        while True:
            try:
                # Show mini dashboard
                print(f"\n{Colors.DIM}[{self.dashboard.current_phase}]{Colors.ENDC}")
                
                # Get user input
                user_input = input(f"{Colors.BOLD}You:{Colors.ENDC} ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["exit", "quit", "q"]:
                    print(f"\n{Colors.CYAN}Goodbye!{Colors.ENDC}")
                    break
                
                if user_input.lower() == "dashboard":
                    print(self.dashboard.render())
                    continue
                
                # Get response
                print(f"\n{Colors.BLUE}{self.agent_name}:{Colors.ENDC} ", end="", flush=True)
                response = asyncio.run(self.chat(user_input))
                print(response)
                
            except KeyboardInterrupt:
                print(f"\n\n{Colors.CYAN}Interrupted. Goodbye!{Colors.ENDC}")
                break
            except EOFError:
                break
    
    def _print_header(self):
        """Print CLI header."""
        print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════╗
║                    KIRO AGENT CLI                        ║
╚══════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.BOLD}Agent:{Colors.ENDC} {self.agent_config.get('name', 'unknown')}
{Colors.BOLD}Model:{Colors.ENDC} {self.agent_config.get('model', 'default')}
{Colors.BOLD}Description:{Colors.ENDC} {self.agent_config.get('description', 'No description')[:70]}
""")


def main():
    parser = argparse.ArgumentParser(
        description="Kiro Agent CLI - Interactive chat with Kiro agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python kiro_cli.py --agent orchestrator
    python kiro_cli.py --agent code-surgeon
    python kiro_cli.py --list
        """
    )
    
    parser.add_argument("--agent", "-a", help="Agent name to load")
    parser.add_argument("--list", "-l", action="store_true", help="List available agents")
    
    args = parser.parse_args()
    
    if args.list:
        print(f"\n{Colors.CYAN}Available Agents:{Colors.ENDC}\n")
        cli = KiroCLI.__new__(KiroCLI)
        cli.agents_dir = Path(".kiro/agents")
        cli._list_agents()
        return
    
    if not args.agent:
        parser.print_help()
        print(f"\n{Colors.YELLOW}Tip: Use --agent orchestrator to start the orchestrator{Colors.ENDC}")
        return
    
    cli = KiroCLI(args.agent)
    cli.run_interactive()


if __name__ == "__main__":
    main()
