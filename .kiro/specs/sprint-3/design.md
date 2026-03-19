# Sprint 3: Technical Design

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   API       │     │  Postgres   │     │   Worker    │
│  (FastAPI)  │────▶│   (Jobs)    │◀────│  (Polling)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    │                   │
       │              ┌─────┴─────┐             │
       │              │ audits    │             │
       │              │ result_json│            │
       │              │ report_*  │             │
       │              └───────────┘             │
       │                                        │
       │         ┌──────────────────────────────┤
       │         │                              │
       │    ┌────┴────┐    ┌─────────────┐    ┌─┴───────────┐
       │    │ Rate    │    │  Audit      │    │  Report     │
       │    │ Limiter │    │  Handlers   │    │  Generator  │
       │    └─────────┘    └─────────────┘    └─────────────┘
       │                          │
       │                   ┌──────┴──────┐
       │                   │ orchestrate │
       │                   │ .py         │
       │                   └─────────────┘
       │                          │
       │              ┌───────────┼───────────┐
       │              ▼           ▼           ▼
       │         technical   content    ai_visibility
       │         audit       audit      audit
       │
       └──────────────────────▶ Webhook Callback
```

## Design Decisions

### D1: Single Job = Full Audit
One `audit_job` runs the complete orchestrated audit (technical + content + AI visibility) and generates reports.

**Rationale**: Simplest integration with current queue. Avoids building a DAG/sub-jobs system.

### D2: Store Raw + Normalized Results
```python
audits.result_json = {
    "raw": {
        "technical": {...},  # Direct output from technical audit
        "content": {...},    # Direct output from content audit
        "ai_visibility": {...}  # Direct output from AI visibility audit
    },
    "summary": AuditResult.to_dict()  # Normalized for UI/API stability
}
```

**Rationale**: Existing modules return inconsistent structures; this avoids refactoring all modules in Sprint 3.

### D3: Report Storage Pattern
```
storage/{tenant_id}/{audit_id}/report.html
storage/{tenant_id}/{audit_id}/report.pdf
```

**Rationale**: Predictable retrieval, easy cleanup, uses existing storage abstraction.

### D4: Rate Limiting Without New Dependencies
```python
# Global concurrency
fetch_semaphore = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)

# Per-host throttling
host_last_request: Dict[str, float] = {}
host_lock = asyncio.Lock()

async def throttled_fetch(url: str, min_delay: float = 0.5):
    host = urlparse(url).netloc
    
    async with host_lock:
        last = host_last_request.get(host, 0)
        wait = max(0, min_delay - (time.time() - last))
        if wait > 0:
            await asyncio.sleep(wait)
        host_last_request[host] = time.time()
    
    async with fetch_semaphore:
        return await safe_fetch(url)
```

### D5: Webhook Callback Security
```python
def sign_webhook_payload(payload: dict, secret: str) -> str:
    """HMAC-SHA256 signature for webhook verification."""
    body = json.dumps(payload, sort_keys=True)
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

async def deliver_webhook(callback_url: str, payload: dict, secret: str):
    # Validate callback URL (block private IPs)
    parsed = urlparse(callback_url)
    ip = await resolve_dns(parsed.hostname)
    validate_ip(ip)  # Reuse SSRF protection
    
    signature = sign_webhook_payload(payload, secret)
    headers = {"X-Webhook-Signature": signature}
    
    # Retry with backoff
    for attempt in range(5):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(callback_url, json=payload, headers=headers)
                if response.status_code < 400:
                    return True
        except Exception:
            pass
        await asyncio.sleep(calculate_backoff(attempt))
    
    return False  # Failed after retries
