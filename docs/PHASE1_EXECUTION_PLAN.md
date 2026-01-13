# Phase 1: Production Hardening - Execution Plan

## Overview
Transform the SEO Health Report project from 75/100 maturity to production-ready state.

## Target State
- All dependencies enabled and working
- Structured logging throughout
- Centralized configuration management
- Basic test framework in place
- Production-ready error handling

---

## Task 1: Enable HTML Parsing (2 hours)

### Why
BeautifulSoup4 is commented out but required for proper content analysis in all modules.

### Actions

#### 1.1 Update seo-health-report/requirements.txt
- [ ] Uncomment beautifulsoup4>=4.12.0
- [ ] Uncomment lxml>=4.9.0
- [ ] Validate: pip install -r seo-health-report/requirements.txt

#### 1.2 Update seo-technical-audit/requirements.txt
- [ ] Uncomment beautifulsoup4>=4.12.0
- [ ] Uncomment lxml>=4.9.0
- [ ] Validate: pip install -r seo-technical-audit/requirements.txt

#### 1.3 Update ai-visibility-audit/requirements.txt
- [ ] Uncomment beautifulsoup4>=4.12.0
- [ ] Uncomment lxml>=4.9.0
- [ ] Validate: pip install -r ai-visibility-audit/requirements.txt

#### 1.4 Update seo-content-authority/requirements.txt
- [ ] Uncomment beautifulsoup4>=4.12.0
- [ ] Add textstat>=0.7.0
- [ ] Add nltk>=3.8.0
- [ ] Validate: pip install -r seo-content-authority/requirements.txt

#### 1.5 Verify HTML parsing works
```bash
python -c "from bs4 import BeautifulSoup; print('BeautifulSoup4 installed')"
python -c "import lxml; print('lxml installed')"
```

### Success Criteria
- [ ] All BeautifulSoup4 imports uncommented
- [ ] All packages install without errors
- [ ] Test imports succeed

---

## Task 2: Add Structured Logging (3 hours)

### Why
70+ print statements throughout codebase. Need proper logging for production debugging and monitoring.

### Actions

#### 2.1 Create seo-health-report/scripts/logger.py
- [ ] Create logger configuration module
- [ ] Implement get_logger() function
- [ ] Add configurable log levels
- [ ] Add log formatting
- [ ] Add file rotation support
- [ ] Pattern:
```python
import logging
from logging.handlers import RotatingFileHandler
import os

def get_logger(name: str = "seo_health_report", level: str = "INFO") -> logging.Logger:
    """Get configured logger instance."""
```

#### 2.2 Replace print statements in seo-health-report/__init__.py
- [ ] Replace 8 print statements with logger calls
- [ ] Add import: from .scripts.logger import get_logger
- [ ] Initialize logger at module level
- [ ] Map prints to appropriate log levels (INFO, WARNING, ERROR)

#### 2.3 Replace print statements in seo-health-report/scripts/orchestrate.py
- [ ] Replace 6 print statements with logger calls
- [ ] Add import: from .logger import get_logger
- [ ] Initialize logger for orchestrate module

#### 2.4 Replace print statements in seo-health-report/scripts/build_report.py
- [ ] Replace 3 print statements with logger calls
- [ ] Add import: from .logger import get_logger

#### 2.5 Replace print statements in other modules
- [ ] seo-technical-audit/scripts/crawl_site.py: 2 prints
- [ ] ai-visibility-audit/scripts/check_parseability.py: 2 prints
- [ ] seo-health-report/scripts/pdf_components.py: 1 print

#### 2.6 Add environment variable for log level
- [ ] Support SEO_HEALTH_LOG_LEVEL env var
- [ ] Default to INFO
- [ ] Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

#### 2.7 Add log directory
- [ ] Create logs/ directory if it doesn't exist
- [ ] Configure log file: logs/seo-health-report.log
- [ ] Set rotation: 10MB, keep 5 files

### Success Criteria
- [ ] All print statements replaced with logger calls
- [ ] Log file created in logs/ directory
- [ ] Log level configurable via env var
- [ ] No print statements remaining in production code paths

---

## Task 3: Configuration Management (3 hours)

### Why
Hardcoded values scattered throughout (colors, timeouts, URLs). Need centralized config.

### Actions

#### 3.1 Create seo-health-report/config.py
- [ ] Create configuration management module
- [ ] Implement Config class with:
  - API timeouts
  - Default colors
  - Cache TTL values
  - File paths
  - API endpoints
