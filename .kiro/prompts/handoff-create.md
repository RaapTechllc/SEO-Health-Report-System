# Handoff Creation Prompt

You are responsible for creating structured handoff files when delegating tasks to specialist agents.

## Task
Generate a properly formatted handoff file that provides complete context for the target agent.

## Handoff Template

Use this exact format for all handoffs:

```markdown
# Handoff: [target-agent] - [task-title]

## Metadata
- **Created**: [ISO timestamp]
- **Source Agent**: [your-agent-name]
- **Target Agent**: [specialist-agent-name]
- **Status**: pending

## Task Description
[Clear, specific description of what needs to be done]

## Relevant Files
- [file-path-1]
- [file-path-2]
- [file-path-n]

## Expected Output
[Specific description of deliverable format and content]

## Success Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
- [ ] [Measurable criterion 3]

## Context Summary
[Essential background information the specialist needs]

## Results
<!-- Filled by target agent on completion -->
```

## Handoff Quality Checklist

### Required Elements
- ✅ **Task Description**: Clear, actionable, specific
- ✅ **Relevant Files**: All files the specialist needs access to
- ✅ **Expected Output**: Format, content, delivery method
- ✅ **Success Criteria**: Measurable, testable outcomes
- ✅ **Context Summary**: Essential background without overwhelming detail

### Quality Standards
- **Clarity**: A new agent could understand and execute
- **Completeness**: No missing information that would cause delays
- **Specificity**: Avoid vague terms like "improve" or "optimize"
- **Measurability**: Success criteria can be objectively verified

## Specialist Agent Mapping

Choose the right specialist for each task type:

| Task Type | Target Agent | Expertise |
|-----------|--------------|-----------|
| Code review, refactoring, security | `code-surgeon` | Code quality, security, performance |
| Test creation, coverage analysis | `test-architect` | Testing strategies, quality assurance |
| Database design, queries, optimization | `db-wizard` | Data modeling, SQL, performance |
| UI components, styling, accessibility | `frontend-designer` | React, CSS, user experience |
| CI/CD, deployment, infrastructure | `devops-automator` | DevOps, automation, deployment |
| Documentation, guides, API docs | `doc-smith` | Technical writing, documentation |

## Example Handoffs

### Code Review Handoff
```markdown
# Handoff: code-surgeon - Review Score Calculator

## Task Description
Review the calculate_scores.py module for:
1. Security vulnerabilities
2. Performance issues  
3. Code quality improvements

## Relevant Files
- seo-health-report/scripts/calculate_scores.py
- tests/unit/test_calculate_scores.py

## Expected Output
Structured review with findings categorized by severity.

## Success Criteria
- [ ] All security issues identified
- [ ] Performance bottlenecks flagged
- [ ] At least 3 actionable improvements suggested

## Context Summary
This module calculates composite SEO scores using weighted averages.
Recent changes added AI visibility scoring (35% weight).
```

## Validation Rules
Before creating handoff:
1. **Verify target agent exists** in `.kiro/agents/`
2. **Confirm file paths** are accurate and accessible
3. **Test success criteria** are measurable
4. **Ensure context** is sufficient but not overwhelming

## File Naming Convention
`[timestamp]-[target-agent]-[task-slug].md`

Example: `20240112_143022-code-surgeon-review-score-calc.md`
