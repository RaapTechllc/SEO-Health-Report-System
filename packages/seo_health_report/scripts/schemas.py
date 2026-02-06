"""
Data Contracts for SEO Health Report System.

Defines Pydantic models for type-safe data exchange between modules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class Severity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Priority(str, Enum):
    """Recommendation priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Effort(str, Enum):
    """Implementation effort levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Grade(str, Enum):
    """Score grade mapping."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"
    NA = "N/A"


class AuditStatus(str, Enum):
    """Audit execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


@dataclass
class Issue:
    """Represents a single audit issue."""
    description: str
    severity: Severity = Severity.MEDIUM
    source: str = ""
    category: str = ""
    url: Optional[str] = None
    details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "severity": self.severity.value if isinstance(self.severity, Severity) else self.severity,
            "source": self.source,
            "category": self.category,
            "url": self.url,
            "details": self.details or {},
        }


@dataclass
class Recommendation:
    """Represents a single recommendation."""
    action: str
    priority: Priority = Priority.MEDIUM
    impact: str = "medium"
    effort: Effort = Effort.MEDIUM
    source: str = ""
    category: str = ""
    details: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "priority": self.priority.value if isinstance(self.priority, Priority) else self.priority,
            "impact": self.impact,
            "effort": self.effort.value if isinstance(self.effort, Effort) else self.effort,
            "source": self.source,
            "category": self.category,
            "details": self.details,
        }


@dataclass
class ComponentScore:
    """Score for a single audit component."""
    name: str
    score: int
    max_score: int = 100
    weight: float = 1.0
    issues: list[Issue] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        return (self.score / self.max_score) * 100 if self.max_score > 0 else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "max_score": self.max_score,
            "weight": self.weight,
            "percentage": self.percentage,
            "issues": [i.to_dict() for i in self.issues],
            "findings": self.findings,
        }


@dataclass
class AuditResult:
    """Result from a single audit type."""
    audit_type: str
    score: Optional[int] = None
    grade: Grade = Grade.NA
    status: AuditStatus = AuditStatus.COMPLETED
    components: dict[str, ComponentScore] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_type": self.audit_type,
            "score": self.score,
            "grade": self.grade.value if isinstance(self.grade, Grade) else self.grade,
            "status": self.status.value if isinstance(self.status, AuditStatus) else self.status,
            "components": {k: v.to_dict() for k, v in self.components.items()},
            "issues": [i.to_dict() for i in self.issues],
            "findings": self.findings,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class CompetitorData:
    """Competitor analysis data."""
    url: str
    name: str
    domain: str
    scores: dict[str, int] = field(default_factory=dict)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "name": self.name,
            "domain": self.domain,
            "scores": self.scores,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


@dataclass
class FullAuditResult:
    """Complete audit result with all three audit types."""
    url: str
    company_name: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    overall_score: Optional[int] = None
    overall_grade: Grade = Grade.NA
    audits: dict[str, AuditResult] = field(default_factory=dict)
    competitors: list[CompetitorData] = field(default_factory=list)
    quick_wins: list[Recommendation] = field(default_factory=list)
    critical_issues: list[Issue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "company_name": self.company_name,
            "timestamp": self.timestamp,
            "overall_score": self.overall_score,
            "overall_grade": self.overall_grade.value if isinstance(self.overall_grade, Grade) else self.overall_grade,
            "audits": {k: v.to_dict() for k, v in self.audits.items()},
            "competitors": [c.to_dict() for c in self.competitors],
            "quick_wins": [r.to_dict() for r in self.quick_wins],
            "critical_issues": [i.to_dict() for i in self.critical_issues],
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    output_format: str = "pdf"
    include_competitors: bool = True
    include_recommendations: bool = True
    include_technical_details: bool = True
    logo_path: Optional[str] = None
    brand_colors: dict[str, str] = field(default_factory=dict)
    custom_footer: Optional[str] = None


# Score calculation helpers
def calculate_grade(score: Optional[int]) -> Grade:
    """Calculate grade from numeric score."""
    if score is None:
        return Grade.NA
    if score >= 90:
        return Grade.A
    if score >= 80:
        return Grade.B
    if score >= 70:
        return Grade.C
    if score >= 60:
        return Grade.D
    return Grade.F


def calculate_composite_score(
    technical: Optional[int],
    content: Optional[int],
    ai_visibility: Optional[int],
    weights: dict[str, float] = None
) -> Optional[int]:
    """
    Calculate weighted composite score.

    Default weights: technical=0.30, content=0.35, ai_visibility=0.35
    """
    weights = weights or {"technical": 0.30, "content": 0.35, "ai_visibility": 0.35}

    scores = []
    total_weight = 0.0

    if technical is not None:
        scores.append(technical * weights.get("technical", 0.30))
        total_weight += weights.get("technical", 0.30)

    if content is not None:
        scores.append(content * weights.get("content", 0.35))
        total_weight += weights.get("content", 0.35)

    if ai_visibility is not None:
        scores.append(ai_visibility * weights.get("ai_visibility", 0.35))
        total_weight += weights.get("ai_visibility", 0.35)

    if not scores or total_weight == 0:
        return None

    # Normalize by actual weight used
    return int(sum(scores) / total_weight)


__all__ = [
    "Severity",
    "Priority",
    "Effort",
    "Grade",
    "AuditStatus",
    "Issue",
    "Recommendation",
    "ComponentScore",
    "AuditResult",
    "CompetitorData",
    "FullAuditResult",
    "ReportConfig",
    "calculate_grade",
    "calculate_composite_score",
]
