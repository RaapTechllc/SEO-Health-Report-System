from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
import logging
from datetime import datetime
from pathlib import Path
import os

@dataclass
class RBTAnalysis:
    agent_name: str
    confidence_score: int  # 1-10
    roses: List[str]      # What worked well
    buds: List[str]       # Opportunities for improvement
    thorns: List[str]     # What didn't work
    proposed_changes: Dict[str, Any]  # JSON patch for agent config

@dataclass
class EvolutionRecord:
    timestamp: str
    agent_name: str
    change_type: str      # "prompt_update", "resource_add", "tool_setting"
    confidence_score: int
    changes_applied: Dict[str, Any]
    verification_result: str  # "passed", "failed", "rolled_back"

class EvolutionEngine:
    def __init__(self, evolution_dir: str = None):
        if evolution_dir is None:
            evolution_dir = os.path.expanduser("~/.kiro/evolution")
        self.evolution_dir = Path(evolution_dir)
        self.evolution_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def analyze_session(self, agent_name: str, session_log: str) -> RBTAnalysis:
        """Analyze agent session using RBT framework."""
        # This would typically use Claude API to analyze the session
        # For now, return a mock analysis
        
        self.logger.info(f"Analyzing session for {agent_name}")
        
        # Mock RBT analysis - in real implementation, this would use Claude
        roses = ["Successfully completed task", "Good context management"]
        buds = ["Could improve error handling", "Add more validation"]
        thorns = ["Lost context during handoff", "Slow response time"]
        
        # Mock confidence score based on session success
        confidence = 7 if "error" not in session_log.lower() else 5
        
        # Mock proposed changes
        proposed_changes = {}
        if confidence >= 8:
            proposed_changes = {
                "resources": {"add": ["file://.kiro/specs/**/*.md"]},
                "toolsSettings": {"read": {"allowedPaths": ["./tests/**"]}}
            }
        
        return RBTAnalysis(
            agent_name=agent_name,
            confidence_score=confidence,
            roses=roses,
            buds=buds,
            thorns=thorns,
            proposed_changes=proposed_changes
        )
    
    def generate_patch(self, analysis: RBTAnalysis) -> Optional[Dict]:
        """Generate JSON patch if confidence >= 8."""
        if analysis.confidence_score < 8:
            self.logger.info(f"Confidence {analysis.confidence_score} < 8, skipping patch generation")
            return None
        
        # Validate proposed changes target only allowed fields
        allowed_fields = {"prompt", "resources", "toolsSettings"}
        patch = {}
        
        for field, changes in analysis.proposed_changes.items():
            if field in allowed_fields:
                patch[field] = changes
            else:
                self.logger.warning(f"Skipping disallowed field in patch: {field}")
        
        if patch:
            self.logger.info(f"Generated patch for {analysis.agent_name}: {patch}")
            return patch
        
        return None
    
    def apply_evolution(self, agent_name: str, patch: Dict) -> bool:
        """Apply patch to agent config with backup."""
        # Sanitize agent name to prevent path traversal
        agent_name = os.path.basename(agent_name).replace('..', '')
        if not agent_name.replace('-', '').replace('_', '').isalnum():
            self.logger.error(f"Invalid agent name: {agent_name}")
            return False
            
        agent_config_path = Path(f".kiro/agents/{agent_name}.json")
        backup_path = Path(f".kiro/backups/{agent_name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Validate paths are within expected directories
        try:
            agent_config_path = agent_config_path.resolve()
            backup_path = backup_path.resolve()
            if not str(agent_config_path).startswith(str(Path(".kiro/agents").resolve())):
                self.logger.error("Agent config path outside allowed directory")
                return False
        except Exception as e:
            self.logger.error(f"Path validation failed: {e}")
            return False
        
        if not agent_config_path.exists():
            self.logger.error(f"Agent config not found: {agent_config_path}")
            return False
        
        try:
            # Create backup directory with secure permissions
            backup_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            
            # Load current config with JSON validation
            with open(agent_config_path, 'r') as f:
                config = json.load(f)
            
            # Basic JSON structure validation
            if not isinstance(config, dict):
                raise ValueError("Config must be a JSON object")
            
            # Create backup with secure permissions
            with open(backup_path, 'w') as f:
                json.dump(config, f, indent=2)
            os.chmod(backup_path, 0o600)  # Owner read/write only
            self.logger.info(f"Created backup: {backup_path}")
            
            # Apply patch
            for field, changes in patch.items():
                if field in config:
                    if isinstance(changes, dict) and "add" in changes:
                        # Handle add operations
                        if isinstance(config[field], list):
                            config[field].extend(changes["add"])
                        elif isinstance(config[field], dict):
                            config[field].update(changes["add"])
                    else:
                        config[field] = changes
                else:
                    config[field] = changes
            
            # Write updated config
            with open(agent_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Applied evolution to {agent_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply evolution: {e}")
            return False
    
    def rollback(self, agent_name: str) -> bool:
        """Restore agent config from most recent backup."""
        backup_dir = Path(f".kiro/backups")
        agent_config_path = Path(f".kiro/agents/{agent_name}.json")
        
        if not backup_dir.exists():
            self.logger.error("No backup directory found")
            return False
        
        # Find most recent backup
        backups = list(backup_dir.glob(f"{agent_name}-*.json"))
        if not backups:
            self.logger.error(f"No backups found for {agent_name}")
            return False
        
        latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
        
        try:
            # Restore from backup
            with open(latest_backup, 'r') as f:
                config = json.load(f)
            
            with open(agent_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Rolled back {agent_name} from {latest_backup}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback: {e}")
            return False
    
    def log_evolution(self, record: EvolutionRecord) -> None:
        """Log evolution to ~/.kiro/evolution/[agent]-evolution.md."""
        log_path = self.evolution_dir / f"{record.agent_name}-evolution.md"
        
        # Create evolution entry
        entry = f"""
## Evolution #{datetime.now().strftime('%Y%m%d_%H%M%S')} - {record.timestamp}

### Change Type: {record.change_type}
### Confidence Score: {record.confidence_score}/10

### Changes Applied
```json
{json.dumps(record.changes_applied, indent=2)}
```

### Verification Result: {record.verification_result.upper()}

---
"""
        
        try:
            # Append to evolution log
            with open(log_path, 'a') as f:
                if log_path.stat().st_size == 0:
                    f.write(f"# Evolution Log: {record.agent_name}\n")
                f.write(entry)
            
            self.logger.info(f"Logged evolution for {record.agent_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to log evolution: {e}")
