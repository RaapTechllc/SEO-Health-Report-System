# Webhook Integration Guide

This document explains how to receive audit notifications via webhooks.

## Overview

When an audit completes or fails, the system can send a webhook notification to your specified callback URL. This enables real-time integration with your applications.

## Setting Up Webhooks

### Include callback_url in Audit Request

```http
POST /audit
Content-Type: application/json
Authorization: Bearer <token>

{
  "url": "https://example.com",
  "company_name": "Example Corp",
  "callback_url": "https://your-app.com/webhooks/seo-audit"
}
```

The `callback_url` must be:
- A valid HTTP or HTTPS URL
- Publicly accessible
- Not pointing to private/internal IP addresses (SSRF protection)

## Webhook Payload

### Successful Audit

```json
{
  "event": "audit.completed",
  "audit_id": "aud_abc123",
  "status": "completed",
  "timestamp": "2025-01-18T10:05:32.123456Z",
  "overall_score": 74,
  "grade": "C",
  "report_url": "reports/default/aud_abc123.html"
}
```

### Failed Audit

```json
{
  "event": "audit.failed",
  "audit_id": "aud_abc123",
  "status": "failed",
  "timestamp": "2025-01-18T10:05:32.123456Z",
  "error": "Technical audit module timeout"
}
```

## Security: HMAC-SHA256 Signature

All webhook requests include a signature header for verification:

```
X-Webhook-Signature: 5d41402abc4b2a76b9719d911017c592
```

### How Signatures Are Generated

```python
import hmac
import hashlib
import json

def sign_webhook_payload(payload: dict, secret: str) -> str:
    body = json.dumps(payload, sort_keys=True, default=str)
    signature = hmac.new(
        secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    )
    return signature.hexdigest()
```

Key points:
- Payload is JSON-serialized with `sort_keys=True`
- HMAC-SHA256 algorithm
- Signature is hex-encoded

## Verifying Webhook Signatures

### Python Example

```python
import hmac
import hashlib
import json
from flask import Flask, request

app = Flask(__name__)
WEBHOOK_SECRET = "your-webhook-secret"

def verify_signature(payload: dict, signature: str) -> bool:
    """Verify the webhook signature."""
    body = json.dumps(payload, sort_keys=True, default=str)
    expected = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.route('/webhooks/seo-audit', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.get_json()
    
    if not signature or not verify_signature(payload, signature):
        return {'error': 'Invalid signature'}, 401
    
    # Process the webhook
    event = payload.get('event')
    audit_id = payload.get('audit_id')
    
    if event == 'audit.completed':
        score = payload.get('overall_score')
        grade = payload.get('grade')
        print(f"Audit {audit_id} completed: {score}/100 ({grade})")
    elif event == 'audit.failed':
        error = payload.get('error')
        print(f"Audit {audit_id} failed: {error}")
    
    return {'status': 'received'}, 200
```

### Node.js Example

```javascript
const crypto = require('crypto');
const express = require('express');
const app = express();

const WEBHOOK_SECRET = 'your-webhook-secret';

function verifySignature(payload, signature) {
  const body = JSON.stringify(payload, Object.keys(payload).sort());
  const expected = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(body)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(signature)
  );
}

app.post('/webhooks/seo-audit', express.json(), (req, res) => {
  const signature = req.headers['x-webhook-signature'];
  
  if (!signature || !verifySignature(req.body, signature)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  
  const { event, audit_id, overall_score, grade } = req.body;
  
  if (event === 'audit.completed') {
    console.log(`Audit ${audit_id} completed: ${overall_score}/100 (${grade})`);
  }
  
  res.json({ status: 'received' });
});
```

## Retry Policy

If webhook delivery fails, the system retries with exponential backoff:

| Attempt | Delay | Cumulative Time |
|---------|-------|-----------------|
| 1 | Immediate | 0s |
| 2 | ~1s | ~1s |
| 3 | ~2s | ~3s |
| 4 | ~4s | ~7s |
| 5 | ~8s | ~15s |

### Retry Behavior

- **Max attempts**: 5
- **Base delay**: 1 second
- **Max delay**: 60 seconds
- **Jitter**: ±10% randomization to prevent thundering herd

### What Triggers Retries

| Condition | Retried? |
|-----------|----------|
| Connection timeout | ✅ Yes |
| 5xx server error | ✅ Yes |
| 429 Too Many Requests | ✅ Yes |
| 2xx success | ❌ No (success) |
| 4xx client error (except 429) | ❌ No (permanent failure) |

## SSRF Protection

To prevent Server-Side Request Forgery attacks, callback URLs are validated:

### Blocked Addresses

- `localhost`, `127.0.0.1`
- Private IP ranges: `10.x.x.x`, `172.16-31.x.x`, `192.168.x.x`
- Link-local: `169.254.x.x`
- Loopback: `::1`

### Validation Process

```python
async def validate_callback_url(url: str) -> None:
    parsed = urlparse(url)
    
    # Check scheme
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"Invalid scheme: {parsed.scheme}")
    
    # Resolve DNS and check IP
    ip = resolve_dns(parsed.hostname)
    validate_ip(ip)  # Raises SSRFError if private
```

### Invalid URL Error

```json
{
  "success": false,
  "attempts": 0,
  "error": "Invalid callback URL: Private IP address not allowed"
}
```

## Webhook Headers

All webhook requests include these headers:

```http
POST /your-endpoint HTTP/1.1
Host: your-app.com
Content-Type: application/json
X-Webhook-Signature: <hmac-sha256-signature>
User-Agent: SEOHealthReport-Webhook/1.0
```

## Best Practices

### 1. Respond Quickly
Return a 2xx response within 10 seconds. Process webhook data asynchronously.

```python
@app.route('/webhooks/seo-audit', methods=['POST'])
def handle_webhook():
    # Verify signature first
    # ...
    
    # Queue for async processing
    task_queue.enqueue(process_audit_result, request.json)
    
    # Return immediately
    return {'status': 'received'}, 200
```

### 2. Handle Duplicates
Webhooks may be delivered more than once. Use `audit_id` for idempotency.

```python
def process_audit_result(payload):
    audit_id = payload['audit_id']
    
    # Check if already processed
    if redis.sismember('processed_webhooks', audit_id):
        return
    
    # Process...
    
    # Mark as processed
    redis.sadd('processed_webhooks', audit_id)
```

### 3. Store the Secret Securely
- Use environment variables
- Rotate secrets periodically
- Use different secrets per tenant/environment

### 4. Log Webhook Receipts
Keep an audit trail of received webhooks for debugging.

## Webhook Secret Configuration

The webhook secret is determined per-tenant:

```python
def get_webhook_secret(tenant_id: str) -> str:
    return os.getenv("WEBHOOK_SECRET", f"webhook-secret-{tenant_id}")
```

Configure via environment variable:
```bash
export WEBHOOK_SECRET="your-secure-random-secret"
```

## Delivery Tracking

Successful webhook delivery updates the audit record:

```sql
UPDATE audits 
SET callback_delivered_at = CURRENT_TIMESTAMP 
WHERE id = :audit_id
```

Query delivery status:

```http
GET /audit/{audit_id}
```

```json
{
  "audit_id": "aud_abc123",
  "status": "completed",
  "callback_delivered_at": "2025-01-18T10:05:35Z"
}
```
