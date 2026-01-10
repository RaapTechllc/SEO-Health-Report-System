# Feature: Create Scheduled Audit Functionality

The following plan should be complete, but validate documentation and codebase patterns before implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files.

## Feature Description

Add ability to schedule recurring SEO audits that run automatically at specified intervals. Store audit history and track score changes over time. Enable trend analysis and alerting on significant changes.

## User Story

As an **SEO manager**
I want to **schedule automatic weekly audits**
So that **I can track SEO health trends without manual intervention**

## Problem Statement

Currently audits must be triggered manually. For ongoing monitoring, users need:
- Scheduled recurring audits (daily, weekly, monthly)
- Historical data storage for trend analysis
- Alerts when scores change significantly
- Comparison with previous audit results

## Solution Statement

Implement a scheduler using APScheduler with SQLite job store for persistence. Create audit history storage and trend analysis. Add CLI commands for schedule management.

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: High
**Primary Systems Affected**: New scheduler module, CLI
**Dependencies**: `apscheduler>=3.10.0`, `sqlalchemy>=2.0.0` (for job store)

---

## CONTEXT REFERENCES

### Relevant Codebase Files - READ BEFORE IMPLEMENTING

- `seo-health-report/__init__.py` (lines 1-100) - Why: `generate_report()` function to schedule
- `seo-health-report/__init__.py` (lines 200-250) - Why: CLI `main()` pattern to extend
- `seo-health-report/scripts/calculate_scores.py` (lines 100-150) - Why: `compare_scores()` for trend analysis

### New Files to Create

- `seo-health-report/scripts/scheduler.py` - APScheduler integration
- `seo-health-report/scripts/history.py` - Audit history storage
- `seo-health-report/scripts/trends.py` - Trend analysis

### Files to Update

- `seo-health-report/__init__.py` - Add scheduler CLI commands
- `seo-health-report/requirements.txt` - Add dependencies

### Relevant Documentation

