#!/usr/bin/env python3
"""
Competitive Monitor - Real-Time SEO Monitoring System
CYCLE 1: OBSERVE - Real-Time Monitoring MVP

Usage:
    python3 competitive_monitor/main.py

Features:
- Competitor registration API
- Configurable monitoring intervals
- SEO health report integration
- Score change detection & alerts
- Dashboard API
"""

import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from api import app
from monitor import monitor
from scheduler import setup_signal_handlers


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('competitive_monitor.log')
        ]
    )

def main():
    """Main entry point."""
    print("🚀 Starting Competitive Monitor - CYCLE 1: OBSERVE")
    print("=" * 50)

    # Setup
    setup_logging()
    setup_signal_handlers()

    logger = logging.getLogger(__name__)
    logger.info("Competitive Monitor starting...")

    # Start monitoring system
    try:
        monitor.start_monitoring()
        logger.info("Monitoring system started")

        # Start API server
        import uvicorn
        print("🌐 API Server starting on http://localhost:8000")
        print("📊 Dashboard: http://localhost:8000/dashboard")
        print("📋 Docs: http://localhost:8000/docs")
        print("=" * 50)

        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
