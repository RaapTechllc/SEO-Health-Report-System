# Sprint 5: Technical Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           API Layer                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   Webhooks   │  │   Branding   │  │   Metrics    │               │
│  │   /webhooks  │  │   /tenant    │  │   /metrics   │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
├─────────────────────────────────────────────────────────────────────┤
│                        Middleware                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   Logging    │  │   Metrics    │  │  Request ID  │               │
│  │   (JSON)     │  │  Collection  │  │  Propagation │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
├─────────────────────────────────────────────────────────────────────┤
│                        Services                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   Webhook    │  │   Branding   │  │   Metrics    │               │
│  │   Delivery   │  │   Service    │  │   Registry   │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
├─────────────────────────────────────────────────────────────────────┤
│                        Storage                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   Database   │  │   S3/Local   │  │   In-Memory  │               │
│  │  (webhooks)  │  │  (assets)    │  │  (metrics)   │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Designs

### 5.1 Structured Logging

**Implementation:** `packages/seo_health_report/logging/`

```python
# structured_logger.py
import json
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": request_id_var.get(""),
            "user_id": user_id_var.get(""),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
```

**Middleware:**
```python
# middleware/logging_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)
        
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        )
        
        response.headers["X-Request-ID"] = request_id
        return response
```

### 5.2 Metrics Collection

**Implementation:** `packages/seo_health_report/metrics/`

```python
# metrics_collector.py
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from time import time
from typing import Dict, List

@dataclass
class MetricsRegistry:
    _counters: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _histograms: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    _gauges: Dict[str, float] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)
    
    def inc_counter(self, name: str, labels: dict = None, value: int = 1):
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value
    
    def observe_histogram(self, name: str, value: float, labels: dict = None):
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
    
    def set_gauge(self, name: str, value: float, labels: dict = None):
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
    
    def prometheus_format(self) -> str:
        lines = []
        with self._lock:
            for key, value in self._counters.items():
                lines.append(f"{key} {value}")
            for key, values in self._histograms.items():
                if values:
                    lines.append(f"{key}_count {len(values)}")
                    lines.append(f"{key}_sum {sum(values)}")
            for key, value in self._gauges.items():
                lines.append(f"{key} {value}")
        return "\n".join(lines)
    
    def _make_key(self, name: str, labels: dict = None) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

metrics = MetricsRegistry()
```

**Key Metrics:**
- `http_requests_total{method, path, status}` - Request counter
- `http_request_duration_seconds{method, path}` - Request latency histogram
- `audit_total{tier, status}` - Audit counter
- `audit_duration_seconds{tier}` - Audit completion time
- `webhook_deliveries_total{status}` - Webhook delivery counter
- `active_audits` - Gauge of running audits

### 5.3 Webhook System

**Database Schema:**
```python
# Add to database.py
class Webhook(Base):
    __tablename__ = "webhooks"
    
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=False)  # HMAC signing secret
    events = Column(JSON, nullable=False)  # ["audit.completed", "audit.failed"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant")

class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    
    id = Column(String(36), primary_key=True)
    webhook_id = Column(String(36), ForeignKey("webhooks.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")  # pending, delivered, failed
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    response_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Webhook Service:**
```python
# packages/seo_health_report/webhooks/service.py
import hashlib
import hmac
import httpx
from datetime import datetime

class WebhookService:
    MAX_RETRIES = 3
    RETRY_DELAYS = [60, 300, 900]  # 1min, 5min, 15min
    
    def sign_payload(self, payload: str, secret: str) -> str:
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def deliver(self, webhook: Webhook, event_type: str, payload: dict) -> bool:
        payload_json = json.dumps(payload)
        signature = self.sign_payload(payload_json, webhook.secret)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Event": event_type,
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook.url, content=payload_json, headers=headers)
            return response.status_code < 400
```

### 5.4 Tenant Branding

**Database Schema:**
```python
# Add to database.py or Tenant model
class TenantBranding(Base):
    __tablename__ = "tenant_branding"
    
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), unique=True, nullable=False)
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), default="#1E3A8A")  # hex color
    secondary_color = Column(String(7), default="#3B82F6")
    footer_text = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant")
```

**Report Integration:**
```python
# Update report generation to check branding
def get_report_branding(tenant_id: str | None) -> dict:
    if not tenant_id:
        return DEFAULT_BRANDING
    
    branding = db.query(TenantBranding).filter_by(tenant_id=tenant_id).first()
    if not branding:
        return DEFAULT_BRANDING
    
    return {
        "logo_url": branding.logo_url or DEFAULT_BRANDING["logo_url"],
        "primary_color": branding.primary_color,
        "secondary_color": branding.secondary_color,
        "footer_text": branding.footer_text or DEFAULT_BRANDING["footer_text"],
    }
```

### 5.5 API Documentation

**OpenAPI Enhancements:**
```python
# apps/api/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="SEO Health Report API",
    description="""
    ## Overview
    The SEO Health Report API provides comprehensive SEO auditing capabilities.
    
    ## Authentication
    All endpoints (except /health) require a Bearer token.
    Obtain a token via POST /auth/login.
    
    ## Rate Limits
    - Basic tier: 100 requests/hour, 5 audits/day
    - Pro tier: 500 requests/hour, 25 audits/day
    - Enterprise tier: 2000 requests/hour, 100 audits/day
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

## File Structure

```
packages/seo_health_report/
├── logging/
│   ├── __init__.py
│   ├── structured_logger.py
│   └── middleware.py
├── metrics/
│   ├── __init__.py
│   ├── collector.py
│   └── middleware.py
├── webhooks/
│   ├── __init__.py
│   ├── models.py
│   ├── service.py
│   └── router.py
├── branding/
│   ├── __init__.py
│   ├── models.py
│   ├── service.py
│   └── router.py

apps/api/
├── routers/
│   ├── webhooks.py
│   ├── branding.py
│   └── metrics.py
```

## API Endpoints

### Webhooks
| Method | Path | Description |
|--------|------|-------------|
| POST | /webhooks | Register new webhook |
| GET | /webhooks | List tenant webhooks |
| GET | /webhooks/{id} | Get webhook details |
| DELETE | /webhooks/{id} | Delete webhook |
| GET | /webhooks/{id}/deliveries | List delivery attempts |

### Branding
| Method | Path | Description |
|--------|------|-------------|
| GET | /tenant/branding | Get current branding |
| PATCH | /tenant/branding | Update branding |
| POST | /tenant/branding/logo | Upload logo |
| DELETE | /tenant/branding/logo | Remove logo |

### Metrics
| Method | Path | Description |
|--------|------|-------------|
| GET | /metrics | Prometheus metrics |
| GET | /admin/health | Health dashboard (admin) |

## Security Considerations

1. **Webhook URL Validation:** Reuse SSRF protection from Sprint 4
2. **Logo Upload:** Validate file type, max size 2MB, scan for malicious content
3. **HMAC Secrets:** Generate cryptographically secure secrets (32 bytes)
4. **Metrics Endpoint:** Consider authentication for production
