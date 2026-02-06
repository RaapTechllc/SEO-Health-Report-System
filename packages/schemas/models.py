"""
Canonical Data Models for SEO Health Report System.

Shared schemas between API and worker components.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class AuditStatus(str, Enum):
    """Audit execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class AuditTier(str, Enum):
    """Audit tier levels."""
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


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


class ProgressStage(str, Enum):
    """Progress stages for audit execution."""
    INITIALIZING = "initializing"
    TECHNICAL_AUDIT = "technical_audit"
    CONTENT_AUDIT = "content_audit"
    AI_VISIBILITY_AUDIT = "ai_visibility_audit"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"


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
class AuditRequest:
    """Request to start an audit."""
    url: str
    company_name: str
    tier: AuditTier = AuditTier.BASIC
    user_id: Optional[str] = None
    callback_url: Optional[str] = None
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "company_name": self.company_name,
            "tier": self.tier.value if isinstance(self.tier, AuditTier) else self.tier,
            "user_id": self.user_id,
            "callback_url": self.callback_url,
            "options": self.options,
        }


@dataclass
class AuditResponse:
    """Response after submitting an audit request."""
    audit_id: str
    status: AuditStatus
    message: str = ""
    estimated_time_seconds: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "status": self.status.value if isinstance(self.status, AuditStatus) else self.status,
            "message": self.message,
            "estimated_time_seconds": self.estimated_time_seconds,
            "created_at": self.created_at,
        }


@dataclass
class AuditResult:
    """Complete audit result."""
    audit_id: str
    url: str
    company_name: str
    tier: AuditTier
    status: AuditStatus
    overall_score: Optional[int] = None
    grade: Grade = Grade.NA
    technical_score: Optional[int] = None
    content_score: Optional[int] = None
    ai_visibility_score: Optional[int] = None
    components: dict[str, ComponentScore] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    report_path: Optional[str] = None
    report_pdf_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    execution_time_ms: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "url": self.url,
            "company_name": self.company_name,
            "tier": self.tier.value if isinstance(self.tier, AuditTier) else self.tier,
            "status": self.status.value if isinstance(self.status, AuditStatus) else self.status,
            "overall_score": self.overall_score,
            "grade": self.grade.value if isinstance(self.grade, Grade) else self.grade,
            "technical_score": self.technical_score,
            "content_score": self.content_score,
            "ai_visibility_score": self.ai_visibility_score,
            "components": {k: v.to_dict() for k, v in self.components.items()},
            "issues": [i.to_dict() for i in self.issues],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "report_path": self.report_path,
            "report_pdf_path": self.report_pdf_path,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class ProgressEvent:
    """Progress event for real-time audit status updates."""
    audit_id: str
    stage: ProgressStage
    progress_percent: int
    message: str = ""
    details: Optional[dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "stage": self.stage.value if isinstance(self.stage, ProgressStage) else self.stage,
            "progress_percent": self.progress_percent,
            "message": self.message,
            "details": self.details or {},
            "timestamp": self.timestamp,
        }


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
    weights: Optional[dict[str, float]] = None
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

    return int(sum(scores) / total_weight)


__all__ = [
    "AuditStatus",
    "AuditTier",
    "Severity",
    "Priority",
    "Effort",
    "Grade",
    "ProgressStage",
    "Issue",
    "Recommendation",
    "ComponentScore",
    "AuditRequest",
    "AuditResponse",
    "AuditResult",
    "ProgressEvent",
    "calculate_grade",
    "calculate_composite_score",
]
