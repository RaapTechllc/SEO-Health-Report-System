# SEO Health Report System

A comprehensive SEO audit system that generates branded health reports by orchestrating technical, content, and AI visibility audits.

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
| Anthropic | Yes | Claude API for AI visibility queries |
| OpenAI | No | ChatGPT queries (expands AI coverage) |
| Perplexity | No | Perplexity queries (expands AI coverage) |
| Google | No | PageSpeed Insights API |

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
