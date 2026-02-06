# Sprint 2: Technical Design

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   API       │     │  Postgres   │     │   Worker    │
│  (FastAPI)  │────▶│   (Jobs)    │◀────│  (Polling)  │
└─────────────┘     └─────────────┘     └─────────────┘
      │                    │                   │
      │              ┌─────┴─────┐             │
      │              │  Tables   │             │
      │              │-----------│             │
      │              │audit_jobs │             │
      │              │progress   │             │
      │              │events     │             │
      │              └───────────┘             │
      │                                        │
      └────────────────────────────────────────┘
                    safe_fetch()
                         │
                    ┌────┴────┐
                    │ SSRF    │
                    │ Filter  │
                    └─────────┘
```

## Database Schema

### audit_jobs Table
```sql
CREATE TABLE audit_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    audit_id UUID NOT NULL REFERENCES audits(id),
    
    -- State machine
    status VARCHAR(20) NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'done', 'failed', 'canceled')),
    
    -- Retry handling
    attempt INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 3,
    
    -- Timestamps
    queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    
    -- Lease management (prevents double-processing)
    locked_until TIMESTAMPTZ,
    locked_by VARCHAR(255),
    
    -- Idempotency
    idempotency_key VARCHAR(64) NOT NULL UNIQUE,
    
    -- Payload
    payload_json JSONB NOT NULL,
    
    -- Error tracking (redacted)
    last_error TEXT,
    
    -- Indexes
    CONSTRAINT valid_timestamps CHECK (
        (started_at IS NULL OR started_at >= queued_at) AND
        (finished_at IS NULL OR finished_at >= started_at)
    )
);

CREATE INDEX idx_jobs_claimable ON audit_jobs (queued_at)
    WHERE status = 'queued' OR (status = 'running' AND locked_until < NOW());
CREATE INDEX idx_jobs_tenant ON audit_jobs (tenant_id, queued_at DESC);
```

### audit_progress_events Table
```sql
CREATE TABLE audit_progress_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL REFERENCES audits(id),
    job_id UUID REFERENCES audit_jobs(job_id),
    
    -- Event data
    event_type VARCHAR(50) NOT NULL
        CHECK (event_type IN ('status_changed', 'step_started', 'step_done', 
                              'warning', 'error', 'metric')),
    message TEXT,  -- redacted
    data_json JSONB,  -- redacted
    progress_pct SMALLINT CHECK (progress_pct BETWEEN 0 AND 100),
    
    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Index for timeline queries
    CONSTRAINT no_future_events CHECK (created_at <= NOW() + INTERVAL '1 minute')
);

CREATE INDEX idx_events_audit_timeline ON audit_progress_events (audit_id, created_at);
```

## Worker Design

### Job Claim Algorithm (Postgres Leasing)
```python
async def claim_job(worker_id: str, lease_seconds: int = 300) -> Optional[AuditJob]:
    """
    Atomically claim a job using SELECT FOR UPDATE SKIP LOCKED.
    
    This prevents double-processing even with multiple workers.
    """
    query = """
    UPDATE audit_jobs
    SET 
        status = 'running',
        started_at = COALESCE(started_at, NOW()),
        locked_until = NOW() + INTERVAL '%s seconds',
        locked_by = $1,
        attempt = attempt + 1
    WHERE job_id = (
        SELECT job_id FROM audit_jobs
        WHERE 
            (status = 'queued')
            OR (status = 'running' AND locked_until < NOW())  -- expired lease
        ORDER BY queued_at
        FOR UPDATE SKIP LOCKED
        LIMIT 1
    )
    RETURNING *
    """
    return await db.fetch_one(query, worker_id, lease_seconds)
```

### Worker Loop
```python
async def worker_loop(worker_id: str):
    while not shutdown_requested:
        job = await claim_job(worker_id)
        
        if job is None:
            await asyncio.sleep(POLL_INTERVAL)
            continue
        
        try:
            await execute_job(job)
            await mark_job_done(job.job_id)
        except TransientError as e:
            if job.attempt < job.max_attempts:
                await mark_job_queued(job.job_id, backoff(job.attempt))
            else:
                await mark_job_failed(job.job_id, redact(str(e)))
        except Exception as e:
            await mark_job_failed(job.job_id, redact(str(e)))
```

## Safe Fetch Design

### SSRF Protection Layers
```python
BLOCKED_RANGES = [
    # IPv4
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private
    ipaddress.ip_network("172.16.0.0/12"),    # Private
    ipaddress.ip_network("192.168.0.0/16"),   # Private
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local (AWS metadata)
    ipaddress.ip_network("0.0.0.0/8"),        # Current network
    # IPv6
    ipaddress.ip_network("::1/128"),          # Loopback
    ipaddress.ip_network("fc00::/7"),         # Unique local
    ipaddress.ip_network("fe80::/10"),        # Link-local
]

