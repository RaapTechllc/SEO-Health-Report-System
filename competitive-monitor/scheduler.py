import asyncio
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional
import signal
import sys

class MonitoringScheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tasks: Dict[int, Dict] = {}  # competitor_id -> task info
        self.running = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start the scheduler in a background thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        self.logger.info("Monitoring scheduler started")
        
    def stop(self):
        """Stop the scheduler gracefully."""
        if not self.running:
            return
            
        self.running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("Monitoring scheduler stopped")
        
    def schedule_competitor(self, competitor_id: int, frequency_minutes: int, 
                          callback: Callable[[int], None]):
        """Schedule monitoring for a competitor."""
        self.tasks[competitor_id] = {
            'frequency': frequency_minutes,
            'callback': callback,
            'next_run': datetime.now() + timedelta(minutes=frequency_minutes),
            'last_run': None
        }
        self.logger.info(f"Scheduled competitor {competitor_id} every {frequency_minutes} minutes")
        
    def unschedule_competitor(self, competitor_id: int):
        """Remove competitor from scheduling."""
        if competitor_id in self.tasks:
            del self.tasks[competitor_id]
            self.logger.info(f"Unscheduled competitor {competitor_id}")
            
    def _run_scheduler(self):
        """Run the scheduler loop."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._scheduler_loop())
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
        finally:
            self.loop.close()
            
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                now = datetime.now()
                
                # Check each scheduled task
                for competitor_id, task_info in list(self.tasks.items()):
                    if now >= task_info['next_run']:
                        # Run the callback
                        try:
                            task_info['callback'](competitor_id)
                            task_info['last_run'] = now
                            task_info['next_run'] = now + timedelta(minutes=task_info['frequency'])
                            self.logger.debug(f"Executed monitoring for competitor {competitor_id}")
                        except Exception as e:
                            self.logger.error(f"Monitoring callback failed for competitor {competitor_id}: {e}")
                
                # Sleep for 30 seconds before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
                
    def get_status(self) -> Dict:
        """Get scheduler status."""
        return {
            'running': self.running,
            'scheduled_competitors': len(self.tasks),
            'tasks': {
                cid: {
                    'frequency_minutes': info['frequency'],
                    'next_run': info['next_run'].isoformat(),
                    'last_run': info['last_run'].isoformat() if info['last_run'] else None
                }
                for cid, info in self.tasks.items()
            }
        }

# Global scheduler instance
scheduler = MonitoringScheduler()

def setup_signal_handlers():
    """Setup graceful shutdown on signals."""
    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, shutting down...")
        scheduler.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
