# Ralph Loop Multi-Agent System Documentation

## Overview

The Ralph Loop Multi-Agent System is an autonomous development workflow that uses specialized AI agents working in parallel to complete complex software projects. Each agent operates in continuous "Ralph Loops" (Observe-Orient-Decide-Act cycles), picking tasks, executing them, and updating progress until all work is complete.

## Current Project Status (2026-01-12)

**SEO Health Report Platform: ~70% Complete**

### Completed
- Core audit modules (technical, content, AI visibility)
- Report generation (DOCX, PDF, MD)
- Caching system & async orchestration
- Frontend dashboard components
- Infrastructure configs
- 132 unit tests passing

### Remaining (~24h effort)
1. Fix test_orchestrate.py import error
2. Data Contracts (schemas.py)
3. Competitor Dashboard feature
4. CI Pipeline (GitHub Actions)
5. Integration tests
6. Documentation & packaging

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PLAN.md       │    │  PROGRESS.md    │    │ ralph-runner.py │
│   (Master Plan) │◄──►│ (Shared State)  │◄──►│ (Coordinator)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    7 Specialized Agents                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐  │
│  │ devops-     │ │ agent-      │ │ db-wizard   │ │ code-    │  │
│  │ automator   │ │ creator     │ │             │ │ surgeon  │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ frontend-   │ │ test-       │ │ doc-smith   │              │
│  │ designer    │ │ architect   │ │             │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Master Plan (PLAN.md)
- Defines 16 tasks across 6 phases
- Assigns tasks to specific agents
- Includes acceptance criteria for each task
- Serves as single source of truth for project scope

### 2. Shared Progress Tracker (PROGRESS.md)
- Real-time status of all tasks
- Agent activity timestamps
- Completion promises tracking
- Conflict resolution through file locking

### 3. Ralph Loop Coordinator (ralph-runner.py)
- Spawns all agents in parallel
- Monitors system health
- Handles graceful shutdown
- Coordinates inter-agent dependencies

### 4. Specialized Agents
Each agent operates autonomously with:
- **Ralph Loop Protocol**: Continuous Observe-Orient-Decide-Act cycles
- **Task Claiming**: Atomic task selection to prevent conflicts
- **Progress Updates**: Real-time status reporting
- **Error Recovery**: Automatic retry and escalation
- **Completion Promises**: Explicit done signals

## Ralph Loop Protocol

Each agent follows this cycle:

1. **Observe**: Check PROGRESS.md for available tasks
2. **Orient**: Identify highest priority unblocked task
3. **Decide**: Claim task by updating status to IN_PROGRESS
4. **Act**: Execute task until completion criteria met
5. **Update**: Mark task DONE and emit completion promise if finished

## Agent Specializations

| Agent | Primary Focus | Key Tasks |
|-------|---------------|-----------|
| **devops-automator** | Infrastructure & CI/CD | Ralph Loop infrastructure, deployment pipeline |
| **agent-creator** | Agent management | Update agent configs for Ralph compatibility |
| **db-wizard** | Database design | Schema design, migrations, optimization |
| **code-surgeon** | Code quality | API implementation, security review |
| **frontend-designer** | UI/UX development | Dashboard, forms, real-time features |
| **test-architect** | Quality assurance | Unit tests, integration tests, E2E tests |
| **doc-smith** | Documentation | User guides, API docs, architecture docs |

## Usage Instructions

### Starting the System

```bash
# Start all agents in Ralph loops
./start-ralph.sh

# Monitor progress in real-time
python3 progress-tracker.py monitor

# Check individual agent status
python3 task-picker.py <agent-name>
```

### Monitoring Progress

```bash
# View current system status
python3 progress-tracker.py

# Monitor logs
tail -f logs/coordinator.log
tail -f ralph-loop.log

# Check specific agent activity
grep "devops-automator" ralph-loop.log
```

### Stopping the System

```bash
# Graceful shutdown
./stop-ralph.sh

# Force stop if needed
pkill -f ralph-runner.py
```

## System States

### Task States
- **PENDING**: Not started, waiting for dependencies
- **IN_PROGRESS**: Currently being worked on by an agent
- **BLOCKED**: Waiting for dependencies to complete
- **DONE**: Completed with all acceptance criteria met

