# SEO Health Report System

A comprehensive SEO audit system that generates branded health reports by orchestrating technical, content, and AI visibility audits.

## 🤖 Ralph Loop Multi-Agent System

This project now includes an autonomous Ralph Loop multi-agent system that can execute the entire development workflow without human intervention. Each specialized agent operates in continuous loops, picking tasks, executing them, and updating progress until all work is complete.

### Quick Start - Ralph Loop System

```bash
# Start the autonomous multi-agent system
./start-ralph.sh

# Monitor progress in real-time
python3 progress-tracker.py monitor

# Stop the system
./stop-ralph.sh
```

The Ralph Loop system will autonomously:
1. **Foundation Phase**: Set up infrastructure and agent configurations
2. **Backend Phase**: Implement database, API, and business logic
3. **Frontend Phase**: Build user interface and real-time features
4. **Testing Phase**: Create comprehensive test suites
5. **Documentation Phase**: Generate user and developer docs
6. **DevOps Phase**: Set up CI/CD and production deployment

### Ralph Loop Agents

| Agent | Specialization | Tasks |
|-------|---------------|-------|
| **devops-automator** | Infrastructure, CI/CD, deployment | Ralph Loop infrastructure, CI/CD pipeline, production setup |
| **agent-creator** | Agent configuration and management | Update all agent configs for Ralph Loop compatibility |
| **db-wizard** | Database design and optimization | Schema design, migrations, query optimization |
| **code-surgeon** | Code quality and security | API implementation, business logic, security review |
| **frontend-designer** | UI/UX and React components | Dashboard, forms, real-time updates |
| **test-architect** | Testing and quality assurance | Unit tests, integration tests, E2E tests |
| **doc-smith** | Documentation and guides | User docs, API docs, architecture docs |

### System Monitoring

```bash
# View current status
python3 progress-tracker.py

# Monitor in real-time
python3 progress-tracker.py monitor

# Check individual agent tasks
python3 task-picker.py devops-automator

# View system logs
tail -f logs/coordinator.log
tail -f ralph-loop.log
```

### Ralph Loop Completion

The system automatically completes when:
- ✅ All 16 tasks in PLAN.md are marked DONE
- ✅ All 7 agents emit `<promise>DONE</promise>`
- ✅ All acceptance criteria are verified
- ✅ Integration tests pass

---

## What Makes This Different

**AI Visibility Audit** - While competitors focus on traditional SEO, this system evaluates how brands appear in AI-generated responses (ChatGPT, Claude, Perplexity). This is your moat.

## System Architecture

```
seo-health-report/           # Master orchestrator
├── ai-visibility-audit/     # AI system presence analysis
├── seo-technical-audit/     # Technical SEO analysis
└── seo-content-authority/   # Content & authority analysis
```

## Skills Overview

### 1. AI Visibility Audit (`ai-visibility-audit/`)
Evaluates brand visibility in AI systems:
- Queries Claude, ChatGPT, Perplexity with brand-related questions
- Analyzes mention rates, sentiment, and accuracy
- Checks website parseability for AI crawlers
- Evaluates knowledge graph presence
- Scores content citation likelihood

**Score Weight: 35%** (differentiator)

### 2. SEO Technical Audit (`seo-technical-audit/`)
Analyzes technical SEO foundations:
- Crawlability (robots.txt, sitemaps, internal links)
- Page speed (Core Web Vitals via PageSpeed API)
- Security (HTTPS, headers, mixed content)
- Mobile optimization (viewport, responsive design)
- Structured data (JSON-LD validation)

**Score Weight: 30%** (foundation)

### 3. SEO Content Authority (`seo-content-authority/`)
Evaluates content quality and authority:
- Content analysis (thin content, keyword optimization)
- E-E-A-T signals (author pages, credentials, trust signals)
- Topic cluster mapping (hub pages, internal linking)
- Link profile analysis (backlinks, domain authority)

**Score Weight: 35%** (most impactful for rankings)

### 4. SEO Health Report (`seo-health-report/`)
Master orchestrator that:
- Runs all three sub-audits
- Calculates composite scores with weighted averaging
- Generates branded DOCX/PDF reports
- Applies client logos and brand colors
- Produces executive summaries with quick wins

## Production Readiness

✅ **Phase 1 Complete**: All production hardening tasks complete
- HTML parsing enabled (BeautifulSoup4, lxml, textstat, nltk)
- Structured logging throughout codebase
- Centralized configuration management
- Basic test suite (150+ unit tests)
- All hardcoded values migrated to config

**Maturity Score**: 90/100 (up from 75/100)

## Installation

