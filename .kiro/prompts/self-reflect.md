# Self-Reflection Prompt

You are an AI agent capable of self-improvement through reflection and evolution.

## Task
Analyze your recent session performance using the RBT (Roses-Buds-Thorns) framework and generate evolution recommendations.

## RBT Analysis Framework

### Roses (What Worked Well)
- Identify successful strategies, efficient workflows, good decisions
- Note positive outcomes and effective tool usage
- Highlight moments of clear communication or problem-solving

### Buds (Opportunities for Improvement)  
- Identify areas with potential for growth
- Note inefficiencies that could be optimized
- Suggest new capabilities or resources that would help

### Thorns (What Didn't Work)
- Identify failures, errors, or suboptimal decisions
- Note context losses, communication breakdowns, or tool misuse
- Highlight blockers or frustrations encountered

## Evolution Output Format

Provide your analysis in this exact JSON format:

```json
{
  "agent_name": "your-agent-name",
  "confidence_score": 8,
  "roses": [
    "Successfully completed task X",
    "Efficient use of tool Y"
  ],
  "buds": [
    "Could improve error handling",
    "Add validation for input Z"
  ],
  "thorns": [
    "Lost context during handoff",
    "Tool timeout caused delays"
  ],
  "proposed_changes": {
    "resources": {
      "add": ["file://.kiro/specs/**/*.md"]
    },
    "toolsSettings": {
      "read": {
        "allowedPaths": ["./tests/**"]
      }
    }
  }
}
```

## Confidence Scoring (1-10)
- **8-10**: High confidence - Generate specific JSON patches for immediate application
- **6-7**: Medium confidence - Suggest improvements but don't generate patches  
- **1-5**: Low confidence - Focus on observation and learning

## Evolution Rules
- Only propose changes to: `prompt`, `resources`, `toolsSettings`
- Be specific and actionable in proposed changes
- Focus on measurable improvements
- Consider impact on other agents and workflows

## Next Steps
If confidence >= 8, your proposed changes will be automatically applied and verified.
If confidence < 8, your insights will be logged for future consideration.
