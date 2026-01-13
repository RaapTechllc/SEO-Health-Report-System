# SEO Health Report - Test Suite

## Overview

Comprehensive test suite for SEO Health Report system with 215+ tests covering:

**Unit Tests (172 tests)**:
- Cache functionality
- Logging configuration
- Configuration management
- Orchestration logic
- Score calculation
- Async operations
- Issue and recommendation handling

**Integration Tests (43 tests)**:
- Full audit pipeline E2E
- Report generation (Markdown, DOCX, PDF)
- CLI interface
- Data flow validation
- Error handling

## Running Tests

### Prerequisites

```bash
# Install package in development mode (required for testing)
pip install -e .
pip install -e seo-technical-audit
pip install -e ai-visibility-audit
pip install -e seo-content-authority

# Install test dependencies
pip install pytest pytest-cov
```

### Run All Tests

```bash
# Run all tests (unit + integration)
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/ --cov=seo_health_report --cov=seo_technical_audit --cov=ai_visibility_audit --cov=seo_content_authority --cov-report=html
```

### Run Specific Test Files

```bash
# Run only config tests
pytest tests/unit/test_config.py -v

# Run only logger tests
pytest tests/unit/test_logger.py -v

# Run only cache tests
pytest tests/unit/test_cache.py -v
```

### Run Specific Test Classes

```bash
# Run only config default tests
pytest tests/unit/test_config.py::TestConfigDefaults -v

# Run only scoring tests
pytest tests/unit/test_calculate_scores.py::TestCalculateCompositeScore -v
```

### Run Specific Tests

```bash
# Run single test
pytest tests/unit/test_config.py::TestConfigDefaults::test_api_timeout_default -v

# Run multiple tests
pytest tests/unit/test_config.py -k "api_timeout or cache_ttl" -v
```

## Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures and configuration
├── __init__.py
├── unit/                          # Fast, isolated unit tests
│   ├── test_async_operations.py   # Async function tests
│   ├── test_cache.py              # Cache functionality tests
│   ├── test_calculate_scores.py   # Score calculation tests
│   ├── test_config.py             # Configuration management tests
│   ├── test_logger.py             # Logger configuration tests
│   ├── test_new_fixtures.py       # Fixture validation tests
│   └── test_orchestrate.py        # Orchestration logic tests
└── integration/                   # End-to-end integration tests
    ├── __init__.py
    ├── test_full_audit.py         # Full audit pipeline E2E
    ├── test_report_generation.py  # Report generation tests
    └── test_cli.py                # CLI interface tests
```

## Fixtures

Available fixtures in `conftest.py`:

- `mock_config` - Config instance for testing
- `sample_audit_results` - Sample audit results
- `sample_scores` - Sample scores data
- `sample_issues` - Sample issues list
- `sample_recommendations` - Sample recommendations list
- `sample_brand_colors` - Sample brand colors dict
- `mock_http_response` - Mock HTTP response class
- `temp_dir` - Temporary directory for file operations

## Test Coverage

Current coverage targets:
- Unit tests: 60%+ (achieved)
- Integration tests: Complete (43 tests)
- E2E tests: Complete

Run coverage report:
```bash
pytest tests/ --cov --cov-report=term-missing
```

## Test Markers

Tests can be marked with:
- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (external dependencies)
- `@pytest.mark.slow` - Slow tests (network, long runtime)

Run specific markers:
```bash
# Run only unit tests
pytest -m unit -v

# Run only integration tests
pytest -m integration -v

# Skip slow tests
pytest -m "not slow" -v
```

## Known Limitations

1. **Package Naming**: Tests require package installation because `seo-health-report` has a hyphen in the name, making direct import difficult.

2. **Network Tests**: Tests requiring network (API calls, external services) are marked as `@pytest.mark.slow` and may need API keys.

3. **External Dependencies**: Some tests are skipped if optional dependencies (diskcache, reportlab) are not installed.

## Troubleshooting

### ModuleNotFoundError: No module named 'seo_health_report'

**Solution**: Install packages in development mode:
```bash
pip install -e .
pip install -e seo-technical-audit
pip install -e ai-visibility-audit
pip install -e seo-content-authority
```

### ImportError: No module named 'diskcache'

**Solution**: Install diskcache or tests will fallback gracefully:
```bash
pip install diskcache>=5.6.0
```

### ImportError: No module named 'reportlab'

**Solution**: Install reportlab or tests will skip PDF-related tests:
```bash
pip install reportlab>=4.0.0
```

## Adding New Tests

1. Create test file in appropriate directory
2. Import required fixtures from conftest.py
3. Write test methods following naming convention `test_*`
4. Add docstrings describing what is being tested
5. Run `pytest tests/` to verify new tests pass

Example:
```python
"""
Tests for new_module.
"""

import pytest
from seo_health_report.scripts.new_module import function_to_test

class TestNewModule:
    def test_basic_functionality(self):
        \"\"\"Test that function works correctly.\"\"\"
        result = function_to_test("input")
        assert result == "expected_output"
```

## CI/CD Integration

For GitHub Actions or other CI/CD:

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          pip install -e .
          pip install pytest pytest-cov pytest-asyncio
          pytest tests/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Integration Test Details

### test_full_audit.py
Tests the complete audit pipeline from input to output:
- Audit result structure validation
- Score calculation integration
- Executive summary generation
- Placeholder result handling
- Issue and recommendation collection
- Data flow through pipeline

### test_report_generation.py
Tests report generation for all formats:
- Markdown report generation
- DOCX generation (or fallback)
- PDF generation (or fallback)
- Brand color application
- Section structure validation
- Edge cases (empty data, special characters)

### test_cli.py
Tests command-line interface:
- Argument parsing
- Output formatting
- Module exports
- Error handling
