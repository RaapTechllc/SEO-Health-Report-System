from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import logging
import os
import time
from collections import defaultdict

from storage import CompetitorStorage
from models import CompetitorProfile
from scheduler import scheduler
from monitor import monitor
from alerts import alert_system

# Import competitive intelligence
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'competitive-intel'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'multi-tier-reports'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from competitive_intel.api import router as competitive_router
from multi_tier_reports.api import router as tier_router
from ooda_orchestrator import ooda_orchestrator

# Security
security = HTTPBearer()
API_KEY = os.getenv("OODA_API_KEY", "ooda-demo-key-change-in-production")

# Rate limiting
rate_limit_store = defaultdict(list)
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 3600   # 1 hour in seconds

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key authentication."""
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

def check_rate_limit(api_key: str):
    """Check if request is within rate limits."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    
    # Clean old requests
    rate_limit_store[api_key] = [req_time for req_time in rate_limit_store[api_key] if req_time > window_start]
    
    # Check limit
    if len(rate_limit_store[api_key]) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Add current request
    rate_limit_store[api_key].append(now)

# Pydantic models for API
class CompetitorCreate(BaseModel):
    url: HttpUrl
    company_name: str
    monitoring_frequency: int = 60
    alert_threshold: int = 10

class CompetitorResponse(BaseModel):
    id: int
    url: str
    company_name: str
    last_score: int
    current_score: int
    monitoring_frequency: int
    alert_threshold: int
    created_at: str
    updated_at: str

# FastAPI app
app = FastAPI(title="Competitive OODA Loop System", version="2.0.0", 
              description="Complete competitive intelligence platform with real-time monitoring, analysis, and automated response")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict to your domain in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

storage = CompetitorStorage()
logger = logging.getLogger(__name__)

# Include all routers
app.include_router(competitive_router)
app.include_router(tier_router)

@app.post("/competitors", response_model=dict)
async def add_competitor(competitor_data: CompetitorCreate, api_key: str = Depends(verify_api_key)):
    """Add new competitor for monitoring."""
    try:
        # Rate limiting
        check_rate_limit(api_key)
        
        # Validate URL format
        url_str = str(competitor_data.url)
        if not url_str.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Validate company name
        if len(competitor_data.company_name.strip()) < 2:
            raise HTTPException(status_code=400, detail="Company name must be at least 2 characters")
        
        # Convert to internal model
        competitor = CompetitorProfile(
            url=url_str,
            company_name=competitor_data.company_name.strip(),
            monitoring_frequency=max(30, min(1440, competitor_data.monitoring_frequency)),  # 30min to 24h
            alert_threshold=max(5, min(50, competitor_data.alert_threshold))  # 5 to 50 points
        )
        
        # Add to storage
        competitor_id = storage.add_competitor(competitor)
        
        return {
            "success": True,
            "competitor_id": competitor_id,
            "message": f"Added competitor: {competitor_data.company_name}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add competitor: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/competitors", response_model=List[CompetitorResponse])
