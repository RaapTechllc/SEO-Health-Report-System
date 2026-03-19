# How Audits Work End-to-End

This document explains the complete audit lifecycle in the SEO Health Report System.

## Audit Lifecycle

Audits progress through the following statuses:

```
pending → queued → running → completed | failed
```

| Status | Description |
|--------|-------------|
| `pending` | Audit created but not yet picked up |
| `queued` | Added to job queue, waiting for worker |
| `running` | Worker is executing the audit |
| `completed` | All audits finished, report generated |
| `failed` | Audit encountered an error |
| `canceled` | Audit was manually cancelled |

## Three Audit Components

The system runs three parallel audits:

### 1. Technical Audit (30% weight)
- Site crawlability and indexability
- Page speed and Core Web Vitals
- Mobile responsiveness
- HTTPS and security
- Structured data validation
- XML sitemap and robots.txt

### 2. Content & Authority Audit (35% weight)
- Content quality analysis
- Keyword optimization
- Backlink profile
- Domain authority metrics
- E-E-A-T signals
- Internal linking structure

### 3. AI Visibility Audit (35% weight)
- Brand mentions in AI systems (ChatGPT, Claude, Perplexity)
- Citation accuracy
- Competitor comparison in AI responses
- Ground truth validation

## Scoring Formula

The overall score is calculated using weighted component scores:

```
Overall Score = (Technical × 0.30) + (Content × 0.35) + (AI Visibility × 0.35)
```

### Grade Mapping

| Score Range | Grade |
|-------------|-------|
| 90-100 | A |
| 80-89 | B |
| 70-79 | C |
| 60-69 | D |
| 0-59 | F |

Example calculation:
```
Technical Score: 85
Content Score: 72
AI Visibility Score: 68

Overall = (85 × 0.30) + (72 × 0.35) + (68 × 0.35)
        = 25.5 + 25.2 + 23.8
        = 74.5 → Grade C
```

## Job Queue Architecture

### Database Tables

**`audit_jobs` table:**
```sql
CREATE TABLE audit_jobs (
    id VARCHAR PRIMARY KEY,
    audit_id VARCHAR REFERENCES audits(id),
    job_type VARCHAR,
    payload JSON,
    status VARCHAR DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Worker Polling

Workers poll the job queue for available jobs:

```python
# Worker picks up next available job
job = db.execute("""
    SELECT * FROM audit_jobs 
    WHERE status = 'pending' 
    ORDER BY priority DESC, created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
""")
```

## Progress Events

Progress is tracked via the `audit_progress_events` table:

```sql
CREATE TABLE audit_progress_events (
    event_id VARCHAR PRIMARY KEY,
    audit_id VARCHAR,
    job_id VARCHAR,
    event_type VARCHAR,
    message TEXT,
    progress_pct INTEGER,
    created_at TIMESTAMP
);
```

### Progress Stages

| Stage | Progress % | Description |
|-------|-----------|-------------|
| `initializing` | 0% | Starting audit |
| `technical_audit` | 10% | Running technical SEO checks |
| `content_audit` | 30% | Analyzing content and authority |
| `ai_visibility_audit` | 50% | Querying AI systems |
| `generating_report` | 80% | Building HTML/PDF report |
| `completed` | 100% | Audit finished |
| `failed` | - | Audit encountered an error |

## API Endpoints

### Create Audit

```http
POST /audit
Content-Type: application/json
Authorization: Bearer <token>

{
  "url": "https://example.com",
  "company_name": "Example Corp",
  "keywords": ["seo", "marketing"],
  "competitors": ["https://competitor.com"],
  "tier": "pro",
  "callback_url": "https://your-app.com/webhook"
}
```

**Response:**
```json
{
  "audit_id": "aud_abc123",
  "status": "queued",
  "url": "https://example.com",
  "company_name": "Example Corp"
}
```

### Get Audit Status

```http
GET /audit/{audit_id}
```

**Response:**
```json
{
  "audit_id": "aud_abc123",
  "status": "completed",
  "url": "https://example.com",
  "company_name": "Example Corp",
  "tier": "pro",
  "overall_score": 74,
  "grade": "C",
  "created_at": "2025-01-18T10:00:00Z",
  "completed_at": "2025-01-18T10:05:32Z"
}
```

### Get Full Audit Results

```http
GET /audit/{audit_id}/full
```

Returns complete audit data including all component scores and detailed results.

### Get Progress Events

```http
GET /audits/{audit_id}/events
```

**Response:**
```json
{
  "audit_id": "aud_abc123",
  "events": [
    {
      "event_type": "initializing",
      "message": "Starting audit for https://example.com",
      "progress_pct": 0,
      "timestamp": "2025-01-18T10:00:00Z"
    },
    {
      "event_type": "technical_audit",
      "message": "Running technical SEO audit",
      "progress_pct": 10,
      "timestamp": "2025-01-18T10:00:05Z"
    }
  ]
}
```

### List All Audits

```http
GET /audits
```

Returns the 100 most recent audits.

## Audit Tiers

| Tier | Description | Features |
|------|-------------|----------|
| `basic` | Free tier | Core metrics, limited depth |
| `pro` | Professional | Full analysis, PDF reports |
| `enterprise` | Business | Custom branding, API access, priority |

## Error Handling

When an audit fails, the system:

1. Updates status to `failed`
2. Records error in `audit_progress_events`
3. Sends webhook notification (if callback_url provided)
4. Returns partial results if available

Failed audits can be retried by creating a new audit request.
