# Implementation Plan: Agent-Prompt Integration & Self-Evolution System

## Overview

This plan implements the agent-prompt binding system, self-evolution engine, pytest verification layer, and handoff protocol for the SEO Health Report platform. Tasks are ordered to build foundational components first, then layer on more complex features.

## Tasks

- [ ] 1. Create smoke test suite foundation
  - [ ] 1.1 Create `tests/smoke/` directory structure
    - Create `tests/smoke/__init__.py`
    - Create `tests/smoke/conftest.py` with smoke fixtures
    - _Requirements: 8.5_

  - [ ] 1.2 Implement core smoke tests
    - Create `tests/smoke/test_orchestration.py` - test orchestrate.py loads
    - Create `tests/smoke/test_scoring.py` - test calculate_scores.py works
    - Create `tests/smoke/test_report.py` - test build_report.py generates output
    - Tag all tests with `@pytest.mark.smoke`
    - _Requirements: 8.2, 8.3_

  - [ ]* 1.3 Add smoke test timing validation
    - Add timing assertions to ensure suite completes < 60s
    - _Requirements: 8.1_

- [ ] 2. Implement Agent Configuration Schema
  - [ ] 2.1 Create schema module with dataclasses
    - Create `.kiro/lib/agent_schema.py`
    - Define `AgentPromptConfig`, `HookConfig`, `AgentConfig` dataclasses
    - Implement `parse_agent_config()` function
    - Implement `validate_agent_config()` function
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 2.2 Implement default value handling
    - Add sensible defaults for missing optional fields
    - Implement version field validation (semver format)
    - _Requirements: 9.5, 9.4_

  - [ ]* 2.3 Write property test for config schema validation
    - **Property 10: Agent Config Schema Validation**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

  - [ ]* 2.4 Write property test for config round-trip
    - **Property 2: Config Parsing Completeness**
    - **Validates: Requirements 1.1, 1.6**

- [ ] 3. Checkpoint - Schema foundation complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement Binding System
  - [ ] 4.1 Create binding system module
    - Create `.kiro/lib/binding_system.py`
    - Implement `BindingSystem` class with `parse_config()` method
    - Implement `invoke_prompts()` method for lifecycle events
    - Implement `register_hook()` method for post-tool-use hooks
    - _Requirements: 1.1, 1.6_

  - [ ] 4.2 Implement lifecycle event handling
    - Handle `onStart` event - invoke prompts at session start
    - Handle `onComplete` event - invoke prompts at task completion
    - Handle `afterWrite` trigger - invoke after code writes
    - Handle `afterError` trigger - invoke after errors
    - _Requirements: 1.2, 1.3, 1.4, 1.5_

  - [ ] 4.3 Implement missing prompt handling
    - Log warning when prompt file not found
    - Continue execution without failing
    - _Requirements: 1.7_

  - [ ]* 4.4 Write property test for lifecycle event triggers
    - **Property 1: Lifecycle Event Triggers**
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5**

- [ ] 5. Checkpoint - Binding system complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement Evolution Engine
  - [ ] 6.1 Create evolution engine module
    - Create `.kiro/lib/evolution_engine.py`
    - Implement `RBTAnalysis` and `EvolutionRecord` dataclasses
    - Implement `analyze_session()` method for RBT analysis
    - _Requirements: 2.1_

  - [ ] 6.2 Implement patch generation
    - Implement `generate_patch()` method
    - Only generate patches when confidence >= 8
    - Restrict patches to allowed fields (prompt, resources, toolsSettings)
    - _Requirements: 2.2, 2.4_

  - [ ] 6.3 Implement evolution application with backup
    - Implement `apply_evolution()` method
    - Create backup before applying changes
    - Implement `rollback()` method to restore from backup
    - _Requirements: 3.2, 3.3, 3.5_

  - [ ] 6.4 Implement evolution logging
    - Create `~/.kiro/evolution/` directory if not exists
    - Implement `log_evolution()` method
    - Write to `[agent-name]-evolution.md` in markdown format
    - _Requirements: 2.5, 10.1, 10.2_

  - [ ]* 6.5 Write property test for self-reflection output schema
    - **Property 3: Self-Reflection Output Schema**
    - **Validates: Requirements 2.1, 2.3**

  - [ ]* 6.6 Write property test for high-confidence patch generation
    - **Property 4: High-Confidence Patch Generation**
    - **Validates: Requirements 2.2, 2.4**

  - [ ]* 6.7 Write property test for evolution application with backup
    - **Property 5: Evolution Application with Backup**
    - **Validates: Requirements 3.2, 3.3, 3.5**

  - [ ]* 6.8 Write property test for evolution log completeness
    - **Property 11: Evolution Log Completeness**
    - **Validates: Requirements 10.1, 10.3, 10.5**

