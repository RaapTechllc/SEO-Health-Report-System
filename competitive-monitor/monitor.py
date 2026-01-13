import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path for SEO health report imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage import CompetitorStorage
from models import ScoreSnapshot
from scheduler import scheduler

class CompetitorMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.storage = CompetitorStorage()
        
    def start_monitoring(self):
        """Start monitoring all registered competitors."""
        competitors = self.storage.list_competitors()
        
        for competitor in competitors:
            scheduler.schedule_competitor(
                competitor.id,
                competitor.monitoring_frequency,
                self._monitor_competitor_callback
            )
            
        scheduler.start()
        self.logger.info(f"Started monitoring {len(competitors)} competitors")
        
    def stop_monitoring(self):
        """Stop all monitoring."""
        scheduler.stop()
        self.logger.info("Stopped competitor monitoring")
        
    def _monitor_competitor_callback(self, competitor_id: int):
        """Callback function for scheduled monitoring."""
        try:
            competitor = self.storage.get_competitor(competitor_id)
            if not competitor:
                self.logger.error(f"Competitor {competitor_id} not found")
                return
                
            self.logger.info(f"Monitoring competitor: {competitor.company_name}")
            
            # Run SEO health report
            report_result = self._run_seo_health_report(competitor.url)
            
            if report_result:
                # Extract scores
                new_score = report_result.get('overall_score', 0)
                
                # Update competitor score
                self.storage.update_competitor_score(competitor_id, new_score)
                
                # Create score snapshot
                snapshot = ScoreSnapshot(
                    timestamp=datetime.now(),
                    overall_score=report_result.get('overall_score', 0),
                    technical_score=report_result.get('technical', {}).get('score', 0),
                    content_score=report_result.get('content', {}).get('score', 0),
                    ai_visibility_score=report_result.get('ai_visibility', {}).get('score', 0),
                    grade=report_result.get('grade', 'F'),
                    key_changes=self._identify_key_changes(competitor, report_result)
                )
                
                # Store snapshot
                self.storage.add_score_snapshot(competitor_id, snapshot)
                
                # Check for significant changes
                self._check_score_changes(competitor, new_score)
                
                self.logger.info(f"Updated {competitor.company_name}: {new_score}/100 ({snapshot.grade})")
            else:
                self.logger.error(f"Failed to generate report for {competitor.company_name}")
                
        except Exception as e:
            self.logger.error(f"Monitoring failed for competitor {competitor_id}: {e}")
            
    def _run_seo_health_report(self, url: str) -> Optional[Dict[str, Any]]:
        """Run SEO health report for a URL."""
        try:
            # Try to import and run the SEO health report system
            try:
                # Import with module registration for hyphenated packages
                import importlib.util
                import sys
                
                # Register seo_health_report module
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                seo_path = os.path.join(project_root, "seo-health-report", "__init__.py")
                
                if os.path.exists(seo_path):
                    spec = importlib.util.spec_from_file_location("seo_health_report", seo_path)
                    seo_module = importlib.util.module_from_spec(spec)
                    sys.modules["seo_health_report"] = seo_module
                    spec.loader.exec_module(seo_module)
                    
                    # Run the report
                    result = seo_module.generate_report(
                        target_url=url,
                        company_name="Competitor Analysis",
                        output_format="json"
                    )
                    return result
                else:
                    # Fallback: Mock report for testing
                    self.logger.warning("SEO health report system not found, using mock data")
                    return self._generate_mock_report()
                    
            except ImportError as e:
                self.logger.warning(f"Could not import SEO health report: {e}, using mock data")
                return self._generate_mock_report()
                
        except Exception as e:
            self.logger.error(f"Failed to run SEO health report for {url}: {e}")
            return None
            
    def _generate_mock_report(self) -> Dict[str, Any]:
        """Generate mock report data for testing."""
        import random
        
        # Generate realistic but random scores
        technical_score = random.randint(60, 95)
        content_score = random.randint(55, 90)
        ai_visibility_score = random.randint(40, 85)
        
        overall_score = int((technical_score * 0.30) + (content_score * 0.35) + (ai_visibility_score * 0.35))
        
        # Determine grade
        if overall_score >= 90:
            grade = 'A'
        elif overall_score >= 80:
            grade = 'B'
        elif overall_score >= 70:
            grade = 'C'
        elif overall_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
            
        return {
            'overall_score': overall_score,
            'grade': grade,
            'technical': {'score': technical_score},
            'content': {'score': content_score},
            'ai_visibility': {'score': ai_visibility_score},
            'timestamp': datetime.now().isoformat()
        }
        
    def _identify_key_changes(self, competitor, report_result: Dict[str, Any]) -> list:
        """Identify key changes from the report."""
        changes = []
        
        # Compare with previous score
        score_change = report_result.get('overall_score', 0) - competitor.current_score
        
        if abs(score_change) >= competitor.alert_threshold:
            if score_change > 0:
                changes.append(f"Score increased by {score_change} points")
            else:
                changes.append(f"Score decreased by {abs(score_change)} points")
                
        # Add grade change if significant
        current_grade = report_result.get('grade', 'F')
        if hasattr(competitor, 'last_grade') and competitor.last_grade != current_grade:
            changes.append(f"Grade changed from {competitor.last_grade} to {current_grade}")
            
        return changes
        
    def _check_score_changes(self, competitor, new_score: int):
        """Check for significant score changes and trigger alerts."""
        score_change = new_score - competitor.current_score
        
        if abs(score_change) >= competitor.alert_threshold:
            # Import here to avoid circular imports
            from models import AlertEvent
            
            alert = AlertEvent(
                competitor_url=competitor.url,
                score_change=score_change,
                previous_score=competitor.current_score,
                current_score=new_score,
                trigger_reason=f"Score change of {score_change} points exceeds threshold of {competitor.alert_threshold}",
                alert_channels=["email", "log"]
            )
            
            self.storage.add_alert(alert)
            self.logger.warning(f"ALERT: {competitor.company_name} score changed by {score_change} points")

# Global monitor instance
monitor = CompetitorMonitor()
