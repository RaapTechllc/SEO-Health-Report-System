# Rollback Procedure

This document describes how to rollback a production deployment if issues are discovered.

## Quick Rollback (Automated)

The fastest way to rollback is using the GitHub Actions workflow:

1. Go to **Actions** → **Rollback Production**
2. Click **Run workflow**
3. Enter:
   - **Target version**: The version tag to rollback to (e.g., `v1.0.0`)
   - **Reason**: Brief description of why rollback is needed
   - **Confirm**: Type `ROLLBACK`
4. Click **Run workflow**

The workflow will:
- Verify the target version images exist
- Deploy the previous version
- Run health checks
- Notify the team

## Manual Rollback

If the automated workflow fails, follow these steps:

### 1. Identify the Previous Version

```bash
# List recent deployments
git tag -l 'v*' --sort=-creatordate | head -5

# Or check GitHub releases
# https://github.com/RaapTechllc/SEO-Health-Report-System/releases
```

### 2. Pull Previous Images

```bash
TARGET_VERSION="v1.0.0"  # Replace with actual version

docker pull ghcr.io/raaptechllc/seo-health-report-system/api:$TARGET_VERSION
docker pull ghcr.io/raaptechllc/seo-health-report-system/worker:$TARGET_VERSION
```

### 3. Deploy Previous Version

#### Using Kubernetes

```bash
TARGET_VERSION="v1.0.0"

# Rollback to previous revision
kubectl rollout undo deployment/api
kubectl rollout undo deployment/worker

# OR deploy specific version
kubectl set image deployment/api api=ghcr.io/raaptechllc/seo-health-report-system/api:$TARGET_VERSION
kubectl set image deployment/worker worker=ghcr.io/raaptechllc/seo-health-report-system/worker:$TARGET_VERSION

# Wait for rollout
kubectl rollout status deployment/api
kubectl rollout status deployment/worker
```

#### Using Docker Compose

```bash
TARGET_VERSION="v1.0.0"
export IMAGE_TAG=$TARGET_VERSION

# Update and restart
docker-compose pull
docker-compose up -d

# Verify
docker-compose ps
```

### 4. Verify Rollback

```bash
# Check health endpoint
curl -f https://api.seohealthreport.com/health

# Check version
curl https://api.seohealthreport.com/health | jq '.version'

# Check logs for errors
kubectl logs -l app=api --tail=100
```

## Database Rollback

⚠️ **Warning**: Database rollbacks can cause data loss. Only rollback if absolutely necessary.

### When to Rollback Database

- Migration introduced breaking schema changes
- Data corruption occurred
- Migration failed mid-way

### Database Rollback Steps

1. **Stop the application** to prevent further writes

2. **Check current migration status**
   ```bash
   ./scripts/run_migrations.sh status
   ```

3. **Restore from backup** (preferred)
   ```bash
   # List available backups
   ls -la backups/
   
   # Restore (PostgreSQL)
   pg_restore -d $DATABASE_URL backups/backup_YYYYMMDD_HHMMSS.sql
   ```

4. **OR rollback migration** (if no data loss is acceptable)
   ```bash
   # Rollback to specific version
   ./scripts/run_migrations.sh rollback v007
   ```

5. **Restart application with compatible version**

## Rollback Checklist

Before rollback:
- [ ] Confirm the issue requires rollback (not a quick fix)
- [ ] Identify the target version
- [ ] Notify the team
- [ ] Check if database rollback is needed

During rollback:
- [ ] Monitor deployment logs
- [ ] Watch for errors during rollback
- [ ] Have manual intervention plan ready

After rollback:
- [ ] Verify health checks pass
- [ ] Check key functionality works
- [ ] Monitor error rates
- [ ] Document the incident
- [ ] Plan the fix for the failed deployment

## Incident Documentation

After a rollback, document the incident:

```markdown
## Incident: [Date] - [Brief Description]

### Timeline
- HH:MM - Issue detected
- HH:MM - Rollback initiated
- HH:MM - Rollback completed

### Impact
- [User-facing impact]
- [Duration]

### Root Cause
- [What caused the issue]

### Resolution
- [Rollback steps taken]

### Follow-up Actions
- [ ] Fix root cause
- [ ] Add tests to prevent recurrence
- [ ] Update runbooks if needed
```

## Contact

If you need help with a rollback:

- **On-call**: Check PagerDuty/OpsGenie rotation
- **Slack**: #seo-health-alerts
- **Email**: ops@raaptech.com

## Prevention

To reduce the need for rollbacks:

1. **Test thoroughly in staging** before production
2. **Use feature flags** for risky changes
3. **Deploy during low-traffic periods**
4. **Monitor closely after deployment**
5. **Keep deployments small and frequent**
