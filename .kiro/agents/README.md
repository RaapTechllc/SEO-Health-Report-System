# Kiro Custom Agents

Swiss Army knife agents for development workflows. Each agent is specialized for a specific domain with curated tools, permissions, and context.

## 🧬 Self-Evolution Protocol

All agents are equipped with self-healing and continuous improvement capabilities:

- **Roses-Buds-Thorns (RBT) Reflection** - End-of-session analysis
- **Automatic Error Diagnosis** - Self-healing on failures
- **Evolution Logging** - Persistent learning across projects
- **1% Better Every Session** - Compound improvements over time

### How It Works

1. Agents monitor for errors, friction, and successes during sessions
2. At session end, use `@self-reflect` to trigger RBT analysis
3. High-confidence improvements (8+) can be applied automatically
4. Evolution logs persist globally at `~/.kiro/evolution/[agent-name]-evolution.md`

### Triggering Self-Reflection

```bash
# In any agent session
@self-reflect
```

Or agents will self-reflect when:
- Completing a significant task
- Encountering repeated errors
- Sessions exceed 30 minutes

---

## Available Agents

### 🎯 Orchestrator (`orchestrator`)
Workflow coordinator for spec-driven development.

```bash
python kiro_cli.py --agent orchestrator
# Or use the wrapper:
kiro-cli --agent orchestrator
```

**Specialties:**
- PRD/Requirements generation
- Technical design documents
- Task breakdown and tracking
- Intelligent delegation to specialists
- Context-efficient handoffs

**Use with:** `@plan-feature`, `@next-task`, `@workflow-status`

**Workflow Phases:**
1. **Requirements** → `@plan-feature [idea]`
2. **Design** → Auto after requirements approval
3. **Tasks** → Auto after design approval  
4. **Implementation** → `@next-task` (one at a time)

---

### 🔬 Code Surgeon (`code-surgeon`)
Deep code review, refactoring, and quality specialist.

```bash
kiro-cli --agent code-surgeon
```

**Specialties:**
- Security vulnerability detection (OWASP Top 10)
- Performance optimization
- Technical debt identification
- Refactoring patterns

**Use with:** `@code-review`, `@security-audit`

---

### 🧪 Test Architect (`test-architect`)
Testing specialist for comprehensive coverage.

```bash
kiro-cli --agent test-architect
```

**Specialties:**
- Unit tests (Jest, Vitest)
- E2E tests (Playwright)
- Test data generation
- Coverage analysis

**Use with:** `@test-coverage`

---

### 🚀 DevOps Automator (`devops-automator`)
CI/CD, deployment, and infrastructure automation.

```bash
kiro-cli --agent devops-automator
```

**Specialties:**
- GitHub Actions workflows
- Docker and containerization
- AWS infrastructure
- Vercel deployments

**Use with:** `@deploy-checklist`

---

### 🗄️ DB Wizard (`db-wizard`)
Database design, optimization, and Prisma expert.

```bash
kiro-cli --agent db-wizard
```

**Specialties:**
- Schema design
- Query optimization
- Migration strategies
- Prisma best practices

**Use with:** `@db-optimize`

---

### 📝 Doc Smith (`doc-smith`)
Documentation specialist for clear, useful docs.

```bash
kiro-cli --agent doc-smith
```

**Specialties:**
- README files
- API documentation
- Architecture docs
- Code comments

---

### 🎨 Frontend Designer (`frontend-designer`)
UI/UX specialist with browser automation.

```bash
kiro-cli --agent frontend-designer
```

**Specialties:**
- Tailwind CSS / shadcn/ui
- Accessibility (WCAG 2.1 AA)
- Responsive design
- Visual testing with Playwright

**Use with:** `@ui-review`, `@a11y-audit`, `@responsive-check`

---

## Quick Reference

| Agent | Best For | Model |
|-------|----------|-------|
| `orchestrator` | Feature planning, workflow coordination | **Opus 4.5** |
| `code-surgeon` | Code review, security, refactoring | **Opus 4.5** |
| `test-architect` | Writing tests, coverage analysis | **Opus 4.5** |
| `devops-automator` | CI/CD, deployment, infrastructure | **Opus 4.5** |
| `db-wizard` | Schema design, query optimization | **Opus 4.5** |
| `doc-smith` | Documentation, READMEs, API docs | Haiku 4.5 |
| `frontend-designer` | UI/UX, accessibility, styling | **Opus 4.5** |

## Available Prompts

### Workflow Prompts (use with `orchestrator`)
- `@plan-feature` - Start spec-driven development for a new feature
- `@next-task` - Continue to next task in current workflow
- `@workflow-status` - Check status of all active specs

### Specialist Prompts
- `@code-review` - Review recent code changes
- `@security-audit` - Comprehensive security scan
- `@test-coverage` - Analyze test gaps
- `@deploy-checklist` - Pre-deployment verification
- `@db-optimize` - Database performance analysis
- `@self-reflect` - Trigger RBT self-improvement analysis

---

## Spec-Driven Workflow

The orchestrator manages a structured development process:

```
┌─────────────────────────────────────────────────────────┐
│  @plan-feature "user authentication"                    │
├─────────────────────────────────────────────────────────┤
│  Phase 1: REQUIREMENTS                                  │
│  → Creates .kiro/specs/user-auth/requirements.md        │
│  → Wait for "requirements approved"                     │
├─────────────────────────────────────────────────────────┤
│  Phase 2: DESIGN                                        │
│  → Creates .kiro/specs/user-auth/design.md              │
│  → Wait for "design approved"                           │
├─────────────────────────────────────────────────────────┤
│  Phase 3: TASKS                                         │
│  → Creates .kiro/specs/user-auth/tasks.md               │
│  → Wait for "start task 1"                              │
├─────────────────────────────────────────────────────────┤
│  Phase 4: IMPLEMENTATION                                │
│  → Execute ONE task at a time                           │
│  → Delegate to specialists as needed                    │
│  → @next-task to continue                               │
└─────────────────────────────────────────────────────────┘
```

### Context Management

The orchestrator keeps context lean by:
- Starting each phase fresh
- Loading only task-specific files
- Summarizing completed work (not carrying full content)
- Using file references instead of inline content

### Delegation

The orchestrator automatically delegates to specialists:
- Schema changes → `db-wizard`
- UI components → `frontend-designer`
- Test writing → `test-architect`
- Security review → `code-surgeon`
- Documentation → `doc-smith`
- Deployment → `devops-automator`

## Usage Tips

1. **Start with the right agent** - Pick the specialist for your task
2. **Use prompts for structure** - They provide consistent workflows
3. **Combine agents** - Use code-surgeon for review, then test-architect for tests
4. **Trust the permissions** - Agents have pre-approved tools for their domain

## Creating New Agents

Copy an existing agent JSON and customize:

```json
{
  "name": "my-agent",
  "description": "What this agent does",
  "prompt": "System prompt with expertise and workflow",
  "model": "claude-sonnet-4-20250514",
  "tools": ["read", "write", "glob", "grep", "shell"],
  "allowedTools": ["read", "glob", "grep"],
  "resources": ["file://relevant/files/**/*"],
  "toolsSettings": {
    "read": { "allowedPaths": ["./src/**"] },
    "write": { "allowedPaths": ["./src/**"] }
  }
}
```

Key fields:
- `tools` - Available tools
- `allowedTools` - Pre-approved (no confirmation needed)
- `resources` - Auto-loaded context
- `toolsSettings` - Path restrictions for safety