### Agent States
- **IDLE**: No current activity (>30 minutes)
- **ACTIVE**: Recent activity within 30 minutes
- **STUCK**: In progress task with no activity >30 minutes

### System Completion
The system completes when:
1. All 16 tasks marked DONE
2. All 7 agents emit `<promise>DONE</promise>`
3. All acceptance criteria verified
4. No blocking issues remain

## Error Handling

### Automatic Recovery
- **Task Conflicts**: File locking prevents multiple agents claiming same task
- **Agent Failures**: Exponential backoff and retry logic
- **Resource Contention**: Atomic file operations with conflict detection
- **Stuck Agents**: Automatic detection and task reassignment

### Manual Intervention
- **System Deadlock**: Restart with `./stop-ralph.sh && ./start-ralph.sh`
- **Corrupted State**: Reset PROGRESS.md and restart
- **Agent Errors**: Check logs and restart specific agents

## File Structure

```
├── PLAN.md                    # Master project plan
├── PROGRESS.md               # Shared progress tracking
├── ralph-runner.py           # Main coordinator
├── task-picker.py           # Task selection utility
├── progress-tracker.py      # Progress monitoring
├── start-ralph.sh           # System startup script
├── stop-ralph.sh            # System shutdown script
├── .kiro/agents/            # Agent configurations
│   ├── devops-automator-ralph.json
│   ├── agent-creator-ralph.json
│   ├── code-surgeon-ralph.json
│   ├── db-wizard-ralph.json
│   ├── frontend-designer-ralph.json
│   ├── test-architect-ralph.json
│   └── doc-smith-ralph.json
└── logs/                    # System logs
    ├── coordinator.log
    └── ralph-loop.log
```

## Configuration

### Agent Configuration
Each agent has:
- **Ralph Loop Instructions**: Autonomous operation protocol
- **Task Assignments**: Specific tasks from PLAN.md
- **Resource Access**: File and tool permissions
- **Completion Criteria**: Clear success definitions

### System Configuration
- **Task Dependencies**: Phase-based dependency management
- **Monitoring Intervals**: Progress check frequency
- **Timeout Settings**: Stuck agent detection thresholds
- **Retry Logic**: Exponential backoff parameters

## Troubleshooting

### Common Issues

**System Won't Start**
```bash
# Check required files exist
ls -la PLAN.md PROGRESS.md

# Verify agent configurations
ls -la .kiro/agents/*-ralph.json

# Check Python dependencies
python3 --version
```

**Agents Appear Stuck**
```bash
# Check agent activity
python3 progress-tracker.py

# View detailed logs
tail -f logs/coordinator.log

# Restart specific agent (manual intervention)
# Edit PROGRESS.md to reset stuck task to PENDING
```

**Progress Not Updating**
```bash
# Check file permissions
ls -la PROGRESS.md

# Remove lock files
rm -f .progress.lock

# Restart system
./stop-ralph.sh && ./start-ralph.sh
```

### Performance Tuning

**Faster Task Execution**
- Reduce monitoring intervals in ralph-runner.py
- Increase agent parallelism
- Optimize task dependencies

**Resource Management**
- Monitor system resource usage
- Implement agent throttling if needed
- Use SSD storage for better file I/O

## Development

### Adding New Agents
1. Create agent configuration JSON
2. Add to RALPH_AGENTS array in start-ralph.sh
3. Update PLAN.md with agent-specific tasks
4. Test with task-picker.py

### Modifying Tasks
1. Update PLAN.md with new tasks
2. Ensure acceptance criteria are clear
3. Update agent configurations if needed
4. Reset PROGRESS.md for clean start

### Extending Functionality
- Add new tools to agent configurations
- Implement custom task types
- Enhance progress tracking
- Add integration with external systems

## Security Considerations

### File Access
- Agents have restricted file system access
- Shared files use atomic operations
- Lock files prevent race conditions

### Process Isolation
- Each agent runs in separate process
- Resource limits can be enforced
- Graceful shutdown prevents data corruption

### Audit Trail
- All agent actions logged with timestamps
- Progress changes tracked in PROGRESS.md
- Git integration for code change tracking

---

**System Status**: Production Ready
**Last Updated**: 2026-01-12
**Version**: 1.0.0