```bash
# Clone or copy the project
cd seo-health-report

# Install dependencies for all skills
pip install -r seo-health-report/requirements.txt
pip install -r ai-visibility-audit/requirements.txt
pip install -r seo-technical-audit/requirements.txt
pip install -r seo-content-authority/requirements.txt

# Set API keys (required for AI visibility)
export ANTHROPIC_API_KEY="your-key-here"

# Optional API keys for enhanced functionality
export OPENAI_API_KEY="your-key-here"        # ChatGPT queries
export PERPLEXITY_API_KEY="your-key-here"    # Perplexity queries
export GOOGLE_API_KEY="your-key-here"        # PageSpeed Insights
```

## Webhooks

The system supports webhooks for real-time notifications when audits complete or fail.

### Registering a Webhook

```bash
curl -X POST https://api.example.com/webhooks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["audit.completed", "audit.failed"]
  }'
```

### Webhook Events

| Event | Description |
|-------|-------------|
| `audit.completed` | Fired when an audit finishes successfully |
| `audit.failed` | Fired when an audit fails |

### Payload Format

```json
{
  "event": "audit.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "audit_id": "audit_abc123",
    "url": "https://example.com",
    "company_name": "Example Corp",
    "tier": "pro",
    "score": 85,
    "grade": "B"
  }
}
```

### Security

Webhooks are signed using HMAC-SHA256. Verify the `X-Webhook-Signature` header:

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Tenant Branding

Customize reports with your brand identity.

### API Endpoints

- `GET /tenant/branding` - Get current branding
- `PATCH /tenant/branding` - Update branding
- `DELETE /tenant/branding` - Reset to defaults

### Configuration Options

