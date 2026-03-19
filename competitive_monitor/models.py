from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CompetitorProfile:
    id: Optional[int] = None
    url: str = ""
    company_name: str = ""
    last_score: int = 0
    current_score: int = 0
    score_history: list['ScoreSnapshot'] = None
    monitoring_frequency: int = 60  # minutes
    alert_threshold: int = 10  # score change
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.score_history is None:
            self.score_history = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class ScoreSnapshot:
    timestamp: datetime
    overall_score: int
    technical_score: int
    content_score: int
    ai_visibility_score: int
    grade: str
    key_changes: list[str] = None

    def __post_init__(self):
        if self.key_changes is None:
            self.key_changes = []

@dataclass
class AlertEvent:
    id: Optional[int] = None
    competitor_url: str = ""
    score_change: int = 0
    previous_score: int = 0
    current_score: int = 0
    trigger_reason: str = ""
    alert_channels: list[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.alert_channels is None:
            self.alert_channels = ["email"]
        if self.created_at is None:
            self.created_at = datetime.now()