- [ ] Support environment variable overrides
- [ ] Pattern:
```python
import os
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Config:
    """Centralized configuration for SEO Health Report."""
    api_timeout: int = 30
    cache_ttl_pagespeed: int = 86400
    default_colors: Dict[str, str] = None
```

#### 3.2 Migrate hardcoded values from apply_branding.py
- [ ] Move DEFAULT_COLORS dict to config.py
- [ ] Update apply_branding.py to import from config
- [ ] Add tests for color parsing

#### 3.3 Migrate hardcoded values from cache.py
- [ ] Move TTL constants to config.py
- [ ] Update cache.py to import from config
- [ ] Keep backward compatibility

#### 3.4 Migrate hardcoded values from other modules
- [ ] AI model names in query_ai_systems.py
- [ ] API endpoints in analyze_speed.py
- [ ] Scoring thresholds in calculate_scores.py
- [ ] Request timeouts in crawl_site.py

#### 3.5 Create seo-health-report/.env.example
- [ ] Create example environment file
- [ ] Document all required env vars:
  - ANTHROPIC_API_KEY
  - OPENAI_API_KEY (optional)
  - PERPLEXITY_API_KEY (optional)
  - GOOGLE_API_KEY (optional)
  - SEO_HEALTH_LOG_LEVEL
  - SEO_HEALTH_CACHE_DIR

#### 3.6 Add config validation
- [ ] Validate required API keys on startup
- [ ] Warn about missing optional keys
- [ ] Provide helpful error messages

#### 3.7 Update main entry point
- [ ] Load config on module import
- [ ] Make config available via seo_health_report.config
- [ ] Document configuration in README

### Success Criteria
- [ ] All hardcoded values centralized
- [ ] Config class properly documented
- [ ] Environment variable overrides work
- [ ] .env.example created with all documented variables
- [ ] No hardcoded values remaining in core modules

---

## Task 4: Basic Test Suite (4 hours)

### Why
No test framework in place. Need basic tests for reliability and confidence.

### Actions

#### 4.1 Setup test framework
- [ ] Uncomment pytest>=7.0.0 in all requirements files
- [ ] Uncomment black>=23.0.0 in all requirements files
- [ ] Uncomment mypy>=1.0.0 in all requirements files
- [ ] Install pytest: pip install pytest pytest-cov

#### 4.2 Create test structure
- [ ] Create tests/ directory
- [ ] Create tests/__init__.py
- [ ] Create tests/conftest.py (pytest fixtures)
- [ ] Create subdirectories: tests/unit/, tests/integration/

#### 4.3 Create conftest.py with fixtures
- [ ] Mock config fixture
- [ ] Mock logger fixture
- [ ] Sample data fixtures (test URLs, mock API responses)
- [ ] Mock HTTP responses fixture

#### 4.4 Write tests for cache.py (tests/unit/test_cache.py)
- [ ] Test cache decorator with diskcache installed
- [ ] Test cache fallback when diskcache not installed
- [ ] Test cache bypass flag
- [ ] Test cache key generation
- [ ] Test cache invalidation

#### 4.5 Write tests for logger.py (tests/unit/test_logger.py)
- [ ] Test logger initialization
- [ ] Test log level configuration
- [ ] Test log formatting
- [ ] Test file handler rotation

#### 4.6 Write tests for config.py (tests/unit/test_config.py)
- [ ] Test default values
- [ ] Test environment variable overrides
- [ ] Test color parsing
- [ ] Test validation

#### 4.7 Write tests for orchestrate.py (tests/unit/test_orchestrate.py)
- [ ] Test create_placeholder_result()
- [ ] Test extract_domain()
- [ ] Test collect_all_issues()
- [ ] Test collect_all_recommendations()
- [ ] Test identify_quick_wins()
- [ ] Test identify_critical_issues()

#### 4.8 Write tests for calculate_scores.py (tests/unit/test_calculate_scores.py)
- [ ] Test overall score calculation
- [ ] Test grade mapping
- [ ] Test component score weighting
- [ ] Test score clamping

#### 4.9 Create pytest.ini configuration
- [ ] Configure test discovery
- [ ] Configure coverage reporting
- [ ] Configure markers (unit, integration, slow)
- [ ] Set default test options

#### 4.10 Create tests/README.md
- [ ] Document how to run tests
- [ ] Document test structure
- [ ] Document fixtures
- [ ] Document adding new tests

