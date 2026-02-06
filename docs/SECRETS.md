# Secrets Management Guide

This document describes how to manage secrets for the SEO Health Report System.

## GitHub Secrets

The following secrets must be configured in GitHub repository settings for CI/CD pipelines.

### Required Secrets

| Secret Name | Description | Used In |
|-------------|-------------|---------|
| `DATABASE_URL_STAGING` | PostgreSQL connection string for staging | Staging deploy |
| `DATABASE_URL_PRODUCTION` | PostgreSQL connection string for production | Production deploy |
| `JWT_SECRET_KEY_STAGING` | JWT signing key for staging (min 32 chars) | Staging deploy |
| `JWT_SECRET_KEY_PRODUCTION` | JWT signing key for production (256-bit) | Production deploy |

### API Keys

| Secret Name | Description | Used In |
|-------------|-------------|---------|
| `PAGESPEED_API_KEY` | Google PageSpeed Insights API key | All environments |
| `OPENAI_API_KEY` | OpenAI API key for AI analysis | All environments |
| `STRIPE_SECRET_KEY_STAGING` | Stripe test mode secret key | Staging |
| `STRIPE_SECRET_KEY_PRODUCTION` | Stripe live mode secret key | Production |
| `STRIPE_WEBHOOK_SECRET_STAGING` | Stripe webhook signing secret (staging) | Staging |
| `STRIPE_WEBHOOK_SECRET_PRODUCTION` | Stripe webhook signing secret (prod) | Production |

### Infrastructure

| Secret Name | Description | Used In |
|-------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 storage | Production |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 storage | Production |
| `S3_BUCKET_NAME` | S3 bucket for report storage | Production |
| `SENTRY_DSN` | Sentry error tracking DSN | All environments |

## Setting Up Secrets

### GitHub Repository Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret with the appropriate value

### GitHub Environment Secrets

For environment-specific secrets (staging vs production):

1. Go to Settings → Environments
2. Create "staging" and "production" environments
3. Add environment-specific secrets to each

## Secret Naming Convention

- Use `SCREAMING_SNAKE_CASE`
- Suffix with environment: `_STAGING`, `_PRODUCTION`
- Use descriptive names that indicate purpose

## Secret Rotation

### JWT Secret Keys

**Frequency:** Every 90 days or after security incident

**Procedure:**
1. Generate new 256-bit random key
2. Update secret in GitHub
3. Deploy with grace period (both keys valid)
4. Remove old key after 24 hours

### API Keys

**Frequency:** Every 180 days or when compromised

**Procedure:**
1. Generate new key in provider dashboard
2. Update secret in GitHub
3. Deploy new key
4. Revoke old key after confirming new key works

### Database Passwords

**Frequency:** Every 90 days

**Procedure:**
1. Create new database user with new password
2. Update DATABASE_URL secret
3. Deploy with new credentials
4. Remove old database user

## Emergency Response

### If a Secret is Compromised

1. **Immediately** rotate the compromised secret
2. Check audit logs for unauthorized access
3. Review all deployments since compromise
4. Notify security team
5. Document incident in security log

### Generating Secure Secrets

```bash
# Generate JWT secret (256-bit)
openssl rand -base64 32

# Generate API key style secret
openssl rand -hex 32

# Generate password
openssl rand -base64 24
```

## Local Development

For local development, use `.env.local` (not committed):

```bash
# Copy example and fill in values
cp .env.example .env.local

# Or use development defaults
cp infrastructure/envs/staging.env.example .env.local
```

**Never use production secrets locally.**

## Verification

To verify secrets are correctly configured:

```bash
# In CI, secrets are masked in logs
echo "JWT_SECRET_KEY length: ${#JWT_SECRET_KEY}"

# Verify database connection
python -c "from database import init_db; init_db()"
```

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment-specific secrets** (staging ≠ production)
3. **Rotate secrets regularly** on schedule
4. **Use minimum required permissions** for API keys
5. **Monitor for secret exposure** (use tools like GitGuardian)
6. **Audit secret access** regularly
7. **Document all secrets** and their purpose