- [APScheduler Documentation](https://apscheduler.readthedocs.io/en/stable/)
  - Section: BackgroundScheduler
  - Why: Non-blocking scheduler for background execution
- [APScheduler Job Stores](https://apscheduler.readthedocs.io/en/stable/modules/jobstores/sqlalchemy.html)
  - Section: SQLAlchemy job store
  - Why: Persistent job storage across restarts

### Patterns to Follow

**CLI pattern** (from `__init__.py`):
```python
def main():
    import argparse
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("--url", required=True, help="Target URL")
    args = parser.parse_args()
```

**Score comparison** (from `calculate_scores.py`):
```python
def compare_scores(current: Dict, previous: Dict) -> Dict:
    comparison = {
        "overall_change": current["overall_score"] - previous["overall_score"],
        "improved": [],
        "declined": []
    }
```

---

## IMPLEMENTATION PLAN

### Prerequisites Gate

- [ ] `pip install apscheduler>=3.10.0`
- [ ] `pip install sqlalchemy>=2.0.0`
- [ ] Test import: `from apscheduler.schedulers.background import BackgroundScheduler`

### Phase 1: Foundation

Create history storage and scheduler infrastructure.

### Phase 2: Core Implementation

Implement scheduled job execution and history tracking.

### Phase 3: Integration

Add CLI commands for schedule management.

### Phase 4: Testing

Validate scheduling, persistence, and trend analysis.

---

## STEP-BY-STEP TASKS

### Task 1: UPDATE `seo-health-report/requirements.txt`

- **IMPLEMENT**: Add scheduler dependencies
- **ADD**:
  ```
  apscheduler>=3.10.0
  sqlalchemy>=2.0.0
  ```
- **VALIDATE**: `pip install -r seo-health-report/requirements.txt`

### Task 2: CREATE `seo-health-report/scripts/history.py`

- **IMPLEMENT**: Audit history storage using SQLite
- **IMPORTS**:
  ```python
  import os
  import json
  import sqlite3
  from typing import Dict, Any, List, Optional
  from datetime import datetime
  ```
- **COMPONENTS**:
  ```python
  # Default history database location
  HISTORY_DB = os.path.join(os.path.expanduser("~"), ".seo-health-history.db")
  
  def init_db(db_path: str = HISTORY_DB):
      """Initialize history database."""
      conn = sqlite3.connect(db_path)
      conn.execute('''
          CREATE TABLE IF NOT EXISTS audit_history (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              url TEXT NOT NULL,
              company_name TEXT,
              timestamp TEXT NOT NULL,
              overall_score INTEGER,
              grade TEXT,
              technical_score INTEGER,
              content_score INTEGER,
              ai_score INTEGER,
              report_path TEXT,
              full_results TEXT
          )
      ''')
      conn.commit()
      conn.close()
  
  def save_audit(
      url: str,
      company_name: str,
      results: Dict[str, Any],
      report_path: str = None,
      db_path: str = HISTORY_DB
  ):
      """Save audit results to history."""
      init_db(db_path)
      conn = sqlite3.connect(db_path)
      
      scores = results.get("component_scores", {})
      
      conn.execute('''
          INSERT INTO audit_history 
          (url, company_name, timestamp, overall_score, grade, 
           technical_score, content_score, ai_score, report_path, full_results)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ''', (
          url,
          company_name,
          datetime.now().isoformat(),
          results.get("overall_score", 0),
          results.get("grade", "?"),
          scores.get("technical", {}).get("score", 0),
          scores.get("content", {}).get("score", 0),
          scores.get("ai_visibility", {}).get("score", 0),
          report_path,
          json.dumps(results)
      ))
      conn.commit()
      conn.close()
  
  def get_history(
      url: str,
      limit: int = 10,
      db_path: str = HISTORY_DB
  ) -> List[Dict[str, Any]]:
      """Get audit history for a URL."""
      init_db(db_path)
      conn = sqlite3.connect(db_path)
      cursor = conn.execute('''
          SELECT timestamp, overall_score, grade, technical_score, 
                 content_score, ai_score, report_path
          FROM audit_history
          WHERE url = ?
          ORDER BY timestamp DESC
          LIMIT ?
      ''', (url, limit))
      
      results = []
      for row in cursor:
          results.append({
              "timestamp": row[0],
              "overall_score": row[1],
              "grade": row[2],
              "technical_score": row[3],
              "content_score": row[4],
              "ai_score": row[5],
              "report_path": row[6]
          })
      conn.close()
      return results
  
  def get_previous_audit(url: str, db_path: str = HISTORY_DB) -> Optional[Dict]:
      """Get most recent previous audit for comparison."""
      history = get_history(url, limit=1, db_path=db_path)
      return history[0] if history else None
  ```
- **VALIDATE**: `python -c "from seo_health_report.scripts.history import save_audit, get_history"`

### Task 3: CREATE `seo-health-report/scripts/trends.py`

- **IMPLEMENT**: Trend analysis from history
- **COMPONENTS**:
  ```python
  from typing import Dict, Any, List
  from .history import get_history
  
  def analyze_trends(url: str, periods: int = 10) -> Dict[str, Any]:
      """Analyze score trends over time."""
      history = get_history(url, limit=periods)
      
      if len(history) < 2:
          return {"trend": "insufficient_data", "data_points": len(history)}
      
      scores = [h["overall_score"] for h in history]
      
      # Calculate trend direction
      recent_avg = sum(scores[:3]) / min(3, len(scores))
      older_avg = sum(scores[-3:]) / min(3, len(scores))
      
      if recent_avg > older_avg + 5:
          trend = "improving"
      elif recent_avg < older_avg - 5:
          trend = "declining"
      else:
          trend = "stable"
      
      return {
          "trend": trend,
          "current_score": scores[0] if scores else 0,
          "previous_score": scores[1] if len(scores) > 1 else None,
          "change": scores[0] - scores[1] if len(scores) > 1 else 0,
          "history": history,
          "data_points": len(history)
      }
  
  def detect_significant_change(
      current: Dict[str, Any],
      previous: Dict[str, Any],
      threshold: int = 10
  ) -> Dict[str, Any]:
      """Detect significant score changes for alerting."""
      alerts = []
      
      current_score = current.get("overall_score", 0)
      previous_score = previous.get("overall_score", 0) if previous else current_score
      change = current_score - previous_score
      
      if abs(change) >= threshold:
          alerts.append({
              "type": "score_change",
              "severity": "high" if abs(change) >= 20 else "medium",
              "message": f"Score changed by {change:+d} points ({previous_score} → {current_score})",
              "change": change
          })
      
      # Check component changes
      for comp in ["technical", "content", "ai_visibility"]:
          curr_comp = current.get("component_scores", {}).get(comp, {}).get("score", 0)
          prev_comp = previous.get("component_scores", {}).get(comp, {}).get("score", 0) if previous else curr_comp
          comp_change = curr_comp - prev_comp
          
          if abs(comp_change) >= 15:
              alerts.append({
                  "type": "component_change",
                  "component": comp,
                  "severity": "medium",
                  "message": f"{comp.replace('_', ' ').title()} changed by {comp_change:+d}",
                  "change": comp_change
              })
      
      return {
          "has_alerts": len(alerts) > 0,
          "alerts": alerts
      }
  ```
- **VALIDATE**: `python -c "from seo_health_report.scripts.trends import analyze_trends"`

### Task 4: CREATE `seo-health-report/scripts/scheduler.py`

- **IMPLEMENT**: APScheduler integration
- **IMPORTS**:
  ```python
  import os
  import atexit
  from typing import Dict, Any, Optional, Callable
  from datetime import datetime
  ```
- **COMPONENTS**:
  ```python
  # Scheduler state
  _scheduler = None
  JOBS_DB = os.path.join(os.path.expanduser("~"), ".seo-health-jobs.db")
  
  def get_scheduler():
      """Get or create scheduler instance."""
      global _scheduler
      if _scheduler is None:
          from apscheduler.schedulers.background import BackgroundScheduler
          from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
          
          jobstores = {
              'default': SQLAlchemyJobStore(url=f'sqlite:///{JOBS_DB}')
          }
          
          _scheduler = BackgroundScheduler(jobstores=jobstores)
          _scheduler.start()
          atexit.register(lambda: _scheduler.shutdown())
      
      return _scheduler
  
  def scheduled_audit(
      url: str,
      company_name: str,
      keywords: list,
      output_dir: str,
      logo_file: str = ""
  ):
      """Execute scheduled audit job."""
      from seo_health_report import generate_report
      from .history import save_audit
      from .trends import detect_significant_change, get_previous_audit
      
      print(f"[Scheduled] Running audit for {url} at {datetime.now()}")
      
      # Get previous for comparison
      previous = get_previous_audit(url)
      
      # Run audit
      result = generate_report(
          target_url=url,
          company_name=company_name,
          logo_file=logo_file,
          primary_keywords=keywords,
          output_format="docx",
          output_dir=output_dir
      )
      
      # Save to history
      save_audit(
          url=url,
          company_name=company_name,
          results=result,
          report_path=result.get("report", {}).get("output_path")
      )
      
      # Check for significant changes
      alerts = detect_significant_change(result, previous)
      if alerts["has_alerts"]:
          print(f"[Alert] Significant changes detected:")
          for alert in alerts["alerts"]:
              print(f"  - {alert['message']}")
      
      return result
  
  def schedule_audit(
      url: str,
      company_name: str,
      keywords: list,
      output_dir: str,
      interval: str = "weekly",  # "daily", "weekly", "monthly"
      logo_file: str = ""
  ) -> str:
      """Schedule recurring audit."""
      scheduler = get_scheduler()
      
      # Define interval
      if interval == "daily":
          trigger_kwargs = {"days": 1}
      elif interval == "weekly":
          trigger_kwargs = {"weeks": 1}
      elif interval == "monthly":
          trigger_kwargs = {"days": 30}
      else:
          raise ValueError(f"Invalid interval: {interval}")
      
      job_id = f"audit_{url.replace('://', '_').replace('/', '_')}"
      
      # Remove existing job if any
      existing = scheduler.get_job(job_id)
      if existing:
          scheduler.remove_job(job_id)
      
      # Add new job
      scheduler.add_job(
          scheduled_audit,
          'interval',
          id=job_id,
          kwargs={
              "url": url,
              "company_name": company_name,
              "keywords": keywords,
              "output_dir": output_dir,
              "logo_file": logo_file
          },
          **trigger_kwargs
      )
      
      return job_id
  
  def list_scheduled_jobs() -> list:
      """List all scheduled audit jobs."""
      scheduler = get_scheduler()
      jobs = []
      for job in scheduler.get_jobs():
          jobs.append({
              "id": job.id,
              "next_run": str(job.next_run_time),
              "kwargs": job.kwargs
          })
      return jobs
  
  def cancel_scheduled_job(job_id: str) -> bool:
      """Cancel a scheduled job."""
      scheduler = get_scheduler()
      try:
          scheduler.remove_job(job_id)
          return True
      except:
          return False
  ```
- **GOTCHA**: Must call `get_scheduler()` to initialize before listing jobs
- **VALIDATE**: `python -c "from seo_health_report.scripts.scheduler import schedule_audit, list_scheduled_jobs"`

### Task 5: UPDATE `seo-health-report/__init__.py`

- **IMPLEMENT**: Add scheduler CLI commands
- **ADD** to argparse:
  ```python
  # Add subcommands
  subparsers = parser.add_subparsers(dest="command", help="Commands")
  
  # Schedule command
  schedule_parser = subparsers.add_parser("schedule", help="Schedule recurring audit")
  schedule_parser.add_argument("--url", required=True)
  schedule_parser.add_argument("--company", required=True)
  schedule_parser.add_argument("--keywords", required=True)
  schedule_parser.add_argument("--interval", default="weekly", choices=["daily", "weekly", "monthly"])
  schedule_parser.add_argument("--output-dir", default="./reports")
  
  # List jobs command
  list_parser = subparsers.add_parser("list-jobs", help="List scheduled jobs")
  
  # Cancel job command
  cancel_parser = subparsers.add_parser("cancel", help="Cancel scheduled job")
  cancel_parser.add_argument("--job-id", required=True)
  
  # History command
  history_parser = subparsers.add_parser("history", help="Show audit history")
  history_parser.add_argument("--url", required=True)
  history_parser.add_argument("--limit", type=int, default=10)
  
  # Trends command
  trends_parser = subparsers.add_parser("trends", help="Show score trends")
  trends_parser.add_argument("--url", required=True)
  ```
- **ADD** command handlers in `main()`:
  ```python
  if args.command == "schedule":
      from .scripts.scheduler import schedule_audit
      job_id = schedule_audit(
          url=args.url,
          company_name=args.company,
          keywords=args.keywords.split(","),
          interval=args.interval,
          output_dir=args.output_dir
      )
      print(f"Scheduled audit: {job_id}")
  
  elif args.command == "list-jobs":
      from .scripts.scheduler import list_scheduled_jobs
      jobs = list_scheduled_jobs()
      for job in jobs:
          print(f"{job['id']}: next run {job['next_run']}")
  
  elif args.command == "history":
      from .scripts.history import get_history
      history = get_history(args.url, limit=args.limit)
      for h in history:
          print(f"{h['timestamp']}: {h['overall_score']} ({h['grade']})")
  
  elif args.command == "trends":
      from .scripts.trends import analyze_trends
      trends = analyze_trends(args.url)
      print(f"Trend: {trends['trend']}")
      print(f"Current: {trends['current_score']}, Change: {trends['change']:+d}")
  ```
- **VALIDATE**: `python -m seo_health_report --help`

### Task 6: ADD history saving to main generate_report

- **IMPLEMENT**: Auto-save audit results to history
- **ADD** to `generate_report()` after report generation:
  ```python
  # Save to history
  try:
      from .scripts.history import save_audit
      save_audit(
          url=target_url,
          company_name=company_name,
          results=result,
          report_path=result.get("report", {}).get("output_path")
      )
  except Exception as e:
      result["warnings"].append(f"Could not save to history: {e}")
  ```
- **VALIDATE**: Run audit, then check history

---

## TESTING STRATEGY

### Manual Validation

1. Schedule a daily audit
2. Verify job appears in `list-jobs`
3. Run manual audit, check history saved
4. Run second audit, verify trend analysis works
5. Cancel scheduled job

### Edge Cases

1. Schedule same URL twice → should replace existing job
2. History for new URL → empty list, no errors
3. Trends with <2 data points → "insufficient_data" response

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style

```bash
python -m py_compile seo-health-report/scripts/scheduler.py
python -m py_compile seo-health-report/scripts/history.py
python -m py_compile seo-health-report/scripts/trends.py
```

### Level 2: Import Tests

```bash
python -c "from seo_health_report.scripts.scheduler import schedule_audit, list_scheduled_jobs"
python -c "from seo_health_report.scripts.history import save_audit, get_history"
python -c "from seo_health_report.scripts.trends import analyze_trends"
```

### Level 3: History Test

```bash
python -c "
from seo_health_report.scripts.history import save_audit, get_history

# Save test audit
save_audit(
    url='https://test.com',
    company_name='Test',
    results={'overall_score': 75, 'grade': 'C', 'component_scores': {}}
)

# Retrieve
history = get_history('https://test.com')
print(f'History entries: {len(history)}')
print(f'Latest score: {history[0][\"overall_score\"]}')
"
```

### Level 4: CLI Test

```bash
python -m seo_health_report history --url https://test.com --limit 5
python -m seo_health_report trends --url https://test.com
```

---

## ACCEPTANCE CRITERIA

- [ ] Audits can be scheduled (daily/weekly/monthly)
- [ ] Scheduled jobs persist across restarts (SQLite job store)
- [ ] Audit history saved automatically
- [ ] History retrievable via CLI and API
- [ ] Trend analysis shows improving/declining/stable
- [ ] Significant changes detected and logged
- [ ] Jobs can be listed and cancelled
- [ ] Graceful handling when scheduler not running

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each validation command passes
- [ ] Scheduler starts without blocking
- [ ] History database created automatically
- [ ] CLI commands work as expected

---

## NOTES

**Design Decision**: Using APScheduler with SQLite for simplicity. For production scale, could migrate to Redis job store.

**Trade-off**: BackgroundScheduler runs in-process. For true daemon behavior, would need separate scheduler service.

**Limitation**: Scheduler only runs while Python process is active. For always-on scheduling, recommend system cron + CLI.

**Future Enhancement**: 
- Email alerts on significant changes
- Web dashboard for schedule management
- Webhook notifications
