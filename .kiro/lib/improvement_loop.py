from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
from pathlib import Path
import json

from binding_system import BindingSystem, LifecycleEvent
from evolution_engine import EvolutionEngine, RBTAnalysis, EvolutionRecord
from verification_layer import VerificationLayer
from handoff_protocol import HandoffProtocol

@dataclass
class LoopIteration:
    iteration_number: int
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    phases_completed: List[str] = None
    evolution_applied: bool = False
    verification_passed: bool = False
    performance_improvement: Optional[float] = None

class ImprovementLoop:
    def __init__(self, evolution_dir: str = None):
        self.binding_system = BindingSystem()
        self.evolution_engine = EvolutionEngine(evolution_dir)
        self.verification_layer = VerificationLayer()
        self.handoff_protocol = HandoffProtocol()
        self.logger = logging.getLogger(__name__)
        
        # Loop history tracking
        if evolution_dir is None:
            evolution_dir = Path.home() / ".kiro" / "evolution"
        else:
            evolution_dir = Path(evolution_dir)
        self.loop_history_path = evolution_dir / "loop-history.md"
        evolution_dir.mkdir(parents=True, exist_ok=True)
    
    def execute_improvement_loop(self, agent_name: str, agent_config: dict, 
                                session_log: str = "", iteration: int = 1) -> LoopIteration:
        """Execute complete improvement loop: prime → execute → verify → reflect → apply → verify-evolution → log."""
        
        loop_iteration = LoopIteration(
            iteration_number=iteration,
            agent_name=agent_name,
            start_time=datetime.now(),
            phases_completed=[]
        )
        
        self.logger.info(f"Starting improvement loop iteration {iteration} for {agent_name}")
        
        try:
            # Parse agent configuration
            parsed_config = self.binding_system.parse_config(agent_config)
            
            # Phase 1: Prime (Session Start)
            self.logger.info("Phase 1: Prime - Invoking session start prompts")
            prime_prompts = self.binding_system.invoke_prompts(
                LifecycleEvent.SESSION_START, agent_name, parsed_config
            )
            loop_iteration.phases_completed.append("prime")
            
            # Phase 2: Execute (Task Execution)
            self.logger.info("Phase 2: Execute - Task execution phase")
            # In real implementation, this would execute the actual task
            # For now, we simulate successful execution
            loop_iteration.phases_completed.append("execute")
            
            # Phase 3: Verify (Change Verification)
            self.logger.info("Phase 3: Verify - Running verification tests")
            verification_result = self.verification_layer.run_smoke_tests()
            if verification_result.status != "pass":
                self.logger.warning("Verification failed, triggering RCA")
                self.verification_layer.trigger_rca(str(verification_result.failures))
            loop_iteration.phases_completed.append("verify")
            
            # Phase 4: Reflect (Self-Analysis)
            self.logger.info("Phase 4: Reflect - Analyzing session performance")
            rbt_analysis = self.evolution_engine.analyze_session(agent_name, session_log)
            
            # Invoke self-reflect prompts
            reflect_prompts = self.binding_system.invoke_prompts(
                LifecycleEvent.TASK_COMPLETE, agent_name, parsed_config
            )
            loop_iteration.phases_completed.append("reflect")
            
            # Phase 5: Apply (Conditional Evolution)
            if rbt_analysis.confidence_score >= 8:
                self.logger.info("Phase 5: Apply - High confidence, applying evolution")
                patch = self.evolution_engine.generate_patch(rbt_analysis)
                
                if patch:
                    success = self.evolution_engine.apply_evolution(agent_name, patch)
                    if success:
                        loop_iteration.evolution_applied = True
                        
                        # Phase 6: Verify Evolution
                        self.logger.info("Phase 6: Verify Evolution - Testing evolved agent")
                        verification_passed = self.verification_layer.verify_evolution(
                            agent_name, "standardized test task"
                        )
                        loop_iteration.verification_passed = verification_passed
                        
                        if not verification_passed:
                            self.logger.warning("Evolution verification failed, rolling back")
                            self.evolution_engine.rollback(agent_name)
                            loop_iteration.evolution_applied = False
                        
                        loop_iteration.phases_completed.append("verify-evolution")
                    
                loop_iteration.phases_completed.append("apply")
            else:
                self.logger.info(f"Phase 5: Apply - Low confidence ({rbt_analysis.confidence_score}), skipping evolution")
            
            # Phase 7: Log (Record Results)
            self.logger.info("Phase 7: Log - Recording loop results")
            self._log_loop_iteration(loop_iteration, rbt_analysis)
            loop_iteration.phases_completed.append("log")
            
            loop_iteration.end_time = datetime.now()
            
            # Update agent version if evolution was successful
            if loop_iteration.evolution_applied and loop_iteration.verification_passed:
                self._increment_agent_version(agent_name)
            
            self.logger.info(f"Improvement loop completed: {len(loop_iteration.phases_completed)} phases")
            return loop_iteration
            
        except Exception as e:
            self.logger.error(f"Improvement loop failed: {e}")
            loop_iteration.end_time = datetime.now()
            return loop_iteration
    
    def _log_loop_iteration(self, iteration: LoopIteration, analysis: RBTAnalysis) -> None:
        """Log iteration to loop history file."""
        
        duration = (iteration.end_time or datetime.now()) - iteration.start_time
        
        entry = f"""
## Loop Iteration #{iteration.iteration_number} - {iteration.start_time.isoformat()}

### Agent: {iteration.agent_name}
### Duration: {duration.total_seconds():.2f} seconds
### Phases Completed: {' → '.join(iteration.phases_completed)}

### Evolution Status
- **Applied**: {'Yes' if iteration.evolution_applied else 'No'}
- **Verified**: {'Yes' if iteration.verification_passed else 'No'}
- **Confidence**: {analysis.confidence_score}/10

### Performance
- **Improvement**: {iteration.performance_improvement or 'N/A'}
- **Status**: {'Success' if iteration.verification_passed else 'No Change'}

### RBT Summary
- **Roses**: {len(analysis.roses)} items
- **Buds**: {len(analysis.buds)} items  
- **Thorns**: {len(analysis.thorns)} items

---
"""
        
        try:
            with open(self.loop_history_path, 'a') as f:
                if self.loop_history_path.stat().st_size == 0:
                    f.write("# Improvement Loop History\n\n")
                f.write(entry)
            
            self.logger.info(f"Logged loop iteration to {self.loop_history_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to log loop iteration: {e}")
    
    def _increment_agent_version(self, agent_name: str) -> None:
        """Increment agent version after successful evolution."""
        agent_config_path = Path(f".kiro/agents/{agent_name}.json")
        
        if not agent_config_path.exists():
            self.logger.warning(f"Agent config not found for version increment: {agent_config_path}")
            return
        
        try:
            with open(agent_config_path, 'r') as f:
                config = json.load(f)
            
            # Parse current version and increment patch
            current_version = config.get('version', '1.0.0')
            parts = current_version.split('.')
            if len(parts) == 3:
                major, minor, patch = parts
                new_version = f"{major}.{minor}.{int(patch) + 1}"
            else:
                new_version = "1.0.1"
            
            config['version'] = new_version
            
            with open(agent_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Incremented {agent_name} version: {current_version} → {new_version}")
            
        except Exception as e:
            self.logger.error(f"Failed to increment agent version: {e}")
    
    def get_loop_metrics(self, agent_name: str = None) -> Dict[str, Any]:
        """Get cumulative improvement metrics."""
        # This would analyze the loop history file and return metrics
        # For now, return mock metrics
        
        return {
            "total_iterations": 5,
            "successful_evolutions": 3,
            "average_confidence": 7.2,
            "performance_improvements": ["+15%", "+8%", "+12%"],
            "most_common_improvements": ["resource_access", "tool_settings"],
            "agent_versions": {"orchestrator": "1.0.3", "code-surgeon": "1.0.2"}
        }
