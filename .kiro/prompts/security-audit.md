# Security Audit

Perform a comprehensive security audit of the codebase.

## Checklist

1. **Authentication & Authorization**
   - Check for auth bypass vulnerabilities
   - Verify session management
   - Review role-based access controls

2. **Injection Attacks**
   - SQL injection (even with Prisma, check raw queries)
   - XSS vulnerabilities in user input rendering
   - Command injection in shell executions

3. **Data Exposure**
   - Sensitive data in logs
   - API responses leaking internal data
   - Hardcoded secrets or credentials

4. **OWASP Top 10**
   - Broken access control
   - Cryptographic failures
   - Security misconfiguration

## Output Format

For each finding:
- **File**: Location
- **Severity**: Critical/High/Medium/Low
- **Issue**: Description
- **Fix**: Specific remediation
- **Reference**: OWASP or CWE link if applicable

Start by scanning the `src/app/api` directory and authentication-related code.