```

## Full Audit Handler Design

```python
async def handle_full_audit(
    audit_id: str,
    job_id: str,
    payload: dict,
    db_session
) -> dict:
    """
    Execute full SEO audit with all components.
    """
    url = payload["url"]
    company_name = payload.get("company_name", "")
    keywords = payload.get("keywords", [])
    competitors = payload.get("competitors", [])
    
    # Progress: Initializing
    await write_progress(db_session, audit_id, job_id, 
                         ProgressStage.INITIALIZING, 0, "Starting audit")
    
    # Run full audit via orchestrator
    # Progress events emitted during run_full_audit
    raw_result = await run_full_audit(
        target_url=url,
        company_name=company_name,
        primary_keywords=keywords,
        competitor_urls=competitors,
        progress_callback=lambda stage, pct, msg: 
            write_progress(db_session, audit_id, job_id, stage, pct, msg)
    )
    
    # Calculate composite score
    scores = calculate_composite_score(raw_result)
    
    # Build canonical AuditResult
    audit_result = AuditResult(
        audit_id=audit_id,
        url=url,
        company_name=company_name,
        tier=AuditTier(payload.get("tier", "basic")),
        status=AuditStatus.COMPLETED,
        overall_score=scores["overall_score"],
        grade=calculate_grade(scores["overall_score"]),
        technical_score=scores.get("component_scores", {}).get("technical"),
        content_score=scores.get("component_scores", {}).get("content"),
        ai_visibility_score=scores.get("component_scores", {}).get("ai_visibility"),
        issues=collect_all_issues(raw_result),
        recommendations=collect_all_recommendations(raw_result),
    )
    
    # Progress: Generating report
    await write_progress(db_session, audit_id, job_id,
                         ProgressStage.GENERATING_REPORT, 90, "Generating report")
    
    # Generate reports
    html_path = await generate_html_report(audit_result, payload.get("tenant_id"))
    pdf_path = await generate_pdf_report(audit_result, payload.get("tenant_id"))
    
    audit_result.report_path = html_path
    
    # Store result
    result_json = {
        "raw": raw_result,
        "summary": audit_result.to_dict()
    }
    
    # Update audit record
    update_audit_record(db_session, audit_id, audit_result, html_path, pdf_path)
    
    # Progress: Completed
    await write_progress(db_session, audit_id, job_id,
                         ProgressStage.COMPLETED, 100, "Audit completed")
    
    # Webhook callback (if configured)
    if callback_url := payload.get("callback_url"):
        await deliver_webhook(callback_url, {
            "audit_id": audit_id,
            "status": "completed",
            "overall_score": audit_result.overall_score,
            "grade": audit_result.grade.value,
            "report_url": html_path,
        }, get_webhook_secret(payload.get("tenant_id")))
    
    return result_json
```

## Rate Limiter Design

```python
# packages/seo_health_report/scripts/rate_limiter.py

from dataclasses import dataclass, field
from typing import Dict
import asyncio
import time

@dataclass
class RateLimiterConfig:
    """Rate limiting configuration per tier."""
    max_concurrent_fetches: int = 5
    min_host_delay_seconds: float = 0.5
    max_requests_per_minute: int = 60

TIER_LIMITS = {
    "basic": RateLimiterConfig(max_concurrent_fetches=3, min_host_delay_seconds=1.0),
    "pro": RateLimiterConfig(max_concurrent_fetches=5, min_host_delay_seconds=0.5),
    "enterprise": RateLimiterConfig(max_concurrent_fetches=10, min_host_delay_seconds=0.25),
}

class RateLimiter:
    """Rate limiter for external HTTP requests."""
    
    def __init__(self, config: RateLimiterConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_concurrent_fetches)
        self.host_last_request: Dict[str, float] = {}
        self.host_lock = asyncio.Lock()
    
    async def acquire(self, host: str) -> None:
        """Acquire rate limit slot for a host."""
        # Per-host delay
        async with self.host_lock:
            last = self.host_last_request.get(host, 0)
            wait = max(0, self.config.min_host_delay_seconds - (time.time() - last))
            if wait > 0:
                await asyncio.sleep(wait)
            self.host_last_request[host] = time.time()
        
        # Global concurrency
        await self.semaphore.acquire()
    
    def release(self) -> None:
        """Release rate limit slot."""
        self.semaphore.release()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass

