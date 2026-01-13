import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from models import CompetitorProfile, ScoreSnapshot, AlertEvent

class CompetitorStorage:
    def __init__(self, db_path: str = "competitive_monitor.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema with secure permissions."""
        # Set secure file permissions
        if self.db_path.exists():
            os.chmod(self.db_path, 0o600)  # Owner read/write only
        
        with sqlite3.connect(self.db_path) as conn:
            # Set secure database options
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = FULL")
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS competitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    company_name TEXT NOT NULL,
                    last_score INTEGER DEFAULT 0,
                    current_score INTEGER DEFAULT 0,
                    monitoring_frequency INTEGER DEFAULT 60,
                    alert_threshold INTEGER DEFAULT 10,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS score_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    overall_score INTEGER NOT NULL,
                    technical_score INTEGER NOT NULL,
                    content_score INTEGER NOT NULL,
                    ai_visibility_score INTEGER NOT NULL,
                    grade TEXT NOT NULL,
                    key_changes TEXT,
                    FOREIGN KEY (competitor_id) REFERENCES competitors (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_url TEXT NOT NULL,
                    score_change INTEGER NOT NULL,
                    previous_score INTEGER NOT NULL,
                    current_score INTEGER NOT NULL,
                    trigger_reason TEXT NOT NULL,
                    alert_channels TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
        
        # Set secure permissions after creation
        os.chmod(self.db_path, 0o600)
    
    def add_competitor(self, competitor: CompetitorProfile) -> int:
        """Add new competitor and return ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO competitors 
                    (url, company_name, monitoring_frequency, alert_threshold, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    competitor.url,
                    competitor.company_name,
                    competitor.monitoring_frequency,
                    competitor.alert_threshold,
                    competitor.created_at.isoformat(),
                    competitor.updated_at.isoformat()
                ))
                competitor_id = cursor.lastrowid
                conn.commit()
                self.logger.info(f"Added competitor: {competitor.company_name} (ID: {competitor_id})")
                return competitor_id
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Competitor already exists: {competitor.url}")
            raise ValueError(f"Competitor URL already exists: {competitor.url}")
        except Exception as e:
            self.logger.error(f"Failed to add competitor: {e}")
            raise
    
    def get_competitor(self, competitor_id: int) -> Optional[CompetitorProfile]:
        """Get competitor by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM competitors WHERE id = ?
                """, (competitor_id,))
                row = cursor.fetchone()
                
                if row:
                    return CompetitorProfile(
                        id=row['id'],
                        url=row['url'],
                        company_name=row['company_name'],
                        last_score=row['last_score'],
                        current_score=row['current_score'],
                        monitoring_frequency=row['monitoring_frequency'],
                        alert_threshold=row['alert_threshold'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                return None
        except Exception as e:
            self.logger.error(f"Failed to get competitor {competitor_id}: {e}")
            return None
    
    def list_competitors(self) -> List[CompetitorProfile]:
        """List all competitors."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM competitors ORDER BY created_at DESC")
                rows = cursor.fetchall()
                
                competitors = []
                for row in rows:
                    competitors.append(CompetitorProfile(
                        id=row['id'],
                        url=row['url'],
                        company_name=row['company_name'],
                        last_score=row['last_score'],
                        current_score=row['current_score'],
                        monitoring_frequency=row['monitoring_frequency'],
                        alert_threshold=row['alert_threshold'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    ))
                
                return competitors
        except Exception as e:
            self.logger.error(f"Failed to list competitors: {e}")
            return []
    
    def update_competitor_score(self, competitor_id: int, new_score: int) -> bool:
        """Update competitor's current score."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current score first
                cursor = conn.execute("SELECT current_score FROM competitors WHERE id = ?", (competitor_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                old_score = row[0]
                
                # Update scores
                conn.execute("""
                    UPDATE competitors 
                    SET last_score = ?, current_score = ?, updated_at = ?
                    WHERE id = ?
                """, (old_score, new_score, datetime.now().isoformat(), competitor_id))
                
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to update competitor score: {e}")
            return False
    
    def add_score_snapshot(self, competitor_id: int, snapshot: ScoreSnapshot) -> bool:
        """Add score snapshot for competitor."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO score_snapshots 
                    (competitor_id, timestamp, overall_score, technical_score, 
                     content_score, ai_visibility_score, grade, key_changes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    competitor_id,
                    snapshot.timestamp.isoformat(),
                    snapshot.overall_score,
                    snapshot.technical_score,
                    snapshot.content_score,
                    snapshot.ai_visibility_score,
                    snapshot.grade,
                    json.dumps(snapshot.key_changes)
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add score snapshot: {e}")
            return False
    
    def add_alert(self, alert: AlertEvent) -> bool:
        """Add alert event."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO alert_events 
                    (competitor_url, score_change, previous_score, current_score, 
                     trigger_reason, alert_channels, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.competitor_url,
                    alert.score_change,
                    alert.previous_score,
                    alert.current_score,
                    alert.trigger_reason,
                    json.dumps(alert.alert_channels),
                    alert.created_at.isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add alert: {e}")
            return False