- [ ] 7. Checkpoint - Evolution engine complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement Verification Layer
  - [ ] 8.1 Create verification layer module
    - Create `.kiro/lib/verification_layer.py`
    - Implement `TestResult` dataclass
    - Implement `run_smoke_tests()` method
    - Implement `run_full_suite()` method
    - _Requirements: 5.1, 5.4_

  - [ ] 8.2 Implement test flow logic
    - Run smoke tests first with `-x` flag
    - If smoke passes, run full suite
    - Capture and parse pytest output
    - _Requirements: 5.2_

  - [ ] 8.3 Implement RCA trigger on failure
    - Detect test failures from pytest output
    - Invoke `@rca` prompt with failure context
    - _Requirements: 5.3_

  - [ ] 8.4 Implement evolution verification
    - Implement `verify_evolution()` method
    - Compare before/after performance metrics
    - Rollback if regression > 10%
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 8.5 Write property test for test verification flow
    - **Property 7: Test Verification Flow**
    - **Validates: Requirements 5.2, 5.3, 5.5**

  - [ ]* 8.6 Write property test for regression detection and rollback
    - **Property 6: Regression Detection and Rollback**
    - **Validates: Requirements 4.3, 4.4**

- [ ] 9. Checkpoint - Verification layer complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement Handoff Protocol
  - [ ] 10.1 Create handoff protocol module
    - Create `.kiro/lib/handoff_protocol.py`
    - Implement `HandoffFile` dataclass
    - Implement `create_handoff()` method with timestamp naming
    - _Requirements: 6.1_

  - [ ] 10.2 Implement handoff file operations
    - Implement `read_handoff()` method
    - Implement `complete_handoff()` method
    - Implement `validate_handoff()` method
    - _Requirements: 6.2, 6.4, 6.7_

  - [ ]* 10.3 Write property test for handoff file completeness
    - **Property 8: Handoff File Completeness**
    - **Validates: Requirements 6.1, 6.2, 6.6**

- [ ] 11. Checkpoint - Handoff protocol complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Create New Prompts
  - [ ] 12.1 Create self-reflect prompt
    - Create `.kiro/prompts/self-reflect.md`
    - Include RBT analysis framework
    - Include JSON patch generation for confidence >= 8
    - Include evolution logging instructions
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 12.2 Create verify-changes prompt
    - Create `.kiro/prompts/verify-changes.md`
    - Include pytest smoke test execution
    - Include full suite progression
    - Include RCA trigger on failure
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 12.3 Create apply-evolution prompt
    - Create `.kiro/prompts/apply-evolution.md`
    - Include evolution log reading
    - Include patch application with backup
    - Include commit message generation
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 12.4 Create verify-evolution prompt
    - Create `.kiro/prompts/verify-evolution.md`
    - Include test task execution
    - Include metric comparison
    - Include rollback on regression
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ] 12.5 Create handoff-create prompt
    - Create `.kiro/prompts/handoff-create.md`
    - Include handoff file template
    - Include validation checklist
    - _Requirements: 6.1, 6.2, 6.6_

  - [ ] 12.6 Create handoff-complete prompt
    - Create `.kiro/prompts/handoff-complete.md`
    - Include results writing
    - Include validation and closure
    - _Requirements: 6.4, 6.7_

- [ ] 13. Checkpoint - Prompts complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Implement Improvement Loop
  - [ ] 14.1 Create improvement loop orchestrator
    - Create `.kiro/lib/improvement_loop.py`
    - Implement loop execution order: prime → execute → verify → reflect → apply → verify-evolution → log
    - Implement conditional apply-evolution trigger (confidence >= 8)
    - _Requirements: 7.1, 7.2_

  - [ ] 14.2 Implement loop logging and metrics
    - Create `.kiro/evolution/loop-history.md` logging
    - Implement version increment on successful evolution
    - Implement cumulative improvement tracking
    - _Requirements: 7.3, 7.4, 7.5_

  - [ ]* 14.3 Write property test for improvement loop ordering
    - **Property 9: Improvement Loop Ordering**
    - **Validates: Requirements 7.1, 7.2**

- [ ] 15. Checkpoint - Improvement loop complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Update Agent Configurations
  - [ ] 16.1 Update orchestrator.json with new schema
    - Add `prompts` section with onStart, onComplete, available, autoTrigger
    - Add `hooks` section with postToolUse triggers
    - Add `version` field
    - _Requirements: 1.6, 5.6, 9.1_

  - [ ] 16.2 Update code-surgeon.json with new schema
    - Add `prompts` section
    - Add `hooks` section
    - Add `version` field
    - _Requirements: 1.6, 5.6, 9.1_

  - [ ] 16.3 Update test-architect.json with new schema
    - Add `prompts` section
    - Add `hooks` section
    - Add `version` field
    - _Requirements: 1.6, 5.6, 9.1_

  - [ ] 16.4 Update remaining agent configs
    - Update db-wizard.json, frontend-designer.json, devops-automator.json, doc-smith.json
    - Add prompts, hooks, and version fields to each
    - _Requirements: 1.6, 5.6, 9.1_

- [ ] 17. Final Checkpoint - Full integration
  - Ensure all tests pass, ask the user if questions arise.
  - Run full improvement loop demonstration
  - Verify agent configs are valid

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The `.kiro/lib/` directory will contain the Python implementation modules
- Evolution logs are stored in user home directory (`~/.kiro/evolution/`) for persistence across projects
