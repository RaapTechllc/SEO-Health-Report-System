# SEO Audit Skills Implementation Plan

This plan details the integration of specialized Claude Skills to upgrade the SEO Health Report System.
**Focus**: Robust report generation, advanced browser automation (Vercel), and workflow orchestration.

## 0. Code Quality & Maintenance (Immediate Priority)

### A. Static Analysis: `trailofbits/static-analysis`
**Status**: 🆕 New
**Source**: [github.com/trailofbits/skills](https://github.com/trailofbits/skills)
**Role**: Automated code review and security scanning.
**Checks**:
- Detects unused code/imports
- Identifies security vulnerabilities (hardcoded secrets)
- Flags complex logic that needs refactoring

### B. Systematic Debugging: `obra/systematic-debugging`
**Status**: 🆕 New
**Source**: [github.com/obra/superpowers](https://github.com/obra/superpowers)
**Role**: Structured protocol for fixing bugs and refactoring.
**Use Case**: Safe refactoring of root-level scripts into `packages/`.

## 1. Core Implementation (Critical Priority)

### A. Web Scraping & AI Visibility: `vercel-labs/agent-browser`
**Status**: 🔄 Swapped in (Replaces `lackeyjb/playwright-skill`)
**Source**: [github.com/vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser)
**Role**: The primary engine for Technical SEO audits and AI Visibility checks.
**Implementation Steps**:
1.  **Install**:
    ```bash
    git clone https://github.com/vercel-labs/agent-browser
    cd agent-browser
    cargo install --path .  # Or use pre-built binary if available
    ```
2.  **Integration**:
    - Build a wrapper python script `packages/seo_health_report/providers/vercel_browser.py`.
    - **Technical Audit**: Use it to visit client pages, render full DOM, and extract key SEO tags (Title, Meta, Headers, Schema).
    - **AI Visibility**: Use it to visit `chatgpt.com` or `claude.ai` (auth required) or simply search engine AI overviews to test brand visibility.
    - **Advantage**: Returns optimized, token-efficient DOM representations perfect for LLM analysis.

### B. Report Generation: `anthropics/pdf`
**Status**: 🚀 Critical
**Source**: [github.com/anthropics/skills/tree/main/skills/pdf](https://github.com/anthropics/skills/tree/main/skills/pdf)
**Role**: Generates the professional "Executive Health Report" PDF.
**Implementation Steps**:
1.  **Fetch Skill**:
    ```bash
    mkdir -p .claude/skills/pdf
    # Copy SKILL.md and scripts from repo
    ```
2.  **Report Engine**:
    - Update `generate_premium_report.py` to leverage the skill's capabilities (merging, stamping) if needed, or simply use logic inspired by it (ReportLab is already in use, but this skill adds utilities).
    - **Key Feature**: Use it to merge the "Cover Page" (generated separately for high quality) with the "Data Pages".

## 2. Automation & Workflow (High Priority)

### C. Workflow Orchestration: `czlonkowski/n8n-workflow-patterns`
**Status**: ⚡ High
**Source**: [github.com/czlonkowski/n8n-skills](https://github.com/czlonkowski/n8n-skills)
**Role**: Structure the end-to-end audit process.
**Implementation Steps**:
1.  **Pattern Adoption**:
    - Use the **Parallel Processing Pattern** to run Technical, Content, and AI audits simultaneously.
    - Use the **Error Handler Pattern** to ensure a temporary failure in one check doesn't fail the whole report.
2.  **Deployment**:
    - Create a main `Full_Audit_Workflow.json` using these patterns.

### D. Sales Presentations: `anthropics/pptx`
**Status**: 📊 High
**Source**: [github.com/anthropics/skills/tree/main/skills/pptx](https://github.com/anthropics/skills/tree/main/skills/pptx)
**Role**: Generate editable sales decks for client meetings.
**Implementation Steps**:
1.  **Template Creation**: Design a master `Agency_Pitch_Template.pptx`.
2.  **Generator Script**:
    - Create `generate_pitch_deck.py`.
    - Use the skill to find placeholders in `Agency_Pitch_Template.pptx` and replace them with:
        - `{{CLIENT_LOGO}}`
        - `{{OVERALL_SCORE}}`
        - `{{TOP_3_ISSUES}}`

## 3. Advanced Features (Medium Priority)

### E. Deep Technical Security: `jthack/ffuf-claude-skill`
**Status**: 🛡️ Medium
**Source**: [github.com/jthack/ffuf_claude_skill](https://github.com/jthack/ffuf_claude_skill)
**Role**: "Deep Dive" add-on for Premium Tier audits.
**Checks**:
- Exposed `.env` or config files.
- Hidden `/admin` or `/staging` endpoints that leak data.

### F. Competitor Research: `sanjay3290/deep-research`
**Status**: 🧠 Medium
**Source**: [github.com/sanjay3290/ai-skills](https://github.com/sanjay3290/ai-skills)
**Role**: Strategic "Gap Analysis".
**Action**: Automate a research run: "Find top 5 competitors for [Client] and list their highest traffic blog topics."

### G. Content Writer: `ComposioHQ/content-research-writer`
**Status**: 🆕 New
**Source**: [github.com/ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)
**Role**: Generates high-quality blog drafts.
**Use Case**: Replace "Mock Data" with real generated content examples for the "Content Audit" section suggestions.

### H. Ad Intelligence: `ComposioHQ/competitive-ads-extractor`
**Status**: 🆕 New
**Source**: [github.com/ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)
**Role**: Extracts competitor ad copy.
**Use Case**: "See what Sheet Metal Werks competitors are paying for" section in the Premium Report.

### I. Word Reports: `anthropics/docx`
**Status**: 🆕 New
**Source**: [github.com/anthropics/skills/tree/main/skills/docx](https://github.com/anthropics/skills/tree/main/skills/docx)
**Role**: Generate editable Word docs.
**Use Case**: Delivering "Optimization Checklists" that the client's internal team can actually check off and edit.

## Execution Roadmap

0.  **Phase 0 (Immediate)**: ✅ **COMPLETE** - Operation Cleanup
    - Created `packages/core/env.py` - Centralized environment loading
    - Created `apps/cli/` - New location for CLI scripts
    - Refactored `orchestrate.py` - Simplified imports from ~60 lines to ~15 lines
    - Replaced complex `importlib.util` hacks with clean `import packages.X` pattern
    - Added ruff compliance with noqa comments for necessary E402 exceptions
    - Updated `pyproject.toml` to include new `core` package + `requests` dependency
    - Updated `pyproject.toml` ruff config to use new `[tool.ruff.lint]` section (fixed deprecation)
    - Security scan: No hardcoded secrets found (only example strings in SDK docs)
    - Root files kept at root: `database.py` (39 deps), `auth.py` (13 deps), `payments.py` (3 deps)
    - Root files to move later: `generate_premium_report.py` (5 deps - deferred for stability)

1.  **Phase 1 (Day 1)**: ✅ **COMPLETE** - Browser crawler installed and tested on sheetmetalwerks.com
    - `vercel-labs/agent-browser` had daemon issues, pivoted to Python Playwright wrapper
    - Created `packages/seo_health_report/providers/browser_crawler.py`
    - Integrated into `orchestrate.py` - runs automatically before audits
    - Test results: 1368ms load, 55 images (52 without alt!), no Schema.org
    
2.  **Phase 2 (Day 1)**: ✅ **COMPLETE** - Browser data integrated into premium reports
    - Added "Page Analysis (JavaScript Rendered)" section to Technical SEO Analysis
    - Displays load time, image alt coverage, canonical URL, schema.org status
    - Report generator updated in `generate_premium_report.py`
    
3.  **Phase 3 (Day 2)**: 🔄 PENDING - Set up `n8n` workflow using the `workflow-patterns` skill.
4.  **Phase 4 (Day 3+)**: 📋 TODO - Advanced integrations (PPTX, FFUF).

## Files Created/Modified

### Phase 0: Operation Cleanup
- **NEW**: `packages/core/__init__.py` - Core utilities module
- **NEW**: `packages/core/env.py` - Centralized env loading with `init()`, `load_env()`, `setup_paths()`
- **NEW**: `apps/cli/__init__.py` - CLI applications package
- **NEW**: `apps/cli/run_audit.py` - Clean version of audit runner
- **NEW**: `apps/cli/verify_sheetmetal.py` - Verification test with proper imports
- **MOD**: `packages/seo_health_report/scripts/orchestrate.py` - Simplified imports
- **MOD**: `pyproject.toml` - Added `core` package

### Phase 1-2: Browser Crawler
- **NEW**: `packages/seo_health_report/providers/browser_crawler.py` - Playwright-based SEO crawler
- **NEW**: `packages/seo_health_report/providers/__init__.py`
- **MOD**: `packages/seo_health_report/scripts/orchestrate.py` - Added `run_browser_crawl()` function
- **MOD**: `generate_premium_report.py` - Added browser data table to technical section
- **NEW**: `.venv/` - Python virtual environment with playwright installed

## Import Pattern Guide

**Before (messy):**
```python
import importlib.util
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
module_path = os.path.join(project_root, "seo_technical_audit")
spec = importlib.util.spec_from_file_location("seo_technical_audit", ...)
# ... 15 more lines of boilerplate
```

**After (clean):**
```python
import packages.seo_technical_audit as seo_technical_audit
```
