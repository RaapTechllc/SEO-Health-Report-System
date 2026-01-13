from dataclasses import dataclass
from typing import List, Optional
import json
import logging
import os
from datetime import datetime
from pathlib import Path

@dataclass
class HandoffFile:
    timestamp: str
    source_agent: str
    target_agent: str
    task_description: str
    relevant_files: List[str]
    expected_output: str
    success_criteria: List[str]
    context_summary: str
    status: str           # "pending", "in_progress", "completed", "failed"
    results: Optional[str] = None

class HandoffProtocol:
    def __init__(self, handoffs_dir: str = ".kiro/handoffs"):
        self.handoffs_dir = Path(handoffs_dir)
        self.handoffs_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def create_handoff(self, source: str, target: str, task: str, 
                      relevant_files: List[str] = None,
                      expected_output: str = "",
                      success_criteria: List[str] = None,
                      context_summary: str = "") -> str:
        """Create handoff file and return path."""
        # Validate inputs to prevent path traversal
        if '..' in source or '..' in target or '/' in source or '\\' in target:
            raise ValueError("Agent names cannot contain path separators or '..'")
            
        source = os.path.basename(source)
        target = os.path.basename(target)
        
        if not source.replace('-', '').replace('_', '').isalnum():
            raise ValueError(f"Invalid source agent name: {source}")
        if not target.replace('-', '').replace('_', '').isalnum():
            raise ValueError(f"Invalid target agent name: {target}")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_slug = ''.join(c for c in task.lower().replace(" ", "-") if c.isalnum() or c == '-')[:20]
        filename = f"{timestamp}-{target}-{task_slug}.md"
        handoff_path = self.handoffs_dir / filename
        
        # Validate path is within handoffs directory
        try:
            handoff_path = handoff_path.resolve()
            if not str(handoff_path).startswith(str(self.handoffs_dir.resolve())):
                raise ValueError("Handoff path outside allowed directory")
        except Exception as e:
            self.logger.error(f"Path validation failed: {e}")
            raise
        
        handoff = HandoffFile(
            timestamp=datetime.now().isoformat(),
            source_agent=source,
            target_agent=target,
            task_description=task,
            relevant_files=relevant_files or [],
            expected_output=expected_output,
            success_criteria=success_criteria or [],
            context_summary=context_summary,
            status="pending"
        )
        
        # Generate markdown content
        content = f"""# Handoff: {target} - {task}

## Metadata
- **Created**: {handoff.timestamp}
- **Source Agent**: {handoff.source_agent}
- **Target Agent**: {handoff.target_agent}
- **Status**: {handoff.status}

## Task Description
{handoff.task_description}

## Relevant Files
{chr(10).join(f"- {file}" for file in handoff.relevant_files)}

## Expected Output
{handoff.expected_output}

## Success Criteria
{chr(10).join(f"- [ ] {criteria}" for criteria in handoff.success_criteria)}

## Context Summary
{handoff.context_summary}

## Results
<!-- Filled by target agent on completion -->
"""
        
        try:
            with open(handoff_path, 'w') as f:
                f.write(content)
            
            self.logger.info(f"Created handoff: {handoff_path}")
            return str(handoff_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create handoff: {e}")
            raise
    
    def read_handoff(self, path: str) -> HandoffFile:
        """Read and parse handoff file."""
        handoff_path = Path(path)
        
        if not handoff_path.exists():
            raise FileNotFoundError(f"Handoff file not found: {path}")
        
        try:
            with open(handoff_path, 'r') as f:
                content = f.read()
            
            # Parse markdown content (simplified parsing)
            lines = content.split('\n')
            
            # Extract metadata
            timestamp = ""
            source_agent = ""
            target_agent = ""
            status = "pending"
            
            for line in lines:
                if "**Created**:" in line:
                    timestamp = line.split("**Created**:")[1].strip()
                elif "**Source Agent**:" in line:
                    source_agent = line.split("**Source Agent**:")[1].strip()
                elif "**Target Agent**:" in line:
                    target_agent = line.split("**Target Agent**:")[1].strip()
                elif "**Status**:" in line:
                    status = line.split("**Status**:")[1].strip()
            
            # Extract sections (simplified)
            task_description = self._extract_section(content, "## Task Description")
            expected_output = self._extract_section(content, "## Expected Output")
            context_summary = self._extract_section(content, "## Context Summary")
            results = self._extract_section(content, "## Results")
            
            # Extract file list and criteria (simplified)
            relevant_files = []
            success_criteria = []
            
            return HandoffFile(
                timestamp=timestamp,
                source_agent=source_agent,
                target_agent=target_agent,
                task_description=task_description,
                relevant_files=relevant_files,
                expected_output=expected_output,
                success_criteria=success_criteria,
                context_summary=context_summary,
                status=status,
                results=results if results.strip() else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to read handoff: {e}")
            raise
    
    def complete_handoff(self, path: str, results: str) -> None:
        """Write results and mark handoff complete."""
        handoff_path = Path(path)
        
        try:
            with open(handoff_path, 'r') as f:
                content = f.read()
            
            # Update status and results
            content = content.replace("**Status**: pending", "**Status**: completed")
            content = content.replace("**Status**: in_progress", "**Status**: completed")
            
            # Add results
            results_section = f"\n## Results\n{results}\n\n**Completed**: {datetime.now().isoformat()}"
            content = content.replace("## Results\n<!-- Filled by target agent on completion -->", results_section)
            
            with open(handoff_path, 'w') as f:
                f.write(content)
            
            self.logger.info(f"Completed handoff: {handoff_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to complete handoff: {e}")
            raise
    
    def validate_handoff(self, handoff: HandoffFile) -> List[str]:
        """Validate handoff has all required fields."""
        errors = []
        
        if not handoff.task_description.strip():
            errors.append("Task description is required")
        
        if not handoff.target_agent.strip():
            errors.append("Target agent is required")
        
        if not handoff.source_agent.strip():
            errors.append("Source agent is required")
        
        if not handoff.expected_output.strip():
            errors.append("Expected output is required")
        
        if not handoff.success_criteria:
            errors.append("Success criteria are required")
        
        return errors
    
    def _extract_section(self, content: str, section_header: str) -> str:
        """Extract content between section headers."""
        lines = content.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if line.startswith(section_header):
                in_section = True
                continue
            elif line.startswith('## ') and in_section:
                break
            elif in_section:
                section_content.append(line)
        
        return '\n'.join(section_content).strip()