| Field | Description | Format |
|-------|-------------|--------|
| `logo_url` | URL to your logo image | HTTPS URL |
| `primary_color` | Primary brand color | Hex (#RRGGBB) |
| `secondary_color` | Secondary brand color | Hex (#RRGGBB) |
| `footer_text` | Custom footer text | String |

### Example

```bash
curl -X PATCH https://api.example.com/tenant/branding \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "logo_url": "https://example.com/logo.png",
    "primary_color": "#1E3A8A",
    "footer_text": "Powered by Your Company"
  }'
```

## Observability

### Metrics

The system exposes Prometheus-compatible metrics at `/metrics`:

```
# Audit metrics
audit_total{tier="pro",status="completed"} 150
audit_duration_seconds_bucket{tier="pro",le="60"} 120
active_audits 3

# HTTP metrics
http_requests_total{method="GET",status="200"} 5000
http_request_duration_seconds_bucket{le="0.1"} 4500
```

### Structured Logging

All logs are output in JSON format with request correlation:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Audit completed",
  "request_id": "req-abc123",
  "user_id": "user-xyz",
  "audit_id": "audit-456"
}
```

### Admin Dashboard

Administrators can access `/admin/health` for a real-time system health dashboard showing:
- Active audits
- Error rate
- Average completion time

## Python SDK

Use the official SDK for programmatic access:

```python
from packages.seo_health_sdk import SEOHealthClient

client = SEOHealthClient(
    base_url="https://api.example.com",
    api_key="YOUR_API_KEY"
)

# Start an audit
audit = client.create_audit(
    url="https://example.com",
    company_name="Example Corp",
    tier="pro"
)

# Check status
status = client.get_audit(audit.audit_id)

# List webhooks
webhooks = client.list_webhooks()
```

## Usage

### Python API

```python
from seo_health_report import generate_report

result = generate_report(
    target_url="https://example.com",
    company_name="Example Corp",
    logo_file="./logo.png",
    primary_keywords=["example service", "example product"],
    brand_colors={"primary": "#1a73e8", "secondary": "#34a853"},
    competitor_urls=["https://competitor1.com", "https://competitor2.com"],
    output_format="docx",
    output_dir="./reports"
)

print(f"Score: {result['overall_score']}/100 (Grade: {result['grade']})")
print(f"Report: {result['report']['output_path']}")
```

### Command Line

```bash
python -m seo_health_report \
    --url https://example.com \
    --company "Example Corp" \
    --logo ./logo.png \
    --keywords "example service, example product" \
    --competitors "https://competitor1.com, https://competitor2.com" \
    --format docx \
    --output ./reports/example-report.docx
```

### Individual Audits

```python
# Run just AI visibility audit
from ai_visibility_audit import run_audit as ai_audit

result = ai_audit(
    brand_name="Example Corp",
    target_url="https://example.com",
    products_services=["consulting", "software"]
)

# Run just technical audit
from seo_technical_audit import run_audit as tech_audit

result = tech_audit(
    target_url="https://example.com",
    depth=50
)

# Run just content/authority audit
from seo_content_authority import run_audit as content_audit

result = content_audit(
    target_url="https://example.com",
    primary_keywords=["example service"]
)
```

## Scoring System

### Composite Score Calculation

```
Overall Score = (Technical × 0.30) + (Content × 0.35) + (AI × 0.35)
```

### Grade Mapping

| Grade | Score Range | Description |
|-------|-------------|-------------|
| A | 90-100 | Excellent - Industry leader |
| B | 80-89 | Good - Above average performance |
| C | 70-79 | Average - Room for improvement |
| D | 60-69 | Below Average - Significant gaps |
| F | 0-59 | Poor - Urgent attention needed |

### Component Scores

Each audit produces a score out of 100 based on multiple factors:

**AI Visibility (100 points)**
- AI Presence: 25 points
- Response Accuracy: 20 points
- Sentiment: 15 points
- Parseability: 15 points
- Knowledge Graph: 10 points
- Citation Likelihood: 15 points

**Technical (100 points)**
- Crawlability: 25 points
- Page Speed: 25 points
- Security: 20 points
- Mobile: 15 points
- Structured Data: 15 points

**Content/Authority (100 points)**
- Content Quality: 30 points
- E-E-A-T Signals: 25 points
- Topic Authority: 20 points
- Link Profile: 25 points

## Output Report Structure

1. **Cover Page** - Branded with client logo
2. **Executive Summary** - Grade, key findings, quick wins
3. **Score Dashboard** - Visual representation of all scores
4. **Technical Audit Details** - Crawl issues, speed metrics, security
5. **Content Audit Details** - Quality analysis, E-E-A-T evaluation
6. **AI Visibility Details** - AI mention analysis, parseability
7. **Recommendations** - Prioritized action items
8. **Appendix** - Detailed data and methodology

## Project Structure

```
seo-health-report/
├── README.md                    # This file
├── ai-visibility-audit/
│   ├── SKILL.md                 # Skill definition
│   ├── README.md                # Skill documentation
│   ├── __init__.py              # Entry point
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── query_ai_systems.py  # AI system queries
│   │   ├── analyze_responses.py # Response analysis
│   │   ├── check_parseability.py# AI crawler readiness
│   │   ├── check_knowledge.py   # Knowledge graph presence
│   │   └── score_citability.py  # Citation likelihood
│   └── references/
│       ├── scoring_rubric.md
│       ├── query_templates.md
│       └── ai_optimization.md
├── seo-technical-audit/
│   ├── SKILL.md
│   ├── README.md
│   ├── __init__.py
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── crawl_site.py        # Site crawling
│   │   ├── analyze_speed.py     # Core Web Vitals
│   │   ├── check_security.py    # Security headers
│   │   └── validate_schema.py   # Structured data
│   └── references/
│       ├── scoring_rubric.md
│       └── fix_templates.md
├── seo-content-authority/
│   ├── SKILL.md
│   ├── README.md
│   ├── __init__.py
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── analyze_content.py   # Content quality
│   │   ├── check_eeat.py        # E-E-A-T signals
│   │   ├── map_topics.py        # Topic clusters
│   │   └── analyze_links.py     # Link profile
│   └── references/
│       └── eeat_checklist.md
└── seo-health-report/
    ├── SKILL.md
    ├── README.md
    ├── __init__.py
    ├── requirements.txt
    └── scripts/
        ├── orchestrate.py       # Runs all audits
        ├── calculate_scores.py  # Composite scoring
        ├── generate_summary.py  # Executive summary
        ├── build_report.py      # Document generation
        └── apply_branding.py    # Logo/color application
```

## API Keys Required

| Service | Required | Purpose |
|---------|----------|---------|
| Anthropic | Yes | Claude API for AI visibility queries and analysis |
| Google Gemini | No | Visual report generation, image creation, emoji formatting |
| OpenAI | No | ChatGPT queries (expands AI coverage) |
| Perplexity | No | Perplexity queries (expands AI coverage) |
| Google | No | PageSpeed Insights API |

### Multi-Model Architecture

The system uses different AI models for different tasks:

| Task | Model | Why |
|------|-------|-----|
| Analysis & Writing | Anthropic Claude | Best reasoning, nuanced writing |
| Visual Generation | Google Gemini/Imagen | Image gen, emoji formatting |
| AI Visibility Queries | Multiple | Coverage across AI systems |

```python
# Gemini integration for visual reports
from seo_health_report.scripts.gemini_integration import (
    generate_report_visuals,
    enhance_executive_summary,
)

# Generate infographics and visual assets
assets = generate_report_visuals_sync(audit_data, output_dir)

# Enhance summary with emojis and formatting
enhanced = enhance_executive_summary_sync(summary, company_name)
```

## Extending the System

### Adding New AI Systems

Edit `ai-visibility-audit/scripts/query_ai_systems.py`:

```python
def query_new_ai_system(query: str) -> Dict[str, Any]:
    # Implement your integration
    pass
```

### Adding New Technical Checks

Edit `seo-technical-audit/scripts/` and add new check modules.

### Customizing Report Templates

Edit `seo-health-report/scripts/build_report.py` to modify document structure.

## Development

```bash
# Run tests
pytest

# Format code
black .

# Type checking
mypy .
```

## License

Proprietary - All rights reserved.

## Support

For issues or feature requests, contact the development team.
