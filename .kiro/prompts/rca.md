# Root Cause Analysis

Perform root cause analysis on a bug or issue.

## Usage
When invoked, ask: "What issue should I analyze? Provide a description or issue ID."

## Objective
Find the true root cause of a bug, not just the symptom.
Then propose the smallest safe fix that keeps the demo path stable.

## Non-negotiables
- Do not browse the web unless user asks.
- Reproduce first, then analyze.
- Prefer fixing guardrails and tests over adding complexity.

## Inputs
- Issue description (from user or issue tracker)
- Relevant plan file (if any)
- `DEVLOG.md` entries around the break
- failing tests (Playwright or unit)

## Process

### 1) Reproduce
Write the exact reproduction steps.
If possible, encode them as a Playwright spec.

### 2) Observe
Collect evidence:
- stack traces
- logs
- failing assertions
- inputs that cause failure

### 3) Root cause
Answer:
- What actually caused the failure?
- Why did it escape earlier checks?
- What invariant was violated? (determinism, guardrails, state)

### 4) Fix options
Provide 2–3 options ranked by:
- risk
- speed
- long-term stability

### 5) Prevention
- tests to add
- docs to update
- prompt improvements (if workflow allowed it to slip)

## Output file
Create:
- `docs/rca/issue-[issue-id].md`

## Output Format
- Summary
- Repro steps
- Expected vs actual
- Root cause
- Fix plan (with file paths)
- Test plan
- Rollback plan
- Recommended next steps (do not execute long-running commands)
