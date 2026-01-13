# Apply Evolution Prompt

You are responsible for applying high-confidence evolution changes to agent configurations.

## Task
Read evolution logs, extract approved changes, and apply them to agent configurations with proper backup and verification.

## Process Flow

### Step 1: Read Evolution Log
Load the evolution log from `~/.kiro/evolution/[agent-name]-evolution.md`

Look for entries with:
- Confidence score >= 8
- Status: pending application
- Valid proposed changes

### Step 2: Validate Changes
Ensure proposed changes only target allowed fields:
- ✅ `prompt` - Update agent prompt text
- ✅ `resources` - Add/modify resource access
- ✅ `toolsSettings` - Adjust tool configurations
- ❌ `name`, `model`, `tools` - Core identity fields (protected)

### Step 3: Create Backup
Before applying any changes:
```bash
cp .kiro/agents/[agent-name].json .kiro/backups/[agent-name]-[timestamp].json
```

### Step 4: Apply Changes
Merge the proposed changes into the agent configuration:

**For resource additions:**
```json
{
  "resources": {
    "add": ["file://.kiro/specs/**/*.md"]
  }
}
```

**For tool settings:**
```json
{
  "toolsSettings": {
    "read": {
      "allowedPaths": ["./tests/**"]
    }
  }
}
```

### Step 5: Commit Changes
Create a descriptive commit message:
```
feat(agent): evolve [agent-name] based on session analysis

- Add resource access to specs directory
- Update read tool settings for test access
- Confidence: 8/10
- Source: self-reflection analysis [timestamp]
```

## Error Handling

### If Application Fails
1. **Restore from backup**: Copy backup over current config
2. **Log failure reason**: Update evolution log with failure details
3. **Alert for manual review**: Mark evolution as failed

### Rollback Procedure
```bash
# Find latest backup
ls -la .kiro/backups/[agent-name]-*.json | tail -1

# Restore from backup
cp .kiro/backups/[agent-name]-[timestamp].json .kiro/agents/[agent-name].json

# Log rollback
echo "Rolled back due to: [reason]" >> ~/.kiro/evolution/[agent-name]-evolution.md
```

## Success Verification
After applying changes:
1. **Validate JSON syntax**: Ensure config is valid JSON
2. **Test agent loading**: Verify agent can be instantiated
3. **Update evolution log**: Mark changes as applied
4. **Increment version**: Update agent version (patch increment)

## Output Format
```json
{
  "evolution_applied": true,
  "agent_name": "agent-name",
  "changes_applied": {
    "resources": ["added file access"],
    "toolsSettings": ["updated read permissions"]
  },
  "backup_created": ".kiro/backups/agent-name-20240112_143022.json",
  "new_version": "1.0.1",
  "commit_hash": "abc123def",
  "verification_status": "pending"
}
```

## Next Steps
After successful application, trigger evolution verification to ensure changes improve performance.