async def rate_limited_fetch(url: str, limiter: RateLimiter) -> FetchResult:
    """Fetch with rate limiting applied."""
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    
    await limiter.acquire(host)
    try:
        return await safe_fetch(url)
    finally:
        limiter.release()
```

## API Endpoints

### Progress Events Endpoint
```python
@app.get("/audits/{audit_id}/events")
async def get_audit_events(audit_id: str, db: Session = Depends(get_db)):
    """Get progress events for an audit."""
    events = db.execute(
        text('''
            SELECT event_type, message, progress_pct, created_at
            FROM audit_progress_events
            WHERE audit_id = :audit_id
            ORDER BY created_at
        '''),
        {"audit_id": audit_id}
    ).fetchall()
    
    return {
        "audit_id": audit_id,
        "events": [
            {
                "event_type": e[0],
                "message": e[1],
                "progress_pct": e[2],
                "timestamp": e[3].isoformat()
            }
            for e in events
        ]
    }
```

### Report Download Endpoint
```python
@app.get("/audits/{audit_id}/report/{format}")
async def get_audit_report(
    audit_id: str,
    format: str,  # "html" or "pdf"
    db: Session = Depends(get_db)
):
    """Download audit report."""
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(404, "Audit not found")
    
    if format == "html":
        path = audit.report_html_path
        media_type = "text/html"
    elif format == "pdf":
        path = audit.report_pdf_path
        media_type = "application/pdf"
    else:
        raise HTTPException(400, "Invalid format")
    
    if not path or not os.path.exists(path):
        raise HTTPException(404, "Report not available")
    
    return FileResponse(path, media_type=media_type)
```

## Database Schema Updates

```sql
-- Add report path columns to audits
ALTER TABLE audits ADD COLUMN report_html_path VARCHAR(500);
ALTER TABLE audits ADD COLUMN report_pdf_path VARCHAR(500);
ALTER TABLE audits ADD COLUMN callback_url VARCHAR(500);
ALTER TABLE audits ADD COLUMN callback_delivered_at TIMESTAMP;

-- Add webhook delivery log (optional, for debugging)
CREATE TABLE webhook_deliveries (
    id VARCHAR(36) PRIMARY KEY,
    audit_id VARCHAR(36) NOT NULL REFERENCES audits(id),
    callback_url VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- pending, delivered, failed
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP,
    response_status INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## File Structure

```
apps/
├── api/
│   └── routes/
│       ├── audits.py          # Audit endpoints
│       └── reports.py         # Report download endpoints
├── worker/
│   ├── handlers/
│   │   ├── hello_audit.py     # Keep for diagnostics
│   │   ├── full_audit.py      # NEW: Real audit handler
│   │   └── webhook.py         # NEW: Webhook delivery
│   └── rate_limiter.py        # NEW: Rate limiting
├── dashboard/                  # NEW: Minimal UI
│   ├── templates/
│   │   ├── audit_list.html
│   │   └── audit_detail.html
│   └── routes.py
packages/
├── seo_health_report/
│   └── scripts/
│       ├── rate_limiter.py    # Rate limiting utilities
│       └── webhook.py         # Webhook signing/delivery
infrastructure/
└── migrations/
    └── versions/
        └── v004_report_columns.py  # NEW
```

## Lease Renewal for Long Audits

```python
async def handle_full_audit_with_lease_renewal(...):
    """Wrapper that renews lease during long-running audit."""
    
    async def lease_renewal_task():
        while True:
            await asyncio.sleep(LEASE_SECONDS // 2)
            await renew_lease(job_id, worker_id, LEASE_SECONDS)
    
    renewal_task = asyncio.create_task(lease_renewal_task())
    try:
        return await handle_full_audit(...)
    finally:
        renewal_task.cancel()
        try:
            await renewal_task
        except asyncio.CancelledError:
            pass
```
