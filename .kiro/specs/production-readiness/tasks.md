# Production Readiness - Implementation Tasks

## Overview
Minimal MVP to accept payments and run audits with data persistence.

**Total Estimated Time:** 3-4 days
**Goal:** Live-testable payment → audit → report flow

---

## PHASE 1: Database Persistence (Day 1 Morning)

### Task 1.1: Create SQLite Database Schema (30 min)
- [ ] Create `database.py` with SQLAlchemy models
- [ ] Tables: users, audits, payments
- [ ] Auto-create DB on first run
- [ ] Add migration support

**Acceptance Criteria:**
- `python -c "from database import init_db; init_db()"` creates `seo_health.db`
- Tables exist with correct columns

### Task 1.2: Migrate API to Use Database (45 min)
- [ ] Replace `audit_results = {}` with DB queries
- [ ] Replace `competitors = {}` with DB queries
- [ ] Add CRUD functions for audits
- [ ] Data persists across server restarts

**Acceptance Criteria:**
- Start server, create audit, restart server, audit still exists
- `GET /audits` returns audits from database

---

## PHASE 2: Authentication (Day 1 Afternoon)

### Task 2.1: Add User Model and JWT Auth (45 min)
- [ ] Create `auth.py` with JWT functions
- [ ] Add `/auth/register` endpoint
- [ ] Add `/auth/login` endpoint
- [ ] Return JWT token on success

**Acceptance Criteria:**
- `POST /auth/register` creates user, returns token
- `POST /auth/login` validates credentials, returns token

### Task 2.2: Protect API Endpoints (30 min)
- [ ] Create `get_current_user` dependency
- [ ] Protect `/audit` endpoints (require auth)
- [ ] Keep `/health` and `/` public
- [ ] Associate audits with user_id

**Acceptance Criteria:**
- `POST /audit` without token returns 401
- `POST /audit` with valid token creates audit for that user
- `GET /audits` returns only current user's audits

---

## PHASE 3: Stripe Payment Integration (Day 2)

### Task 3.1: Create Stripe Checkout Flow (45 min)
- [ ] Create `payments.py` with Stripe client
- [ ] Add `/checkout/create` endpoint
- [ ] Support 3 tiers: basic ($800), pro ($2500), enterprise ($6000)
- [ ] Return Stripe checkout URL

**Acceptance Criteria:**
- `POST /checkout/create {"tier": "basic"}` returns checkout URL
- Clicking URL shows Stripe checkout page

### Task 3.2: Handle Stripe Webhooks (45 min)
- [ ] Add `/webhooks/stripe` endpoint
- [ ] Verify webhook signature
- [ ] On `checkout.session.completed`: create audit record
- [ ] Store payment_intent_id in payments table

**Acceptance Criteria:**
- Completing Stripe checkout triggers webhook
- Audit record created with status "pending"
- Payment recorded in database

### Task 3.3: Trigger Audit on Payment Success (30 min)
- [ ] Queue audit job when payment succeeds
- [ ] Update audit status: pending → running → completed
- [ ] Store tier in audit record

**Acceptance Criteria:**
- Payment success → audit starts automatically
- Audit result stored in database
- User can retrieve completed audit

---

## PHASE 4: Rate Limiting & Security (Day 3 Morning)

### Task 4.1: Add Rate Limiting (30 min)
- [ ] Create `rate_limiter.py` using in-memory store
- [ ] Limit: 100 requests/hour per IP
- [ ] Limit: 10 audits/day per user
- [ ] Return 429 when exceeded

**Acceptance Criteria:**
- 101st request in an hour returns 429
- 11th audit request in a day returns 429

### Task 4.2: Input Validation & Security Headers (30 min)
- [ ] Add URL validation (reject invalid URLs)
- [ ] Add security headers middleware
- [ ] Sanitize all user inputs
- [ ] Add request logging

**Acceptance Criteria:**
- Invalid URL returns 400 with clear error
- Response headers include security headers
- All requests logged with timestamp, IP, endpoint

---

## PHASE 5: Environment & Deployment (Day 3 Afternoon)

### Task 5.1: Production Configuration (30 min)
- [ ] Create `config.py` with environment detection
- [ ] Separate dev/prod settings
- [ ] Add all secrets to `.env.example`
- [ ] Validate required env vars on startup

**Acceptance Criteria:**
- Missing `STRIPE_SECRET_KEY` in prod → startup error
- Dev mode uses SQLite, prod can use PostgreSQL
- All secrets loaded from environment

### Task 5.2: Create Production Dockerfile (30 min)
- [ ] Create `Dockerfile` for API server
- [ ] Create `docker-compose.yml` for local testing
- [ ] Include health check
- [ ] Optimize for small image size

**Acceptance Criteria:**
- `docker-compose up` starts working API
- Health check passes
- Image size < 500MB

---

## PHASE 6: End-to-End Testing (Day 4)

### Task 6.1: Create E2E Test Script (45 min)
- [ ] Create `tests/e2e/test_payment_flow.py`
- [ ] Test: register → login → pay → audit → report
- [ ] Use Stripe test mode
- [ ] Verify all steps complete

**Acceptance Criteria:**
- Full flow completes in test mode
- Audit result matches expected structure
- PDF report generated

### Task 6.2: Manual Smoke Test Checklist (30 min)
- [ ] Document manual test steps
- [ ] Test with real Stripe test card
- [ ] Verify webhook delivery
- [ ] Test error scenarios

**Acceptance Criteria:**
- Checklist covers all critical paths
- All manual tests pass
- Error messages are user-friendly

---

## File Structure (New Files)

```
├── database.py          # SQLAlchemy models, DB init
├── auth.py              # JWT auth, user management
├── payments.py          # Stripe integration
├── rate_limiter.py      # Request rate limiting
├── config.py            # Environment configuration (update existing)
├── Dockerfile           # Production container
├── docker-compose.yml   # Local development
└── tests/e2e/
    └── test_payment_flow.py
```

---

## Environment Variables (Add to .env)

```bash
# Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...

# Database
DATABASE_URL=sqlite:///./seo_health.db

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_HOUR=100
RATE_LIMIT_AUDITS_PER_DAY=10
```

---

## Success Criteria

### MVP Complete When:
- [ ] User can register and login
- [ ] User can select tier and pay via Stripe
- [ ] Payment triggers automatic audit
- [ ] User can view audit results
- [ ] User can download PDF report
- [ ] Data persists across restarts
- [ ] Rate limiting prevents abuse

### Performance Targets:
- API response < 500ms
- Audit completion < 5 min (basic tier)
- PDF generation < 30 seconds
