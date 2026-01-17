#!/usr/bin/env python3
"""
Simple API server for SEO Health Report

Provides REST endpoints for running audits and generating reports.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "seo-health-report"))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

# Import audit functions
from scripts.orchestrate import run_full_audit
from scripts.calculate_scores import calculate_composite_score

app = FastAPI(
    title="SEO Health Report API",
    description="Run comprehensive SEO audits with AI visibility analysis",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: str = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)

# Store for audit results
audit_results = {}


class AuditRequest(BaseModel):
    url: str
    company_name: str
    keywords: List[str] = []
    competitors: List[str] = []


class AuditResponse(BaseModel):
    audit_id: str
    status: str
    url: str
    company_name: str


class AuditResult(BaseModel):
    audit_id: str
    status: str
    overall_score: Optional[int] = None
    grade: Optional[str] = None
    component_scores: Optional[dict] = None
    url: str
    company_name: str
    timestamp: Optional[str] = None
    report_path: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "SEO Health Report API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/audit", response_model=AuditResponse)
async def start_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    """Start a new SEO audit."""
    audit_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Store initial status
    audit_results[audit_id] = {
        "status": "running",
        "url": request.url,
        "company_name": request.company_name,
    }
    
    # Run audit in background
    background_tasks.add_task(
        run_audit_task,
        audit_id,
        request.url,
        request.company_name,
        request.keywords,
        request.competitors
    )
    
    return AuditResponse(
        audit_id=audit_id,
        status="running",
        url=request.url,
        company_name=request.company_name
    )


async def run_audit_task(
    audit_id: str,
    url: str,
    company_name: str,
    keywords: List[str],
    competitors: List[str]
):
    """Background task to run the audit."""
    try:
        # Run the audit
        result = await run_full_audit(
            target_url=url,
            company_name=company_name,
            primary_keywords=keywords,
            competitor_urls=competitors,
        )
        
        # Calculate scores
        scores = calculate_composite_score(result)
        result["overall_score"] = scores.get("overall_score", 0)
        result["grade"] = scores.get("grade", "N/A")
        result["component_scores"] = scores.get("component_scores", {})
        
        # Save to file
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        domain = url.replace("https://", "").replace("http://", "").replace("/", "_")
        report_path = reports_dir / f"{audit_id}_{domain}.json"
        
        with open(report_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        
        # Update status
        audit_results[audit_id] = {
            "status": "completed",
            "url": url,
            "company_name": company_name,
            "overall_score": result["overall_score"],
            "grade": result["grade"],
            "component_scores": result["component_scores"],
            "timestamp": result.get("timestamp"),
            "report_path": str(report_path),
            "data": result,
        }
        
    except Exception as e:
        audit_results[audit_id] = {
            "status": "failed",
            "url": url,
            "company_name": company_name,
            "error": str(e),
        }


@app.get("/audit/{audit_id}", response_model=AuditResult)
async def get_audit_status(audit_id: str):
    """Get audit status and results."""
    if audit_id not in audit_results:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    result = audit_results[audit_id]
    return AuditResult(
        audit_id=audit_id,
        status=result.get("status", "unknown"),
        overall_score=result.get("overall_score"),
        grade=result.get("grade"),
        component_scores=result.get("component_scores"),
        url=result.get("url", ""),
        company_name=result.get("company_name", ""),
        timestamp=result.get("timestamp"),
        report_path=result.get("report_path"),
    )


@app.get("/audit/{audit_id}/full")
async def get_full_audit_result(audit_id: str):
    """Get full audit data."""
    if audit_id not in audit_results:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    result = audit_results[audit_id]
    if result.get("status") != "completed":
        raise HTTPException(status_code=400, detail=f"Audit status: {result.get('status')}")
    
    return result.get("data", {})


@app.get("/audit/{audit_id}/pdf")
async def get_audit_pdf(audit_id: str):
    """Generate and return PDF report."""
    if audit_id not in audit_results:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    result = audit_results[audit_id]
    if result.get("status") != "completed":
        raise HTTPException(status_code=400, detail=f"Audit status: {result.get('status')}")
    
    json_path = result.get("report_path")
    if not json_path or not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    # Generate PDF
    pdf_path = json_path.replace(".json", "_PREMIUM.pdf")
    
    if not os.path.exists(pdf_path):
        # Import and run PDF generator
        sys.path.insert(0, str(project_root))
        from generate_premium_report import generate_premium_report
        generate_premium_report(json_path, pdf_path)
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"SEO_Report_{audit_id}.pdf"
    )


@app.get("/audits")
async def list_audits():
    """List all audits."""
    return {
        "audits": [
            {
                "audit_id": aid,
                "status": data.get("status"),
                "url": data.get("url"),
                "company_name": data.get("company_name"),
                "overall_score": data.get("overall_score"),
                "grade": data.get("grade"),
            }
            for aid, data in audit_results.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
