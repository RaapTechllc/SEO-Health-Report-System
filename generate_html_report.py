#!/usr/bin/env python3
"""Generate HTML report from JSON audit results."""

import json
import sys
from pathlib import Path
from datetime import datetime

def generate_html_report(json_path: str, output_path: str = None):
    """Generate HTML report from JSON audit results."""
    
    with open(json_path) as f:
        data = json.load(f)
    
    company = data.get("company_name", "Unknown")
    url = data.get("url", "")
    timestamp = data.get("timestamp", "")[:10]
    overall_score = data.get("overall_score", 0)
    grade = data.get("grade", "N/A")
    
    # Get component scores
    tech_score = data.get("audits", {}).get("technical", {}).get("score", 0) or 0
    content_score = data.get("audits", {}).get("content", {}).get("score", 0) or 0
    ai_score = data.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0
    
    # Grade color
    grade_colors = {
        "A": "#28a745",
        "B": "#5cb85c",
        "C": "#f0ad4e",
        "D": "#d9534f",
        "F": "#c9302c"
    }
    grade_color = grade_colors.get(grade, "#6c757d")
    
    # Collect findings
    findings = []
    for audit_name, audit_data in data.get("audits", {}).items():
        if not audit_data:
            continue
        for comp_name, comp_data in audit_data.get("components", {}).items():
            for finding in comp_data.get("findings", [])[:2]:
                findings.append({"source": audit_name, "finding": finding})
    
    # Collect recommendations
    recommendations = []
    for audit_name, audit_data in data.get("audits", {}).items():
        if not audit_data:
            continue
        for rec in audit_data.get("recommendations", [])[:3]:
            recommendations.append(rec)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Health Report - {company}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a73e8, #0d47a1); color: white; padding: 40px; border-radius: 12px; margin-bottom: 30px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header .url {{ opacity: 0.9; font-size: 1.1em; }}
        .header .date {{ opacity: 0.7; margin-top: 10px; }}
        .score-card {{ background: white; border-radius: 12px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .overall-score {{ font-size: 5em; font-weight: bold; color: {grade_color}; }}
        .grade {{ display: inline-block; background: {grade_color}; color: white; padding: 10px 30px; border-radius: 50px; font-size: 1.5em; font-weight: bold; margin-top: 10px; }}
        .components {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 30px; }}
        .component {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .component h3 {{ color: #666; font-size: 0.9em; text-transform: uppercase; margin-bottom: 10px; }}
        .component .score {{ font-size: 2em; font-weight: bold; color: #1a73e8; }}
        .section {{ background: white; border-radius: 12px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #1a73e8; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #e0e0e0; }}
        .finding {{ padding: 15px; background: #f8f9fa; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #1a73e8; }}
        .finding .source {{ font-size: 0.8em; color: #666; text-transform: uppercase; margin-bottom: 5px; }}
        .recommendation {{ padding: 15px; background: #fff3cd; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #ffc107; }}
        .recommendation.high {{ background: #f8d7da; border-left-color: #dc3545; }}
        .recommendation .priority {{ font-size: 0.8em; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }}
        .recommendation.high .priority {{ color: #dc3545; }}
        .footer {{ text-align: center; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SEO Health Report</h1>
            <div class="url">{company}</div>
            <div class="url">{url}</div>
            <div class="date">Generated: {timestamp}</div>
        </div>
        
        <div class="score-card">
            <div class="overall-score">{overall_score}</div>
            <div>/100</div>
            <div class="grade">Grade: {grade}</div>
            
            <div class="components">
                <div class="component">
                    <h3>Technical</h3>
                    <div class="score">{tech_score}</div>
                </div>
                <div class="component">
                    <h3>Content</h3>
                    <div class="score">{content_score}</div>
                </div>
                <div class="component">
                    <h3>AI Visibility</h3>
                    <div class="score">{ai_score}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Key Findings</h2>
'''
    
    for f in findings[:10]:
        html += f'''            <div class="finding">
                <div class="source">{f["source"]}</div>
                {f["finding"]}
            </div>
'''
    
    html += '''        </div>
        
        <div class="section">
            <h2>Top Recommendations</h2>
'''
    
    for rec in recommendations[:5]:
        priority = rec.get("priority", "medium")
        action = rec.get("action", "")
        details = rec.get("details", "")
        priority_class = "high" if priority == "high" else ""
        html += f'''            <div class="recommendation {priority_class}">
                <div class="priority">{priority}</div>
                <strong>{action}</strong>
                <div>{details}</div>
            </div>
'''
    
    html += '''        </div>
        
        <div class="footer">
            <p>Generated by SEO Health Report System</p>
        </div>
    </div>
</body>
</html>'''
    
    if output_path is None:
        output_path = json_path.replace(".json", ".html")
    
    with open(output_path, "w") as f:
        f.write(html)
    
    print(f"HTML report generated: {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_html_report.py <json_file> [output_file]")
        sys.exit(1)
    
    json_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    generate_html_report(json_path, output_path)