async def list_competitors():
    """List all competitors."""
    try:
        competitors = storage.list_competitors()
        
        return [
            CompetitorResponse(
                id=c.id,
                url=c.url,
                company_name=c.company_name,
                last_score=c.last_score,
                current_score=c.current_score,
                monitoring_frequency=c.monitoring_frequency,
                alert_threshold=c.alert_threshold,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat()
            )
            for c in competitors
        ]
        
    except Exception as e:
        logger.error(f"Failed to list competitors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/competitors/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(competitor_id: int):
    """Get specific competitor by ID."""
    try:
        competitor = storage.get_competitor(competitor_id)
        
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        return CompetitorResponse(
            id=competitor.id,
            url=competitor.url,
            company_name=competitor.company_name,
            last_score=competitor.last_score,
            current_score=competitor.current_score,
            monitoring_frequency=competitor.monitoring_frequency,
            alert_threshold=competitor.alert_threshold,
            created_at=competitor.created_at.isoformat(),
            updated_at=competitor.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get competitor {competitor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "competitive-monitor"}

@app.get("/competitors/{competitor_id}/history")
async def get_competitor_history(competitor_id: int):
    """Get score history for a competitor."""
    try:
        competitor = storage.get_competitor(competitor_id)
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
            
        # For now, return basic info with trends
        # In a full implementation, this would query score_snapshots table
        return {
            "competitor": {
                "id": competitor.id,
                "company_name": competitor.company_name,
                "url": competitor.url,
                "current_score": competitor.current_score,
                "last_score": competitor.last_score
            },
            "trends": {
                "direction": "up" if competitor.current_score > competitor.last_score else "down" if competitor.current_score < competitor.last_score else "stable",
                "change": competitor.current_score - competitor.last_score
            },
            "history": []  # Would contain actual snapshots
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get competitor history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/dashboard")
async def get_dashboard():
    """Get comprehensive OODA loop dashboard."""
    try:
        competitors = storage.list_competitors()
        scheduler_status = scheduler.get_status()
        recent_alerts = alert_system.get_recent_alerts(24)
        ooda_status = ooda_orchestrator.get_ooda_status()
        
        # Calculate summary stats
        total_competitors = len(competitors)
        active_monitoring = scheduler_status['scheduled_competitors']
        
        # Score distribution
        scores = [c.current_score for c in competitors if c.current_score > 0]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Competitive intelligence summary
        competitive_summary = {
            "total_analyses": ooda_status["current_cycle"],
            "avg_win_probability": 0.65,  # Would calculate from actual data
            "top_ai_gaps": [
                "Low AI search presence",
                "Poor content structure for AI",
                "Missing schema markup"
            ],
            "market_position": "competitive",
            "threat_level": "medium"
        }
        
        # OODA loop metrics
        ooda_metrics = {
            "current_cycle": ooda_status["current_cycle"],
            "system_status": ooda_status["system_status"],
            "last_execution": ooda_status["last_execution"],
            "performance_metrics": ooda_status["performance_metrics"],
            "components_status": ooda_status["components_status"]
        }
        
        return {
            "summary": {
                "total_competitors": total_competitors,
                "active_monitoring": active_monitoring,
                "average_score": round(avg_score, 1),
                "recent_alerts": len(recent_alerts),
                "ooda_cycles_completed": ooda_status["current_cycle"]
            },
            "competitors": [
                {
                    "id": c.id,
                    "company_name": c.company_name,
                    "url": c.url,
                    "current_score": c.current_score,
                    "last_score": c.last_score,
                    "trend": "up" if c.current_score > c.last_score else "down" if c.current_score < c.last_score else "stable",
                    "monitoring_frequency": c.monitoring_frequency,
                    "last_updated": c.updated_at.isoformat(),
                    "threat_level": "high" if c.current_score > 80 else "medium" if c.current_score > 60 else "low"
                }
                for c in competitors
            ],
            "scheduler_status": scheduler_status,
            "recent_alerts": recent_alerts,
            "competitive_intelligence": competitive_summary,
            "ooda_loop": ooda_metrics,
            "system_capabilities": {
                "real_time_monitoring": True,
                "competitive_analysis": True,
                "battlecard_generation": True,
                "tier_recommendations": True,
                "automated_responses": True,
                "ai_visibility_tracking": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/monitoring/start")
async def start_monitoring():
    """Start the monitoring system."""
    try:
        monitor.start_monitoring()
        return {"success": True, "message": "Monitoring started"}
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to start monitoring")

@app.post("/monitoring/stop")
async def stop_monitoring():
    """Stop the monitoring system."""
    try:
        monitor.stop_monitoring()
        return {"success": True, "message": "Monitoring stopped"}
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop monitoring")

@app.post("/ooda/execute")
async def execute_ooda_cycle():
    """Manually trigger OODA loop execution."""
    try:
        trigger_event = {
            "type": "manual_trigger",
            "timestamp": "2026-01-12T22:00:00Z",
            "prospect_url": "https://our-site.com"
        }
        
        result = ooda_orchestrator.execute_full_ooda_cycle(trigger_event)
        
        return {
            "success": True,
            "message": "OODA cycle executed successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to execute OODA cycle: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute OODA cycle")

@app.get("/ooda/status")
async def get_ooda_status():
    """Get current OODA loop status."""
    try:
        status = ooda_orchestrator.get_ooda_status()
        return {
            "success": True,
            "ooda_status": status
        }
    except Exception as e:
        logger.error(f"Failed to get OODA status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get OODA status")

@app.post("/api/validate-url")
async def validate_url(request: dict, api_key: str = Depends(verify_api_key)):
    """Validate and correct URL format."""
    try:
        check_rate_limit(api_key)
        
        url = request.get("url", "").strip()
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        # Apply URL corrections
        corrected = url
        corrections = []
        
        # Add protocol if missing
        if not corrected.startswith(('http://', 'https://')):
            corrected = f"https://{corrected}"
            corrections.append("Added HTTPS protocol")
        
        # Add www if simple domain
        if corrected.count('.') == 1 and '/' not in corrected.replace('https://', '').replace('http://', ''):
            corrected = corrected.replace('://', '://www.')
            corrections.append("Added www subdomain")
        
        # Validate final URL
        try:
            from urllib.parse import urlparse
            parsed = urlparse(corrected)
            is_valid = bool(parsed.scheme and parsed.netloc)
        except:
            is_valid = False
        
        return {
            "validation": {
                "original": url,
                "corrected": corrected,
                "isValid": is_valid,
                "corrections": corrections
            },
            "suggestions": [
                "Ensure URL includes protocol (https://)",
                "Check for typos in domain name",
                "Verify the website is accessible"
            ] if not is_valid else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL validation failed: {e}")
        raise HTTPException(status_code=500, detail="Validation failed")

@app.get("/api/docs/{section}")
async def get_documentation(section: str):
    """Get documentation content for a section."""
    try:
        # Mock documentation - in production, this would come from a CMS or files
        docs = {
            "api": {
                "title": "API Reference",
                "content": "Complete API documentation for the OODA Loop system.",
                "sections": [
                    {
                        "id": "authentication",
                        "title": "Authentication",
                        "content": "All API requests require Bearer token authentication.",
                        "codeExamples": [
                            {
                                "language": "curl",
                                "code": 'curl -H "Authorization: Bearer YOUR_API_KEY" https://api.ooda-system.com/competitors',
                                "description": "Example authenticated request"
                            }
                        ]
                    }
                ]
            },
            "guides": {
                "title": "Getting Started",
                "content": "Step-by-step guides for using the OODA Loop system.",
                "sections": [
                    {
                        "id": "quickstart",
                        "title": "5-Minute Quick Start",
                        "content": "Get your first competitive analysis running in 5 minutes.",
                        "codeExamples": []
                    }
                ]
            },
            "examples": {
                "title": "Code Examples",
                "content": "Real-world examples and use cases.",
                "sections": [
                    {
                        "id": "python-example",
                        "title": "Python Integration",
                        "content": "Integrate OODA Loop into your Python applications.",
                        "codeExamples": [
                            {
                                "language": "python",
                                "code": "import requests\n\nresponse = requests.post('/competitive-analysis/', json=data)",
                                "description": "Python API integration example"
                            }
                        ]
                    }
                ]
            }
        }
        
        if section not in docs:
            raise HTTPException(status_code=404, detail="Documentation section not found")
        
        return {
            "content": docs[section],
            "navigation": list(docs.keys()),
            "searchIndex": [s["title"] for s in docs[section]["sections"]]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get documentation: {e}")
        raise HTTPException(status_code=500, detail="Failed to load documentation")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