#### 4.11 Run test suite
- [ ] pytest tests/ -v
- [ ] pytest tests/ --cov
- [ ] Verify coverage report

### Success Criteria
- [ ] Test framework installed and configured
- [ ] At least 20 unit tests created
- [ ] All tests pass
- [ ] Coverage > 60% for core modules
- [ ] pytest.ini configured
- [ ] Tests documented

---

## Validation & Testing (1 hour)

### Actions

#### 5.1 Full integration test
```bash
# Clean install
pip install -r seo-health-report/requirements.txt
pip install -r seo-technical-audit/requirements.txt
pip install -r ai-visibility-audit/requirements.txt
pip install -r seo-content-authority/requirements.txt

# Run tests
pytest tests/ -v

# Test imports
python -c "from seo_health_report import generate_report"
python -c "from seo_health_report.config import Config"
python -c "from seo_health_report.scripts.logger import get_logger"
```

#### 5.2 Smoke test - Generate a report
```bash
python -c "
from seo_health_report import generate_report
result = generate_report(
    target_url='https://example.com',
    company_name='Test Corp',
    logo_file='',
    primary_keywords=['test'],
    output_format='markdown',
    output_dir='./output'
)
print(f'Score: {result[\"overall_score\"]}')
print(f'Report: {result[\"report\"][\"output_path\"]}')
"
```

#### 5.3 Check for remaining print statements
```bash
grep -r "print(" --include="*.py" seo-health-report/ seo-technical-audit/ ai-visibility-audit/ seo-content-authority/ | grep -v test | grep -v "#"
```

#### 5.4 Verify logging works
```bash
# Set debug logging
export SEO_HEALTH_LOG_LEVEL=DEBUG
python -c "
from seo_health_report.scripts.logger import get_logger
logger = get_logger('test')
logger.debug('Debug message')
logger.info('Info message')
logger.warning('Warning message')
logger.error('Error message')
"
# Check logs/seo-health-report.log
```

### Success Criteria
- [ ] All validation commands pass
- [ ] Smoke test generates report
- [ ] No print statements in production code
- [ ] Logging works at all levels
- [ ] Tests pass with >60% coverage

---

## Documentation Updates (30 minutes)

### Actions

#### 6.1 Update README.md
- [ ] Document new dependencies
- [ ] Document logging configuration
- [ ] Document environment variables
- [ ] Document how to run tests
- [ ] Update installation instructions

#### 6.2 Update DEVLOG.md
- [ ] Add entry for Phase 1 completion
- [ ] Document what was changed
- [ ] Document decisions made
- [ ] List any known issues

#### 6.3 Create CONTRIBUTING.md
- [ ] Document code style (black)
- [ ] Document running tests
- [ ] Document adding new features
- [ ] Document debugging with logs

### Success Criteria
- [ ] README updated with new information
- [ ] DEVLOG entry created
- [ ] CONTRIBUTING.md created

---

## Final Checklist

### Dependencies
- [ ] BeautifulSoup4 enabled and working
- [ ] lxml enabled and working
- [ ] textstat enabled and working
- [ ] nltk enabled and working
- [ ] pytest enabled and working
- [ ] black enabled and working
- [ ] mypy enabled and working

### Logging
- [ ] All print statements replaced
- [ ] Log file created
- [ ] Log level configurable
- [ ] Proper error messages

### Configuration
- [ ] All hardcoded values centralized
- [ ] Config class implemented
- [ ] Environment variables supported
- [ ] .env.example created

### Testing
- [ ] Test framework setup
- [ ] At least 20 unit tests
- [ ] All tests pass
- [ ] Coverage > 60%

### Documentation
- [ ] README updated
- [ ] DEVLOG updated
- [ ] CONTRIBUTING.md created

### Production Readiness
- [ ] No import errors
- [ ] No breaking changes
- [ ] All validation commands pass
- [ ] Smoke test works
- [ ] Project ready for production

---

## Estimated Timeline
- Task 1 (HTML Parsing): 2 hours
- Task 2 (Logging): 3 hours
- Task 3 (Configuration): 3 hours
- Task 4 (Testing): 4 hours
- Task 5 (Validation): 1 hour
- Task 6 (Documentation): 0.5 hours

**Total: 13.5 hours**

---

## Next Steps (Phase 2)
Once Phase 1 is complete, we can proceed to:
1. Competitor Dashboard
2. Scheduled Audits
3. Performance Optimization
4. Advanced Error Handling
