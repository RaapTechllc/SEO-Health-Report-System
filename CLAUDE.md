# SEO Health Report System - Claude Code Instructions

## Project Overview

This is a comprehensive SEO audit system that generates branded health reports by orchestrating technical, content, and AI visibility audits.

## Architecture

```
seo-health-report/           # Master orchestrator (30% weight)
├── ai-visibility-audit/     # AI system presence analysis (35% weight)  
├── seo-technical-audit/     # Technical SEO analysis (30% weight)
├── seo-content-authority/   # Content & authority analysis (35% weight)
```

## Scoring Formula

```
Overall Score = (Technical × 0.30) + (Content × 0.35) + (AI × 0.35)
```

## Available Agents

When working on this project, you can spawn specialized subagents:

### orchestrator
Workflow coordinator for spec-driven development. Manages the SPEC workflow: Requirements → Design → Tasks → Implementation.

**Trigger phrases:** "plan", "new feature", "PRD", "spec"

**Workflow:**
1. Create `.kiro/specs/[feature-name]/requirements.md`
2. Create `.kiro/specs/[feature-name]/design.md` 
3. Create `.kiro/specs/[feature-name]/tasks.md`
4. Execute tasks one at a time

### code-surgeon
Code review, refactoring, and security specialist. Use for:
- Security vulnerability detection (OWASP Top 10)
- Performance optimization
- Technical debt identification
- Refactoring patterns

### test-architect
Testing specialist. Use for:
- Unit tests (pytest)
- Integration tests
- Test data generation
- Coverage analysis

### db-wizard
Database specialist. Use for:
- Schema design
- Query optimization
- Migration strategies

### frontend-designer
UI/UX specialist. Use for:
- React components
- Tailwind CSS styling
- Accessibility (WCAG 2.1 AA)
- Responsive design

### devops-automator
CI/CD and infrastructure. Use for:
- GitHub Actions workflows
- Docker configuration
- Deployment automation

### doc-smith
Documentation specialist. Use for:
- README files
- API documentation
- Code comments

## Key Files

- `run_audit.py` - Main entry point for running SEO audits
- `seo-health-report/scripts/orchestrate.py` - Core orchestration logic
- `.kiro/agents/` - Agent configuration files
- `.kiro/steering/` - Project context and guidelines
- `.kiro/specs/` - Feature specifications

## Progress Tracking

Check `docs/PROGRESS.md` for current project status.
Check `docs/PLAN.md` for the development roadmap.

## Commands

```bash
# Run an SEO audit
python run_audit.py --url https://example.com --company "Example Co"

# Run tests
pytest tests/

# Check for issues
python -m ruff check .
```
