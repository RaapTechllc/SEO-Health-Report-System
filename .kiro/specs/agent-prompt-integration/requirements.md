# Requirements Document

## Introduction

This specification defines an Agent-Prompt Integration System with Self-Evolution capabilities for the SEO Health Report platform. The system formalizes the relationship between agents and prompts, enables automated verification through pytest, and creates a continuous improvement loop where agents evolve based on their performance.

## Glossary

- **Agent**: A specialized AI assistant defined in `.kiro/agents/*.json` with specific tools, resources, and expertise
- **Prompt**: A reusable instruction template in `.kiro/prompts/*.md` that guides agent behavior for specific tasks
- **Binding**: A formal mapping between an agent and the prompts it should invoke at specific lifecycle events
- **Evolution**: The process of improving agent configurations based on self-reflection and performance data
- **Handoff**: A structured context transfer between agents during task delegation
- **Verification**: Automated testing (pytest) to validate changes don't introduce regressions
- **RBT_Analysis**: Roses-Buds-Thorns reflection framework for identifying improvements

## Requirements

### Requirement 1: Agent-Prompt Binding System

**User Story:** As a developer, I want agents to automatically invoke relevant prompts at specific lifecycle events, so that workflows are consistent and prompts are utilized effectively.

#### Acceptance Criteria

1. WHEN an agent configuration is loaded, THE Binding_System SHALL parse the `prompts` section to identify lifecycle bindings
2. WHEN an agent session starts, THE Binding_System SHALL invoke all prompts listed in `onStart` array
3. WHEN an agent completes a task, THE Binding_System SHALL invoke all prompts listed in `onComplete` array
4. WHEN an agent writes code, THE Binding_System SHALL invoke prompts listed in `autoTrigger.afterWrite` if defined
5. WHEN an agent encounters an error, THE Binding_System SHALL invoke prompts listed in `autoTrigger.afterError` if defined
6. THE Agent_Config SHALL include a `prompts` section with `onStart`, `onComplete`, `available`, and `autoTrigger` fields
7. WHEN a prompt is not found in `.kiro/prompts/`, THE Binding_System SHALL log a warning and continue execution

### Requirement 2: Self-Reflection Prompt Enhancement

**User Story:** As a system architect, I want the self-reflect prompt to generate actionable JSON patches, so that agent improvements can be automatically applied.

#### Acceptance Criteria

1. THE Self_Reflect_Prompt SHALL analyze agent performance using RBT (Roses-Buds-Thorns) framework
2. WHEN confidence score is >= 8, THE Self_Reflect_Prompt SHALL generate a JSON patch for the agent's configuration
3. THE Self_Reflect_Prompt SHALL output structured evolution data including: agent_name, confidence_score, roses, buds, thorns, and proposed_changes
4. WHEN generating patches, THE Self_Reflect_Prompt SHALL target only modifiable fields: prompt, resources, toolsSettings
5. THE Self_Reflect_Prompt SHALL log evolution insights to `~/.kiro/evolution/[agent-name]-evolution.md`

### Requirement 3: Evolution Application System

**User Story:** As a developer, I want high-confidence improvements to be automatically applied to agent configs, so that agents continuously improve without manual intervention.

#### Acceptance Criteria

1. THE Apply_Evolution_Prompt SHALL read evolution logs from `~/.kiro/evolution/[agent-name]-evolution.md`
2. WHEN confidence >= 8, THE Apply_Evolution_Prompt SHALL extract proposed changes and apply them to the agent config
3. WHEN applying changes, THE Apply_Evolution_Prompt SHALL create a backup of the original config
4. THE Apply_Evolution_Prompt SHALL commit changes with a descriptive message including the evolution source
5. IF evolution application fails, THEN THE Apply_Evolution_Prompt SHALL restore the backup and log the failure

### Requirement 4: Evolution Verification System

**User Story:** As a developer, I want evolution changes to be verified before being finalized, so that regressions are caught early.

#### Acceptance Criteria

1. THE Verify_Evolution_Prompt SHALL run the agent on a standardized test task after evolution is applied
2. THE Verify_Evolution_Prompt SHALL compare performance metrics before and after evolution
3. IF regression is detected (performance drops > 10%), THEN THE Verify_Evolution_Prompt SHALL rollback the evolution
4. THE Verify_Evolution_Prompt SHALL log verification results to the evolution file
5. WHEN verification passes, THE Verify_Evolution_Prompt SHALL mark the evolution as "verified" in the log

