# Validation Protocol

## Automatic Validation
After every response, validation scripts run automatically via stop hooks.
You will see the output at the start of your next turn.

## Responding to Validation Failures

When you see validation failures:

1. **Read the error messages carefully** — They indicate exactly what's broken
2. **Fix the specific issues** — Don't rewrite entire files, target the problem
3. **Verify your fix** — After making changes, check if the validation passes
4. **Do not mark task complete** — Until validation shows ✅ PASSED

## Validation Types

- **TypeScript Compilation** — Type errors must be fixed
- **Linting** — Warnings are acceptable, errors should be fixed
- **Tests** — All tests must pass before completion
- **Syntax Checks** — Any syntax error is a blocker

## If Stuck

If you cannot resolve a validation error after 3 attempts:
1. Document what you tried
2. Explain what the error means
3. Escalate to human with full context
