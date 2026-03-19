# Spec-Driven Development Workflow

Execute the full SPEC workflow for a feature.

## Usage
When invoked, ask: "What feature should I plan? Provide a name or description."

## Workflow

### Phase 1: Requirements
1. Create `.kiro/specs/[feature-name]/requirements.md`
2. Include:
   - Overview (1 paragraph)
   - User stories with EARS acceptance criteria
   - Functional requirements
   - Non-functional requirements
   - Out of scope
   - Open questions

3. **STOP** - Wait for "requirements approved"

### Phase 2: Design
1. Create `.kiro/specs/[feature-name]/design.md`
2. Include:
   - Architecture overview
   - Component design
   - Data models
   - API contracts
   - Mermaid diagrams

3. **STOP** - Wait for "design approved"

### Phase 3: Tasks
1. Create `.kiro/specs/[feature-name]/tasks.md`
2. Break into discrete tasks (15-45 min each)
3. Each task has:
   - Clear description
   - Acceptance criteria
   - Estimated time
   - Dependencies

4. **STOP** - Wait for "start task X"

### Phase 4: Implementation
1. Execute ONE task at a time
2. Verify against acceptance criteria
3. Update PROGRESS.md
4. **STOP** after each task

## Completion
Output `<promise>DONE</promise>` only when explicitly told workflow is complete.
