# Coding Standards

## Python Style

- Use Python 3.9+ features
- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Format with `black`
- Type check with `mypy`

## File Organization

Each skill module follows this structure:
```
skill-name/
├── SKILL.md           # Skill definition with frontmatter
├── README.md          # Detailed documentation
├── __init__.py        # Entry point, exports main functions
├── requirements.txt   # Dependencies
├── scripts/           # Implementation modules
│   └── __init__.py
├── references/        # Reference docs (rubrics, templates)
└── assets/            # Templates, images
```

## Function Patterns

### Audit Functions
```python
def run_audit(
    target_url: str,
    **options
) -> Dict[str, Any]:
    """
    Returns dict with:
    - score: int (0-100)
    - grade: str (A-F)
    - components: Dict[str, ComponentScore]
    - findings: List[Finding]
    - recommendations: List[Recommendation]
    """
```

### Score Components
```python
@dataclass
class ComponentScore:
    score: int
    max: int
    findings: List[str]
```

## Error Handling

- Use specific exceptions for different failure modes
- Always provide fallback behavior when external APIs fail
- Log errors with context for debugging
- Return partial results when possible

## Testing

- Run tests with `pytest`
- Test each script module independently
- Mock external API calls in tests


## Input Validation

- Validate inputs at function boundaries
- Return safe defaults for invalid inputs (don't raise)
- Use bounds checking: `clamped = min(max(value, 0), 100)`
- Document expected input formats in docstrings

## Optional Dependencies

When adding optional dependencies, use graceful import pattern:
```python
try:
    from .optional_module import feature
    HAS_FEATURE = True
except ImportError:
    feature = None
    HAS_FEATURE = False
```

## Exception Handling Best Practices

- Never use bare `except:` or `except Exception: pass`
- Catch specific exceptions: `except (IOError, OSError) as e:`
- Always log with context: `print(f"Warning: {operation} failed: {e}")`