async def safe_fetch(
    url: str,
    *,
    timeout: float = 30.0,
    max_bytes: int = 10_000_000,
    max_redirects: int = 5,
    user_agent: str = "SEOHealthBot/1.0"
) -> FetchResult:
    """
    Fetch URL with SSRF protections.
    
    Validates:
    1. Scheme is http or https
    2. No credentials in URL
    3. Resolved IP is not in blocked ranges
    4. Every redirect hop is re-validated
    """
    # Validate scheme
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFError(f"Blocked scheme: {parsed.scheme}")
    
    # Reject credentials in URL
    if parsed.username or parsed.password:
        raise SSRFError("Credentials in URL not allowed")
    
    # Resolve and validate IP
    ip = await resolve_dns(parsed.hostname)
    validate_ip(ip)  # Raises SSRFError if blocked
    
    # Fetch with redirect validation
    response = await http_client.get(
        url,
        timeout=timeout,
        max_redirects=0,  # Handle manually
        headers={"User-Agent": user_agent}
    )
    
    redirects = 0
    while response.is_redirect and redirects < max_redirects:
        location = response.headers.get("location")
        # Re-validate redirect target
        redirect_ip = await resolve_dns(urlparse(location).hostname)
        validate_ip(redirect_ip)
        response = await http_client.get(location, ...)
        redirects += 1
    
    return FetchResult(
        url=str(response.url),
        status_code=response.status_code,
        content=response.content[:max_bytes],
        headers=dict(response.headers)
    )
```

## Idempotency Design

### Key Computation
```python
def compute_idempotency_key(
    tenant_id: str,
    target_url: str,
    options: dict,
    recipe_version: str = "v1"
) -> str:
    """
    Compute deterministic hash for audit request.
    
    Canonicalization rules:
    - URL: lowercase scheme/host, strip default ports, normalize trailing slash
    - Options: sort keys, remove None values
    - Include recipe version to invalidate when logic changes
    """
    canonical_url = canonicalize_url(target_url)
    canonical_options = json.dumps(options, sort_keys=True, default=str)
    
    payload = f"{tenant_id}|{canonical_url}|{canonical_options}|{recipe_version}"
    return hashlib.sha256(payload.encode()).hexdigest()[:64]

def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    
    # Lowercase scheme and host
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower()
    
    # Strip default ports
    port = parsed.port
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None
    
    # Normalize path (remove trailing slash except for root)
    path = parsed.path.rstrip("/") or "/"
    
    # Rebuild without fragment
    netloc = host + (f":{port}" if port else "")
    return f"{scheme}://{netloc}{path}"
```

## Redaction Design

```python
REDACTION_PATTERNS = [
    (r"(?i)(api[_-]?key|token|secret|password|auth)['\"]?\s*[:=]\s*['\"]?[\w\-\.]+", "[REDACTED]"),
    (r"(?i)authorization:\s*bearer\s+[\w\-\.]+", "Authorization: Bearer [REDACTED]"),
    (r"(?i)cookie:\s*.+", "Cookie: [REDACTED]"),
    (r"(?i)set-cookie:\s*.+", "Set-Cookie: [REDACTED]"),
]

def redact_sensitive(text: str) -> str:
    """Remove secrets from text before logging/storing."""
    result = text
    for pattern, replacement in REDACTION_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result

def redact_dict(data: dict) -> dict:
    """Recursively redact sensitive values in nested dict."""
    sensitive_keys = {"api_key", "token", "secret", "password", "authorization", "cookie"}
    
    result = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = redact_dict(value)
        elif isinstance(value, str):
            result[key] = redact_sensitive(value)
        else:
            result[key] = value
    return result
```

## File Structure

```
apps/
├── api/
│   └── routes/
│       └── audits.py          # POST /audits enqueue endpoint
├── worker/
│   ├── __init__.py
│   ├── main.py                # Worker entrypoint
│   ├── executor.py            # Job execution logic
│   └── handlers/
│       └── hello_audit.py     # Hello audit handler
packages/
├── shared-schemas/
│   └── jobs.py                # AuditJob, ProgressEvent models
├── seo_health_report/
│   └── scripts/
│       ├── safe_fetch.py      # SSRF-protected HTTP client
│       ├── redaction.py       # Sensitive data redaction
│       └── idempotency.py     # Audit hash computation
infrastructure/
└── migrations/
    ├── 002_audit_jobs.sql
    └── 003_progress_events.sql
```

## Error Handling

### Transient vs Permanent Errors
```python
class TransientError(Exception):
    """Retry-able errors: timeouts, 429, 503, network issues."""
    pass

class PermanentError(Exception):
    """Non-retry-able: 404, invalid URL, SSRF blocked."""
    pass

# In handler:
try:
    result = await safe_fetch(url)
except httpx.TimeoutException:
    raise TransientError("Timeout fetching URL")
except SSRFError as e:
    raise PermanentError(f"SSRF blocked: {e}")
```
