# Project Primer

Load all project context and provide a comprehensive overview of the SEO Health Report System.

## Non-negotiables
1. Preserve scoring weights (Technical 0.30, Content 0.35, AI 0.35) and grade mapping.
2. AI Visibility audit is required and must not be skipped.
3. Never hardcode or expose API keys; use documented fallback chains.
4. Use hyphenated package aliasing via importlib; do not exec() source files.
5. Console output must be ASCII-only for Windows compatibility.
6. Errors must be logged or returned with meaningful defaults; no silent failures.
7. Frontend score/AI colors must follow `score-*` and `ai-*` semantics when touching UI.

## Context Files to Load
- `.kiro/steering/project-overview.md`
- `.kiro/steering/seo-health-report.md`
- `.kiro/steering/ai-visibility-audit.md`
- `.kiro/steering/seo-technical-audit.md`
- `.kiro/steering/seo-content-authority.md`
- `.kiro/steering/tech.md`
- `.kiro/steering/frontend.md`
- `.kiro/steering/coding-standards.md`
- `.kiro/steering/validation.md`
- `README.md`
- `docs/PLAN.md`
- `docs/PROGRESS.md`

## Project Summary
Provide a concise overview covering:
1. **Purpose**: What this project does
2. **Tech Stack**: Key technologies used
3. **Current Status**: What's been completed
4. **Next Steps**: What needs to be done

## Key Files
List the most important files for understanding the codebase (orchestrator, scoring, report assembly, AI visibility queries, and frontend dashboard).

## Known Issues
Note any bugs, technical debt, or blockers.

## Demo Path
Describe the critical user journey for generating a report end-to-end.