### Requirement 5: Pytest Verification Integration

**User Story:** As a developer, I want code changes to be automatically verified with pytest, so that regressions are caught immediately.

#### Acceptance Criteria

1. THE Verify_Changes_Prompt SHALL run `pytest tests/ -x --tb=short` for quick verification after code changes
2. IF smoke tests pass, THE Verify_Changes_Prompt SHALL run `pytest tests/ --tb=short` for full suite
3. WHEN tests fail, THE Verify_Changes_Prompt SHALL invoke the `@rca` prompt to diagnose the failure
4. THE Verify_Changes_Prompt SHALL output structured results: status (pass/fail/flaky), test_count, failures, duration
5. WHEN all tests pass, THE Verify_Changes_Prompt SHALL return success and allow workflow to continue
6. THE Agent_Config SHALL support a `hooks.postToolUse` section for automatic verification triggers

### Requirement 6: Structured Handoff Protocol

**User Story:** As an orchestrator, I want to delegate tasks to specialist agents with structured context, so that handoffs are reliable and context is preserved.

#### Acceptance Criteria

1. WHEN delegating to a specialist, THE Orchestrator SHALL create a handoff file at `.kiro/handoffs/[timestamp]-[agent]-[task].md`
2. THE Handoff_File SHALL include: task_description, relevant_file_refs, expected_output, success_criteria, context_summary
3. THE Specialist_Agent SHALL read the handoff file and execute the task according to its criteria
4. WHEN task completes, THE Specialist_Agent SHALL write results back to the handoff file
5. THE Orchestrator SHALL read handoff results and continue workflow
6. THE Handoff_Create_Prompt SHALL generate properly formatted handoff files
7. THE Handoff_Complete_Prompt SHALL validate and close handoff files

### Requirement 7: Continuous Improvement Loop

**User Story:** As a system architect, I want a complete feedback loop from execution to evolution, so that the system continuously improves.

#### Acceptance Criteria

1. THE Improvement_Loop SHALL execute in this order: prime → execute → verify → reflect → apply → verify-evolution → log
2. WHEN confidence >= 8 in self-reflection, THE Improvement_Loop SHALL trigger apply-evolution automatically
3. THE Improvement_Loop SHALL log all iterations to `.kiro/evolution/loop-history.md`
4. WHEN an evolution is verified successfully, THE Improvement_Loop SHALL increment the agent's version in its config
5. THE Improvement_Loop SHALL track cumulative improvement metrics over time

### Requirement 8: Smoke Test Suite

**User Story:** As a developer, I want a fast smoke test suite that validates critical paths, so that verification doesn't slow down development.

#### Acceptance Criteria

1. THE Smoke_Test_Suite SHALL complete in under 60 seconds
2. THE Smoke_Test_Suite SHALL cover: orchestration flow, score calculation, report generation, API integrations
3. THE Smoke_Test_Suite SHALL be tagged with `@pytest.mark.smoke` for selective execution
4. WHEN smoke tests fail, THE System SHALL block further execution until issues are resolved
5. THE Smoke_Test_Suite SHALL be located in `tests/smoke/` directory

### Requirement 9: Agent Configuration Schema

**User Story:** As a developer, I want a consistent schema for agent configurations, so that all agents support the new binding and evolution features.

#### Acceptance Criteria

1. THE Agent_Config_Schema SHALL include: name, description, prompt, model, tools, allowedTools, resources, toolsSettings, prompts, hooks, version
2. THE `prompts` field SHALL be an object with: onStart (array), onComplete (array), available (array), autoTrigger (object)
3. THE `hooks` field SHALL be an object with: postToolUse (array of trigger configs)
4. THE `version` field SHALL be a semantic version string (e.g., "1.0.0")
5. WHEN an agent config is missing required fields, THE System SHALL use sensible defaults

### Requirement 10: Evolution Logging and Audit Trail

**User Story:** As a system administrator, I want a complete audit trail of all evolution changes, so that I can track and review agent improvements over time.

#### Acceptance Criteria

1. THE Evolution_Log SHALL record: timestamp, agent_name, change_type, confidence_score, changes_applied, verification_result
2. THE Evolution_Log SHALL be stored in `~/.kiro/evolution/` directory
3. WHEN an evolution is rolled back, THE Evolution_Log SHALL record the rollback reason
4. THE Evolution_Log SHALL support querying by agent name, date range, and change type
5. THE Evolution_Log SHALL be human-readable markdown format
