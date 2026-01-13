from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
import re
from pathlib import Path

@dataclass
class HookConfig:
    matcher: str
    command: str

@dataclass
class AgentPromptConfig:
    on_start: List[str] = field(default_factory=list)
    on_complete: List[str] = field(default_factory=list)
    available: List[str] = field(default_factory=list)
    auto_trigger: Dict[str, List[str]] = field(default_factory=dict)

@dataclass
class AgentConfig:
    name: str
    description: str
    prompt: str
    model: str
    version: str = "1.0.0"
    tools: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    tools_settings: Dict[str, Any] = field(default_factory=dict)
    prompts: AgentPromptConfig = field(default_factory=AgentPromptConfig)
    hooks: List[HookConfig] = field(default_factory=list)

def validate_semver(version: str) -> bool:
    """Validate semantic version format."""
    pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
    return bool(re.match(pattern, version))

def parse_agent_config(config_data: dict) -> AgentConfig:
    """Parse agent JSON config and extract all fields with sensible defaults."""
    # Handle prompts section with defaults
    prompts_data = config_data.get('prompts', {})
    prompts = AgentPromptConfig(
        on_start=prompts_data.get('onStart', ['prime'] if 'prime' in prompts_data.get('available', []) else []),
        on_complete=prompts_data.get('onComplete', ['self-reflect'] if 'self-reflect' in prompts_data.get('available', []) else []),
        available=prompts_data.get('available', []),
        auto_trigger=prompts_data.get('autoTrigger', {
            'afterWrite': ['verify-changes'],
            'afterError': ['rca']
        })
    )
    
    # Handle hooks section with defaults
    hooks_data = config_data.get('hooks', [])
    if isinstance(hooks_data, dict):
        hooks_data = hooks_data.get('postToolUse', [])
    hooks = [HookConfig(matcher=h.get('matcher', 'write'), command=h.get('command', 'pytest tests/smoke/ -x --tb=line')) for h in hooks_data]
    
    # Add default hook if none specified
    if not hooks and config_data.get('tools') and 'fs_write' in config_data.get('tools', []):
        hooks = [HookConfig(matcher='write', command='pytest tests/smoke/ -x --tb=line')]
    
    return AgentConfig(
        name=config_data.get('name', 'unnamed-agent'),
        description=config_data.get('description', 'Agent description not provided'),
        prompt=config_data.get('prompt', ''),
        model=config_data.get('model', 'claude-3-5-sonnet-20241022'),
        version=config_data.get('version', '1.0.0'),
        tools=config_data.get('tools', []),
        allowed_tools=config_data.get('allowedTools', config_data.get('tools', [])),
        resources=config_data.get('resources', []),
        tools_settings=config_data.get('toolsSettings', {}),
        prompts=prompts,
        hooks=hooks
    )

def validate_agent_config(config: AgentConfig) -> List[str]:
    """Validate agent configuration and return list of errors."""
    errors = []
    
    # Validate name
    if not config.name or not config.name.replace('-', '').replace('_', '').isalnum():
        errors.append("Agent name must be alphanumeric with hyphens/underscores only")
    
    # Validate description
    if not config.description or len(config.description.strip()) < 10:
        errors.append("Agent description must be at least 10 characters")
        
    # Validate version format
    if not validate_semver(config.version):
        errors.append(f"Invalid semantic version: {config.version}")
    
    # Validate tools
    for tool in config.tools:
        if not tool.replace('_', '').replace('-', '').isalnum():
            errors.append(f"Invalid tool name: {tool}")
    
    # Validate model name
    if not config.model or len(config.model.strip()) < 3:
        errors.append("Model name is required and must be at least 3 characters")
    
    return errors
