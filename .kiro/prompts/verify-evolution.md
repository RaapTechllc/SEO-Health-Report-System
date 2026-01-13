# Verify Evolution Prompt

You are responsible for verifying that evolution changes actually improve agent performance.

## Task
Test the evolved agent on a standardized task and compare performance metrics against baseline.

## Verification Process

### Step 1: Baseline Measurement
If available, load baseline metrics from previous verification:
- Task completion time
- Success rate
- Context efficiency
- Error rate

### Step 2: Run Test Task
Execute the agent on a standardized test task:

**Example Test Tasks:**
- Code review of a sample file
- Generate a simple report
- Analyze a website URL
- Complete a multi-step workflow

### Step 3: Measure Performance
Collect metrics:
```json
{
  "completion_time_seconds": 45.2,
  "success_rate": 1.0,
  "context_reloads": 0,
  "errors_encountered": 0,
  "tools_used": ["fs_read", "fs_write"],
  "prompt_invocations": 3
}
```

### Step 4: Compare Against Baseline
Calculate improvement/regression:
- **Improvement**: Faster completion, fewer errors, better success rate
- **Regression**: Slower completion (>10% increase), more errors, lower success rate

## Regression Detection

### Critical Thresholds
- **Performance regression**: >10% increase in completion time
- **Success regression**: Any decrease in success rate
- **Error regression**: Increase in error count

### Rollback Triggers
If any critical regression is detected:
1. **Automatic rollback**: Restore agent from backup
2. **Log rollback reason**: Update evolution log
3. **Mark evolution failed**: Prevent future similar changes

## Verification Results

### Success Case
```json
{
  "verification_status": "passed",
  "performance_change": "+15.5%",
  "metrics": {
    "before": {"completion_time": 45.0, "errors": 2},
    "after": {"completion_time": 38.0, "errors": 0}
  },
  "recommendation": "evolution_approved"
}
```

### Failure Case
```json
{
  "verification_status": "failed",
  "performance_change": "-12.3%",
  "regression_type": "performance",
  "metrics": {
    "before": {"completion_time": 45.0, "errors": 0},
    "after": {"completion_time": 50.5, "errors": 1}
  },
  "recommendation": "rollback_required"
}
```

## Rollback Procedure
When regression is detected:

```bash
# Restore from backup
python3 -c "
from .kiro.lib.evolution_engine import EvolutionEngine
engine = EvolutionEngine()
engine.rollback('agent-name')
"

# Update evolution log
echo '### Verification Result: FAILED - ROLLED BACK
- Performance regression: -12.3%
- Rollback completed: [timestamp]
' >> ~/.kiro/evolution/agent-name-evolution.md
```

## Success Actions
When verification passes:
1. **Update evolution log**: Mark as verified and successful
2. **Store new baseline**: Save current metrics for future comparisons
3. **Increment confidence**: Boost confidence in similar future changes

## Continuous Learning
Track verification results to improve evolution quality:
- Success patterns in changes
- Common regression causes
- Optimal confidence thresholds
