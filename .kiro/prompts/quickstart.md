# Project Quick Start Wizard

## Welcome
This wizard bootstraps a new project with the orchestrator template.

## What I will create or verify
- `.kiro/steering/*` - Project context files
- `.kiro/prompts/*` - Custom prompts
- `docs/` - Documentation structure
- `README.md` - Project readme
- Basic project scaffold

## Step 1 — Gather inputs
Ask:
1) Project name
2) Tech stack (or confirm defaults)
3) Database choice (if applicable)

## Step 2 — Repository hygiene check
**CRITICAL**: Before scaffolding, verify:
1. `.gitignore` exists with appropriate entries
2. If `.gitignore` is missing, CREATE IT FIRST
3. If `node_modules/` or build artifacts are committed, STOP and warn user

## Step 3 — Scaffold commands
Provide the exact commands to run, in order.
Use safe defaults appropriate for the chosen stack.

## Step 4 — Write baseline docs
Ensure these exist with project-specific content:
- `.kiro/steering/product.md` - Fill in product overview
- `.kiro/steering/tech.md` - Fill in tech stack
- `.kiro/steering/structure.md` - Fill in project structure
- `docs/prd/[project-name].md` - Product requirements
- `README.md` - Setup, run, and usage instructions

## Step 5 — Minimal working demo
Create a minimal route/endpoint that:
- Demonstrates the core concept
- Runs without external dependencies (where possible)

## Step 6 — Add test guardrail
Create a basic test that:
- Verifies the app starts
- Checks the primary path works

## Output
- A checklist of what was created
- Any missing items
- The next command to run
