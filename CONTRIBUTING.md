# Contributing to SEO Health Report

## Development Setup

```bash
# Clone the repository
git clone https://github.com/raaptech/seo-health-report.git
cd seo-health-report

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r seo-health-report/requirements.txt
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Project Structure

```
seo-health-report/     # Master orchestrator
seo-technical-audit/   # Technical SEO analysis
seo-content-authority/ # Content & authority
ai-visibility-audit/   # AI system presence
frontend/              # React dashboard
tests/                 # Test suites
```

## Code Standards

- Python 3.9+ with type hints
- Format with `black`, lint with `ruff`
- Run `pytest` before submitting PRs
- Follow existing patterns in codebase

## Pull Request Process

1. Create feature branch from `develop`
2. Write tests for new functionality
3. Ensure all tests pass
4. Update documentation if needed
5. Submit PR with clear description

## API Keys for Testing

Copy `.env.example` to `.env.local` and add your keys:
- `ANTHROPIC_API_KEY` - Required
- `GOOGLE_API_KEY` - Optional (Gemini, PageSpeed)
- `OPENAI_API_KEY` - Optional
