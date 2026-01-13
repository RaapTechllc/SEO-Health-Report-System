# Handoff Completion Prompt

You are responsible for completing handoff tasks and providing results back to the requesting agent.

## Task
Execute the delegated task according to the handoff specifications and document results.

## Completion Process

### Step 1: Read Handoff File
Load and parse the handoff file:
- Understand task requirements
- Review success criteria
- Note expected output format
- Gather context from summary

### Step 2: Execute Task
Perform the requested work:
- Follow task description precisely
- Use relevant files as specified
- Apply your specialized expertise
- Document your process and findings

### Step 3: Validate Against Criteria
Check your work against success criteria:
- ✅ Each criterion met
- ✅ Output format matches expectations
- ✅ Quality standards achieved

### Step 4: Document Results
Update the handoff file with comprehensive results:

```markdown
## Results

### Summary
[Brief overview of what was accomplished]

### Detailed Findings
[Comprehensive results organized by category]

### Deliverables
[List of files created, modified, or analyzed]

### Success Criteria Status
- [x] Criterion 1: Completed successfully
- [x] Criterion 2: Completed with notes
- [ ] Criterion 3: Partially completed (explain why)

### Recommendations
[Next steps or follow-up actions needed]

### Notes
[Any important context for the requesting agent]

**Completed**: [ISO timestamp]
**Duration**: [time spent]
**Status**: completed
```

## Quality Standards

### Result Documentation
- **Comprehensive**: Cover all aspects of the task
- **Organized**: Use clear headings and structure
- **Actionable**: Provide specific next steps
- **Traceable**: Reference files and line numbers where relevant

### Deliverable Standards
- **Code**: Follow project coding standards
- **Documentation**: Clear, concise, properly formatted
- **Analysis**: Data-driven with supporting evidence
- **Recommendations**: Prioritized and feasible

## Handoff Status Updates

Update the metadata section:
```markdown
- **Status**: completed
- **Completed By**: [your-agent-name]
- **Completion Time**: [ISO timestamp]
- **Duration**: [time-spent]
```

## Error Handling

### If Task Cannot Be Completed
Document partial completion:
```markdown
## Results

### Status: Partially Completed

### What Was Accomplished
[List completed portions]

### Blockers Encountered
[Specific issues that prevented full completion]

### Recommendations
[How to resolve blockers or alternative approaches]

**Status**: failed
**Reason**: [specific blocker description]
```

### If Requirements Are Unclear
Request clarification:
```markdown
## Results

### Status: Clarification Needed

### Questions
1. [Specific question about requirement]
2. [Another unclear aspect]

### Assumptions Made
[What you assumed to proceed]

### Partial Results
[Any work completed based on assumptions]

**Status**: pending_clarification
```

## Validation Checklist

Before marking handoff complete:
- [ ] All success criteria addressed
- [ ] Expected output format followed
- [ ] Results are comprehensive and actionable
- [ ] Files are properly organized and accessible
- [ ] Handoff status updated correctly

## Communication Protocol

### Success Case
- Mark status as "completed"
- Provide comprehensive results
- Include any follow-up recommendations

### Failure Case  
- Mark status as "failed" with specific reason
- Document what was attempted
- Suggest alternative approaches or resources needed

### Partial Success
- Mark status as "partially_completed"
- Clearly document what was and wasn't accomplished
- Provide path forward for completion
