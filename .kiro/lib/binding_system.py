from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from enum import Enum
import json
import logging
from pathlib import Path

from agent_schema import AgentConfig, parse_agent_config

class LifecycleEvent(Enum):
    SESSION_START = "onStart"
    TASK_COMPLETE = "onComplete"
    AFTER_WRITE = "afterWrite"
    AFTER_ERROR = "afterError"

@dataclass
class PromptBinding:
    event: LifecycleEvent
    prompt_names: List[str]
    condition: Optional[Callable[[], bool]] = None

class BindingSystem:
    def __init__(self, prompts_dir: str = ".kiro/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.logger = logging.getLogger(__name__)
        self.hooks: List[Dict] = []
    
    def parse_config(self, agent_config: dict) -> AgentConfig:
        """Parse agent JSON config and extract prompt bindings."""
        return parse_agent_config(agent_config)
    
    def invoke_prompts(self, event: LifecycleEvent, agent_name: str, agent_config: AgentConfig) -> List[str]:
        """Invoke all prompts bound to the given lifecycle event in correct order."""
        invoked_prompts = []
        
        # Get prompts for this event
        if event == LifecycleEvent.SESSION_START:
            prompt_names = agent_config.prompts.on_start
            self.logger.info(f"Session start for {agent_name}: invoking {len(prompt_names)} prompts")
        elif event == LifecycleEvent.TASK_COMPLETE:
            prompt_names = agent_config.prompts.on_complete
            self.logger.info(f"Task complete for {agent_name}: invoking {len(prompt_names)} prompts")
        elif event == LifecycleEvent.AFTER_WRITE:
            prompt_names = agent_config.prompts.auto_trigger.get('afterWrite', [])
            self.logger.info(f"After write trigger for {agent_name}: invoking {len(prompt_names)} prompts")
        elif event == LifecycleEvent.AFTER_ERROR:
            prompt_names = agent_config.prompts.auto_trigger.get('afterError', [])
            self.logger.info(f"After error trigger for {agent_name}: invoking {len(prompt_names)} prompts")
        else:
            prompt_names = []
        
        # Invoke each prompt in order
        for i, prompt_name in enumerate(prompt_names):
            prompt_path = self.prompts_dir / f"{prompt_name}.md"
            
            if not prompt_path.exists():
                self.logger.warning(f"Prompt file not found: {prompt_path} (continuing execution)")
                continue
                
            try:
                with open(prompt_path, 'r') as f:
                    prompt_content = f.read()
                    invoked_prompts.append(prompt_content)
                    self.logger.info(f"[{i+1}/{len(prompt_names)}] Invoked prompt: {prompt_name} for {agent_name}")
            except Exception as e:
                self.logger.error(f"Failed to read prompt {prompt_name}: {e} (continuing execution)")
                continue
        
        return invoked_prompts
    
    def register_hook(self, matcher: str, command: str) -> None:
        """Register a post-tool-use hook for automatic verification."""
        hook = {"matcher": matcher, "command": command}
        self.hooks.append(hook)
        self.logger.info(f"Registered hook: {matcher} -> {command}")
    
    def trigger_hooks(self, tool_name: str) -> List[str]:
        """Trigger hooks that match the given tool name."""
        triggered_commands = []
        
        for hook in self.hooks:
            if hook["matcher"] in tool_name or tool_name in hook["matcher"]:
                triggered_commands.append(hook["command"])
                self.logger.info(f"Triggered hook: {hook['command']}")
        
        return triggered_commands
