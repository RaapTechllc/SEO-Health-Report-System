#!/usr/bin/env python3
"""
Premium PDF Report Generator

Generates professional, agency-quality SEO health reports with:
- Company logo and custom branding
- Gemini-enhanced executive summaries with emojis
- Matplotlib charts and visualizations
- Professional branding and layout
- Comprehensive findings and recommendations
"""

import os
import sys
import json
import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from io import BytesIO
from urllib.parse import urlparse

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.local')
load_dotenv('.env')

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "seo-health-report"))

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image, PageBreak, ListFlowable, ListItem, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart


def hex_to_rgb(hex_str: str) -> tuple:
    """Convert hex to RGB tuple (0-1 scale)."""
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i:i+2], 16) / 255 for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB (0-255) to hex string."""
    return f"#{r:02x}{g:02x}{b:02x}"


# Get model names from environment (updated Jan 2026)
GEMINI_TEXT_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3-flash-preview')
GEMINI_IMAGE_MODEL = os.environ.get('GEMINI_IMAGE_MODEL', 'imagen-3.0-generate-002')


def generate_gemini_summary(company_name: str, score: int, grade: str, 
                            tech_score: int, content_score: int, ai_score: int,
                            industry: str) -> Optional[str]:
    """Generate executive summary using Gemini."""
    api_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return None
    
    prompt = f"""Write a brief, professional executive summary (3-4 sentences) for an SEO health report.

Company: {company_name}
Industry: {industry}
Overall Score: {score}/100 (Grade: {grade})
Technical SEO: {tech_score}/100
Content & Authority: {content_score}/100  
AI Visibility: {ai_score}/100

Use appropriate emojis (✅, ⚠️, 🚨, 📈, 🎯) sparingly.
Be specific about what's working and what needs attention.
End with an encouraging but actionable statement.
Keep it professional and suitable for a C-level executive."""

    try:
        import httpx
        model = GEMINI_TEXT_MODEL
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
        response = httpx.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.7}
        }, timeout=30)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"Gemini text API ({model}) returned {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"Gemini summary generation failed: {e}")
    
    return None


def generate_gemini_score_badge(score: int, grade: str, company_name: str, output_path: str) -> Optional[str]:
    """Generate a premium score badge using Gemini Imagen."""
    api_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return None
    
    # Determine color based on score
    if score >= 80:
        color_desc = "green, success, healthy"
    elif score >= 60:
        color_desc = "yellow-orange, caution, warning"
    else:
        color_desc = "red-orange, alert, critical"
    
    prompt = f"""Create a premium circular score gauge visualization for a business report:

DESIGN REQUIREMENTS:
- Clean circular progress ring showing {score}% filled
- Large "{score}" number in center (bold)
- "out of 100" smaller text below the number
- Grade letter "{grade}" in a colored badge below
- Color theme: {color_desc} gradient for the filled portion
- Unfilled portion in light gray
- White background
- Subtle drop shadow for depth
- Modern, flat design aesthetic
- Professional consulting report quality (McKinsey/Deloitte style)
- 1:1 square aspect ratio
- NO company name or extra text"""

    try:
        import httpx
        import base64
        model = GEMINI_IMAGE_MODEL
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}'
        
        response = httpx.post(url, json={
            'instances': [{'prompt': prompt}],
            'parameters': {'sampleCount': 1, 'aspectRatio': '1:1'}
        }, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if 'predictions' in data and data['predictions']:
                img_data = data['predictions'][0].get('bytesBase64Encoded')
                if img_data:
                    with open(output_path, 'wb') as f:
                        f.write(base64.b64decode(img_data))
                    print(f"[OK] Generated Gemini score badge using {model}")
                    return output_path
        else:
            print(f"Gemini badge API ({model}) returned {response.status_code}")
    except Exception as e:
        print(f"Gemini badge generation failed: {e}")
    
    return None


def generate_gemini_header_image(company_name: str, industry: str, output_path: str) -> Optional[str]:
    """Generate a professional header banner using Gemini Imagen."""
    api_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return None
    
    prompt = f"""Create a subtle professional header banner for a business report:

DESIGN:
- Abstract geometric pattern with flowing lines
- {industry} industry aesthetic (subtle visual cues)
- Primary colors: deep blue (#1a73e8) and dark gray (#202124)
- Gradient flowing from left to right
- Modern, minimal, corporate style
- NO text, logos, or words
- Suitable as PDF report header decoration
- 16:9 wide aspect ratio
- Premium consulting firm report cover style"""

    try:
        import httpx
        import base64
        model = GEMINI_IMAGE_MODEL
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}'
        
        response = httpx.post(url, json={
            'instances': [{'prompt': prompt}],
            'parameters': {'sampleCount': 1, 'aspectRatio': '16:9'}
        }, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if 'predictions' in data and data['predictions']:
                img_data = data['predictions'][0].get('bytesBase64Encoded')
                if img_data:
                    with open(output_path, 'wb') as f:
                        f.write(base64.b64decode(img_data))
                    print(f"[OK] Generated Gemini header image using {model}")
                    return output_path
        else:
            print(f"Gemini header API ({model}) returned {response.status_code}")
    except Exception as e:
        print(f"Gemini header generation failed: {e}")
    
    return None


def get_dominant_colors(image_path: str, num_colors: int = 3) -> List[str]:
    """Extract dominant colors from an image."""
    try:
        img = PILImage.open(image_path)
        img = img.convert('RGB')
        img = img.resize((100, 100))  # Resize for speed
        
        pixels = list(img.getdata())
        
        # Simple color clustering
        color_counts = {}
        for pixel in pixels:
            # Skip very light colors (likely background)
            if sum(pixel) > 700:
                continue
            # Quantize to reduce colors
            quantized = (pixel[0] // 32 * 32, pixel[1] // 32 * 32, pixel[2] // 32 * 32)
            color_counts[quantized] = color_counts.get(quantized, 0) + 1
        
        # Sort by frequency
        sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return top colors as hex
        result = []
        for color, _ in sorted_colors[:num_colors]:
            result.append(rgb_to_hex(*color))
        
        return result if result else ["#1a73e8", "#34a853", "#202124"]
        
    except Exception as e:
        print(f"Could not extract colors: {e}")
        return ["#1a73e8", "#34a853", "#202124"]


def fetch_company_logo(url: str, company_name: str, output_dir: Path) -> Optional[str]:
    """Fetch company logo from website or Clearbit."""
    # Use company-specific filename to avoid caching issues
    safe_name = "".join(c if c.isalnum() else "_" for c in company_name)[:20]
    logo_path = output_dir / f"logo_{safe_name}.png"
    
    # Check if we already have this company's logo
    if logo_path.exists() and logo_path.stat().st_size > 1000:
        print(f"✅ Using cached logo for {company_name}")
        return str(logo_path)
    
    domain = urlparse(url).netloc.replace("www.", "")
    
    # Try to find logo on the website first
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            import re
            # Look for logo in HTML
            logo_patterns = [
                rf'src="([^"]*logo[^"]*\.(?:png|jpg|jpeg|svg))"',
                rf'src="([^"]*{re.escape(company_name.split()[0].lower())}[^"]*\.(?:png|jpg|jpeg|svg))"',
            ]
            for pattern in logo_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                for match in matches:
                    logo_url = match if match.startswith('http') else f"https://{domain}{match}" if match.startswith('/') else f"https://{domain}/{match}"
                    try:
                        logo_resp = requests.get(logo_url, timeout=10)
                        if logo_resp.status_code == 200 and len(logo_resp.content) > 1000:
                            with open(logo_path, 'wb') as f:
                                f.write(logo_resp.content)
                            print(f"✅ Fetched logo from website for {company_name}")
                            return str(logo_path)
                    except:
                        continue
    except Exception as e:
        print(f"Website logo fetch failed: {e}")
    
    # Try Clearbit Logo API
    clearbit_url = f"https://logo.clearbit.com/{domain}"
    try:
        response = requests.get(clearbit_url, timeout=10)
        if response.status_code == 200 and len(response.content) > 1000:
            with open(logo_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Fetched logo from Clearbit for {domain}")
            return str(logo_path)
    except Exception as e:
        print(f"Clearbit logo fetch failed: {e}")
    
    # Try Clearbit Logo API (free, no key needed)
    clearbit_url = f"https://logo.clearbit.com/{domain}"
    
    try:
        response = requests.get(clearbit_url, timeout=10)
        if response.status_code == 200 and len(response.content) > 1000:
            with open(logo_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Fetched logo from Clearbit for {domain}")
            return str(logo_path)
    except Exception as e:
        print(f"Clearbit logo fetch failed: {e}")
    
    # Try favicon as fallback
    favicon_urls = [
        f"https://{domain}/favicon.ico",
        f"https://{domain}/apple-touch-icon.png",
        f"https://{domain}/favicon-32x32.png",
    ]
    
    for fav_url in favicon_urls:
        try:
            response = requests.get(fav_url, timeout=5)
            if response.status_code == 200 and len(response.content) > 500:
                # Convert to PNG if needed
                img = PILImage.open(BytesIO(response.content))
                img = img.convert('RGBA')
                # Resize to reasonable size
                img = img.resize((128, 128), PILImage.Resampling.LANCZOS)
                img.save(logo_path, 'PNG')
                print(f"✅ Fetched favicon from {domain}")
                return str(logo_path)
        except Exception:
            continue
    
    print(f"⚠️ Could not fetch logo for {domain}")
    return None


def get_industry_theme(company_name: str, url: str) -> Dict[str, str]:
    """Get industry-appropriate color theme based on company/URL."""
    name_lower = company_name.lower()
    domain = urlparse(url).netloc.lower()
    
    # Industry detection and theming
    if any(word in name_lower or word in domain for word in ['metal', 'steel', 'iron', 'fabricat', 'weld', 'machine']):
        return {
            "primary": "#2c3e50",      # Dark steel blue
            "secondary": "#e67e22",    # Industrial orange
            "accent": "#95a5a6",       # Metal gray
            "industry": "Manufacturing"
        }
    elif any(word in name_lower or word in domain for word in ['tech', 'software', 'digital', 'cyber', 'cloud', 'data']):
        return {
            "primary": "#3498db",      # Tech blue
            "secondary": "#2ecc71",    # Success green
            "accent": "#9b59b6",       # Purple
            "industry": "Technology"
        }
    elif any(word in name_lower or word in domain for word in ['health', 'medical', 'care', 'clinic', 'hospital', 'dental']):
        return {
            "primary": "#1abc9c",      # Medical teal
            "secondary": "#3498db",    # Trust blue
            "accent": "#e74c3c",       # Alert red
            "industry": "Healthcare"
        }
    elif any(word in name_lower or word in domain for word in ['law', 'legal', 'attorney', 'lawyer']):
        return {
            "primary": "#2c3e50",      # Professional navy
            "secondary": "#c0392b",    # Authority red
            "accent": "#f39c12",       # Gold
            "industry": "Legal"
        }
    elif any(word in name_lower or word in domain for word in ['food', 'restaurant', 'cafe', 'kitchen', 'bakery']):
        return {
            "primary": "#d35400",      # Warm orange
            "secondary": "#27ae60",    # Fresh green
            "accent": "#f1c40f",       # Appetizing yellow
            "industry": "Food & Beverage"
        }
    elif any(word in name_lower or word in domain for word in ['real', 'estate', 'property', 'home', 'house']):
        return {
            "primary": "#2980b9",      # Trust blue
            "secondary": "#27ae60",    # Growth green
            "accent": "#f39c12",       # Warm gold
            "industry": "Real Estate"
        }
    else:
        return {
            "primary": "#1a73e8",      # Default blue
            "secondary": "#34a853",    # Default green
            "accent": "#fbbc04",       # Default yellow
            "industry": "Business"
        }


class PremiumReportGenerator:
    """Generate premium PDF reports."""
    
    # Brand colors
    COLORS = {
        "primary": "#1a73e8",
        "secondary": "#34a853", 
        "warning": "#fbbc04",
        "danger": "#ea4335",
        "dark": "#202124",
        "light": "#f8f9fa",
        "grade_a": "#28a745",
        "grade_b": "#5cb85c",
        "grade_c": "#f0ad4e",
        "grade_d": "#d9534f",
        "grade_f": "#c9302c",
    }
    
    def __init__(self, audit_data: Dict[str, Any], output_path: str, logo_path: str = None):
        self.data = audit_data
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self.elements = []
        self.charts_dir = Path(output_path).parent / "charts"
        self.charts_dir.mkdir(exist_ok=True)
        
        # Get company info
        self.company_name = audit_data.get("company_name", "Company")
        self.url = audit_data.get("url", "")
        
        # Fetch logo if not provided
        if logo_path and os.path.exists(logo_path):
            self.logo_path = logo_path
        else:
            self.logo_path = fetch_company_logo(self.url, self.company_name, self.charts_dir)
        
        # Get industry theme
        self.theme = get_industry_theme(self.company_name, self.url)
        
        # Extract colors from logo if available
        if self.logo_path:
            logo_colors = get_dominant_colors(self.logo_path)
            if logo_colors:
                self.theme["primary"] = logo_colors[0]
                if len(logo_colors) > 1:
                    self.theme["secondary"] = logo_colors[1]
        
        # Update COLORS with theme
        self.COLORS["primary"] = self.theme["primary"]
        self.COLORS["secondary"] = self.theme["secondary"]
        
        self._setup_styles()
        
    def _setup_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            'CoverTitle',
            parent=self.styles['Title'],
            fontSize=36,
            textColor=colors.HexColor(self.COLORS["primary"]),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold',
        ))
        self.styles.add(ParagraphStyle(
            'CoverSubtitle',
            parent=self.styles['Heading2'],
            fontSize=24,
            textColor=colors.HexColor(self.COLORS["dark"]),
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold',
        ))
        self.styles.add(ParagraphStyle(
            'SectionTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor(self.COLORS["primary"]),
            spaceBefore=24,
            spaceAfter=12,
            fontName='Helvetica-Bold',
            borderPadding=5,
        ))
        self.styles.add(ParagraphStyle(
            'SubSection',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor(self.COLORS["dark"]),
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold',
        ))
        self.styles.add(ParagraphStyle(
            'CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=14,
        ))
        self.styles.add(ParagraphStyle(
            'Finding',
            parent=self.styles['Normal'],
            fontSize=9,
            leftIndent=15,
            spaceAfter=4,
            leading=12,
        ))
        self.styles.add(ParagraphStyle(
            'BulletItem',
            parent=self.styles['Normal'],
            fontSize=9,
            leftIndent=25,
            spaceAfter=3,
            bulletIndent=15,
            leading=12,
        ))
        self.styles.add(ParagraphStyle(
            'ScoreText',
            parent=self.styles['Normal'],
            fontSize=48,
            alignment=TA_CENTER,
            textColor=colors.HexColor(self.COLORS["primary"]),
        ))
        self.styles.add(ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            fontName='Helvetica-Bold',
        ))
        self.styles.add(ParagraphStyle(
            'SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER,
        ))
        
    def _get_grade_color(self, grade: str) -> str:
        """Get color for grade."""
        return self.COLORS.get(f"grade_{grade.lower()}", self.COLORS["dark"])
    
    def _get_score_color(self, score: int) -> str:
        """Get color based on score."""
        if score >= 90: return self.COLORS["grade_a"]
        if score >= 80: return self.COLORS["grade_b"]
        if score >= 70: return self.COLORS["grade_c"]
        if score >= 60: return self.COLORS["grade_d"]
        return self.COLORS["grade_f"]
    
    def _create_score_chart(self) -> str:
        """Create overall score gauge chart."""
        score = self.data.get("overall_score", 0) or 0
        grade = self.data.get("grade", "F")
        
        fig, ax = plt.subplots(figsize=(5, 3.5))
        
        # Create semi-circle gauge
        theta = np.linspace(0, np.pi, 100)
        
        # Background arc segments (gray zones)
        for i, (start, end, alpha) in enumerate([(0, 0.6, 0.15), (0.6, 0.7, 0.1), (0.7, 0.8, 0.08), (0.8, 1.0, 0.05)]):
            segment_theta = np.linspace(start * np.pi, end * np.pi, 20)
            ax.fill_between(segment_theta, 0.6, 1, alpha=alpha, color='gray')
        
        # Score arc
        score_theta = np.linspace(0, np.pi * score / 100, 100)
        color = self._get_score_color(score)
        ax.fill_between(score_theta, 0.6, 1, alpha=0.9, color=color)
        
        # Inner circle (white)
        inner_circle = plt.Circle((0, 0), 0.55, color='white', zorder=5)
        ax.add_patch(inner_circle)
        
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-0.3, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Score text
        ax.text(0, 0.25, f"{score}", fontsize=42, ha='center', va='center', 
                fontweight='bold', color=color, zorder=10)
        ax.text(0, -0.05, f"Grade: {grade}", fontsize=16, ha='center', va='center',
                color=self.COLORS["dark"], fontweight='bold', zorder=10)
        
        # Company name
        company = self.data.get("company_name", "")
        ax.text(0, 1.1, f"{company}", fontsize=11, ha='center', va='center',
                color=self.COLORS["primary"], fontweight='bold')
        
        chart_path = str(self.charts_dir / "overall_score.png")
        plt.savefig(chart_path, dpi=150, bbox_inches='tight', 
                    facecolor='white', edgecolor='none', pad_inches=0.1)
        plt.close()
        return chart_path
    
    def _create_component_chart(self) -> str:
        """Create component scores bar chart."""
        tech = self.data.get("audits", {}).get("technical", {}).get("score", 0) or 0
        content = self.data.get("audits", {}).get("content", {}).get("score", 0) or 0
        ai = self.data.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0
        
        fig, ax = plt.subplots(figsize=(6.5, 2.2))
        
        components = ['Technical SEO (30%)', 'Content & Authority (35%)', 'AI Visibility (35%)']
        scores = [tech, content, ai]
        colors_list = [self._get_score_color(s) for s in scores]
        
        # Create horizontal bars
        y_pos = np.arange(len(components))
        bars = ax.barh(y_pos, scores, color=colors_list, height=0.5, edgecolor='white', linewidth=1)
        
        # Add background bars (to 100)
        ax.barh(y_pos, [100]*3, color='#f0f0f0', height=0.5, zorder=0)
        
        # Add score labels inside bars
        for i, (bar, score) in enumerate(zip(bars, scores)):
            label_x = max(score - 8, 5) if score > 20 else score + 3
            label_color = 'white' if score > 20 else self.COLORS["dark"]
            ax.text(label_x, i, f'{score}', va='center', ha='center' if score > 20 else 'left',
                    fontsize=11, fontweight='bold', color=label_color, zorder=10)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(components, fontsize=9)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.tick_params(axis='x', labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        # Add benchmark line
        ax.axvline(x=70, color='#666', linestyle='--', alpha=0.7, linewidth=1)
        ax.text(71, 2.3, 'Target: 70', fontsize=7, color='#666')
        
        plt.tight_layout()
        chart_path = str(self.charts_dir / "components.png")
        plt.savefig(chart_path, dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none', pad_inches=0.1)
        plt.close()
        return chart_path
    
    def _create_radar_chart(self) -> Optional[str]:
        """Create radar chart for detailed breakdown."""
        # Get sub-component scores
        tech = self.data.get("audits", {}).get("technical", {}).get("components", {})
        
        categories = []
        scores = []
        max_scores = []
        
        for name, data in tech.items():
            if isinstance(data, dict):
                categories.append(name.replace("_", " ").title()[:12])
                scores.append(data.get("score", 0) or 0)
                max_scores.append(data.get("max", 100) or 100)
        
        if len(categories) < 3:
            return None
            
        # Normalize scores to 0-100
        normalized = [s/m*100 if m > 0 else 0 for s, m in zip(scores, max_scores)]
        
        # Create radar chart
        angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
        normalized += normalized[:1]
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.fill(angles, normalized, color=self.COLORS["primary"], alpha=0.25)
        ax.plot(angles, normalized, color=self.COLORS["primary"], linewidth=2)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=9)
        ax.set_ylim(0, 100)
        ax.set_title('Technical Components', fontsize=14, fontweight='bold',
                     color=self.COLORS["primary"], pad=20)
        
        chart_path = str(self.charts_dir / "radar.png")
        plt.savefig(chart_path, dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close()
        return chart_path
    
    def _fetch_company_contact_info(self) -> Dict[str, str]:
        """Fetch company contact info from website."""
        url = self.data.get("url", "")
        if not url:
            return {}
        
        try:
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code != 200:
                return {}
            
            html = response.text.lower()
            import re
            
            info = {}
            
            # Extract phone
            phone_patterns = [
                r'tel:([+\d\-\(\)\s]{10,20})',
                r'phone[:\s]*([+\d\-\(\)\s\.]{10,20})',
                r'(\(\d{3}\)\s*\d{3}[-.\s]?\d{4})',
                r'(\d{3}[-.\s]\d{3}[-.\s]\d{4})',
            ]
            for pattern in phone_patterns:
                match = re.search(pattern, html)
                if match:
                    info['phone'] = match.group(1).strip()
                    break
            
            # Extract email
            email_match = re.search(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', html)
            if email_match:
                info['email'] = email_match.group(1)
            else:
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', html)
                if email_match:
                    info['email'] = email_match.group(1)
            
            # Extract address - look for common patterns
            address_patterns = [
                r'(\d+\s+[A-Za-z\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|blvd|boulevard)[,\s]+[A-Za-z\s]+,?\s*[A-Z]{2}\s*\d{5})',
                r'(\d+\s+[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5})',
            ]
            for pattern in address_patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    info['address'] = match.group(1).strip()
                    break
            
            return info
        except Exception as e:
            print(f"Could not fetch contact info: {e}")
            return {}
    
    def _add_cover_page(self):
        """Add professional cover page with company info and branding."""
        company = self.data.get("company_name", "Company")
        url = self.data.get("url", "")
        date = datetime.now().strftime("%B %d, %Y")
        industry = self.theme.get("industry", "Business")
        score = self.data.get("overall_score", 0) or 0
        grade = self.data.get("grade", "F")
        
        # Fetch contact info
        contact_info = self._fetch_company_contact_info()
        
        # Try to generate Gemini header banner
        safe_company = "".join(c if c.isalnum() else "_" for c in company)[:20]
        header_path = str(self.charts_dir / f"header_{safe_company}.png")
        if not os.path.exists(header_path):
            generate_gemini_header_image(company, industry, header_path)
        
        # Add header banner if available, otherwise colored bar
        if os.path.exists(header_path):
            try:
                header_img = Image(header_path, width=7.5*inch, height=1.2*inch)
                header_img.hAlign = 'CENTER'
                self.elements.append(header_img)
                self.elements.append(Spacer(1, 0.2*inch))
            except:
                self._add_header_bar()
        else:
            self._add_header_bar()
        
        # Company logo - properly sized
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                with PILImage.open(self.logo_path) as img:
                    w, h = img.size
                    aspect = w / h
                    # Smart sizing based on aspect ratio
                    if aspect > 3:  # Very wide logo
                        logo_width = 3.5*inch
                        logo_height = logo_width / aspect
                    elif aspect > 1.5:  # Wide logo
                        logo_width = 2.5*inch
                        logo_height = logo_width / aspect
                    elif aspect < 0.7:  # Tall logo
                        logo_height = 1.2*inch
                        logo_width = logo_height * aspect
                    else:  # Square-ish logo
                        logo_height = 1.2*inch
                        logo_width = logo_height * aspect
                
                logo_img = Image(self.logo_path, width=logo_width, height=logo_height)
                logo_img.hAlign = 'CENTER'
                self.elements.append(logo_img)
                self.elements.append(Spacer(1, 0.25*inch))
            except Exception as e:
                print(f"Could not add logo: {e}")
        
        # Title - clean typography
        title_style = ParagraphStyle('CoverTitle', parent=self.styles['Title'],
            fontSize=36, textColor=colors.HexColor(self.COLORS["primary"]),
            alignment=TA_CENTER, spaceAfter=6, spaceBefore=0, 
            fontName='Helvetica-Bold', leading=40)
        self.elements.append(Paragraph("SEO Health Report", title_style))
        
        # Subtitle - clearly separated
        subtitle_style = ParagraphStyle('Subtitle', parent=self.styles['Normal'],
            fontSize=13, textColor=colors.HexColor("#666666"), 
            alignment=TA_CENTER, spaceAfter=20)
        self.elements.append(Paragraph("Comprehensive Website Analysis &amp; Recommendations", subtitle_style))
        
        # Company name
        company_style = ParagraphStyle('CompanyName', parent=self.styles['Heading1'],
            fontSize=22, textColor=colors.HexColor(self.COLORS["dark"]),
            alignment=TA_CENTER, spaceAfter=4, fontName='Helvetica-Bold')
        self.elements.append(Paragraph(company, company_style))
        
        # URL
        url_style = ParagraphStyle('URL', parent=self.styles['Normal'], 
            fontSize=11, alignment=TA_CENTER, textColor=colors.HexColor(self.COLORS["primary"]))
        self.elements.append(Paragraph(url, url_style))
        self.elements.append(Spacer(1, 0.15*inch))
        
        # Contact info - clean formatting without emoji issues
        if contact_info:
            contact_parts = []
            if contact_info.get('phone'):
                phone = contact_info['phone'].strip()
                contact_parts.append(f"Phone: {phone}")
            if contact_info.get('email'):
                contact_parts.append(f"Email: {contact_info['email']}")
            if contact_info.get('address'):
                contact_parts.append(contact_info['address'])
            
            if contact_parts:
                contact_style = ParagraphStyle('Contact', parent=self.styles['Normal'],
                    fontSize=9, alignment=TA_CENTER, textColor=colors.gray, leading=13)
                self.elements.append(Paragraph(" | ".join(contact_parts), contact_style))
                self.elements.append(Spacer(1, 0.2*inch))
        
        # Try Gemini score badge first, fallback to clean table
        score_color = self._get_score_color(score)
        badge_path = str(self.charts_dir / f"badge_{safe_company}.png")
        
        if not os.path.exists(badge_path):
            generate_gemini_score_badge(score, grade, company, badge_path)
        
        if os.path.exists(badge_path):
            try:
                badge_img = Image(badge_path, width=2.5*inch, height=2.5*inch)
                badge_img.hAlign = 'CENTER'
                self.elements.append(badge_img)
                self.elements.append(Spacer(1, 0.15*inch))
            except:
                self._add_score_display(score, grade, score_color)
        else:
            self._add_score_display(score, grade, score_color)
        
        # Industry and date
        info_style = ParagraphStyle('Info', parent=self.styles['Normal'], 
            fontSize=10, alignment=TA_CENTER, textColor=colors.gray)
        self.elements.append(Paragraph(f"Industry: {industry}  |  Report Date: {date}", info_style))
        
        self.elements.append(Spacer(1, 0.5*inch))
        
        # Prepared by section
        prepared_style = ParagraphStyle('Prepared', parent=self.styles['Normal'],
            fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor(self.COLORS["dark"]))
        self.elements.append(Paragraph("<b>Prepared by</b>", prepared_style))
        self.elements.append(Spacer(1, 0.08*inch))
        
        brand_style = ParagraphStyle('Brand', parent=self.styles['Normal'],
            fontSize=12, textColor=colors.HexColor(self.COLORS["primary"]),
            alignment=TA_CENTER, fontName='Helvetica-Bold')
        self.elements.append(Paragraph("RaapTech SEO Intelligence", brand_style))
        
        contact_brand = ParagraphStyle('BrandContact', parent=self.styles['Normal'],
            fontSize=9, alignment=TA_CENTER, textColor=colors.gray)
        self.elements.append(Paragraph("www.raaptech.com | info@raaptech.com", contact_brand))
        
        # Footer bar
        self.elements.append(Spacer(1, 0.3*inch))
        footer_bar = Drawing(500, 4)
        footer_bar.add(Rect(0, 0, 500, 4, fillColor=colors.HexColor(self.COLORS["primary"]), strokeColor=None))
        self.elements.append(footer_bar)
        
        self.elements.append(PageBreak())
    
    def _add_header_bar(self):
        """Add simple colored header bar as fallback."""
        header_bar = Drawing(500, 8)
        header_bar.add(Rect(0, 0, 500, 8, fillColor=colors.HexColor(self.COLORS["primary"]), strokeColor=None))
        self.elements.append(header_bar)
        self.elements.append(Spacer(1, 0.3*inch))
    
    def _add_score_display(self, score: int, grade: str, score_color: str):
        """Add clean score display without debug borders."""
        # Centered score block
        score_style = ParagraphStyle('ScoreDisplay', parent=self.styles['Normal'],
            fontSize=48, alignment=TA_CENTER, textColor=colors.HexColor(score_color),
            fontName='Helvetica-Bold', spaceAfter=0)
        self.elements.append(Paragraph(str(score), score_style))
        
        label_style = ParagraphStyle('ScoreLabel', parent=self.styles['Normal'],
            fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor(self.COLORS["dark"]),
            spaceAfter=8)
        self.elements.append(Paragraph("out of 100", label_style))
        
        grade_style = ParagraphStyle('GradeDisplay', parent=self.styles['Normal'],
            fontSize=18, alignment=TA_CENTER, textColor=colors.HexColor(score_color),
            fontName='Helvetica-Bold', spaceAfter=15)
        self.elements.append(Paragraph(f"Grade: {grade}", grade_style))
    
    def _add_table_of_contents(self):
        """Add table of contents."""
        self.elements.append(Paragraph("Table of Contents", self.styles['SectionTitle']))
        self.elements.append(Spacer(1, 0.2*inch))
        
        # Check if market intelligence is available
        has_market_intel = "market_intelligence" in self.data
        
        toc_items = [
            ("1. Executive Summary", "Key findings and overall score"),
            ("2. Scoring Methodology", "How we calculate your SEO health"),
        ]
        
        # Add market intelligence sections if available
        if has_market_intel:
            toc_items.extend([
                ("3. Market Position Analysis", "Your competitive standing in the market"),
                ("4. Competitor Benchmarking", "Side-by-side comparison with competitors"),
                ("5. Technical SEO Analysis", "Site structure, speed, and security"),
                ("6. Content & Authority", "Content quality and E-E-A-T signals"),
                ("7. AI Visibility Assessment", "Presence in AI-generated responses"),
                ("8. Prioritized Recommendations", "Action items ranked by impact"),
                ("9. Appendix", "Detailed data and methodology"),
            ])
        else:
            toc_items.extend([
                ("3. Technical SEO Analysis", "Site structure, speed, and security"),
                ("4. Content & Authority", "Content quality and E-E-A-T signals"),
                ("5. AI Visibility Assessment", "Presence in AI-generated responses"),
                ("6. Prioritized Recommendations", "Action items ranked by impact"),
                ("7. Appendix", "Detailed data and methodology"),
            ])
        
        toc_style = ParagraphStyle('TOC', parent=self.styles['Normal'],
            fontSize=11, spaceAfter=8, leftIndent=20)
        toc_desc_style = ParagraphStyle('TOCDesc', parent=self.styles['Normal'],
            fontSize=9, textColor=colors.gray, leftIndent=40, spaceAfter=12)
        
        for title, desc in toc_items:
            self.elements.append(Paragraph(f"<b>{title}</b>", toc_style))
            self.elements.append(Paragraph(desc, toc_desc_style))
        
        self.elements.append(PageBreak())
    
    def _add_methodology_section(self):
        """Add scoring methodology section."""
        self.elements.append(Paragraph("2. Scoring Methodology", self.styles['SectionTitle']))
        self.elements.append(Spacer(1, 0.15*inch))
        
        intro = """Our SEO Health Score is calculated using a weighted composite of three key areas, 
        each evaluated against industry best practices and search engine guidelines. This methodology 
        ensures a comprehensive view of your website's search visibility potential."""
        self.elements.append(Paragraph(intro, self.styles['CustomBodyText']))
        self.elements.append(Spacer(1, 0.15*inch))
        
        # Scoring breakdown table
        method_data = [
            ['Component', 'Weight', 'What We Measure'],
            ['Technical SEO', '30%', 'Crawlability, speed, security, mobile, structured data'],
            ['Content & Authority', '35%', 'Content quality, E-E-A-T, keywords, backlinks'],
            ['AI Visibility', '35%', 'Presence in ChatGPT, Claude, Perplexity responses'],
        ]
        
        method_table = Table(method_data, colWidths=[1.8*inch, 0.8*inch, 3.5*inch])
        method_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["primary"])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        self.elements.append(method_table)
        self.elements.append(Spacer(1, 0.2*inch))
        
        # Grade scale
        self.elements.append(Paragraph("<b>Grade Scale</b>", self.styles['SubSection']))
        grade_data = [
            ['Grade', 'Score Range', 'Interpretation'],
            ['A', '90-100', 'Excellent - Industry leader, minimal improvements needed'],
            ['B', '80-89', 'Good - Above average, some optimization opportunities'],
            ['C', '70-79', 'Average - Competitive but room for improvement'],
            ['D', '60-69', 'Below Average - Significant gaps affecting visibility'],
            ['F', '0-59', 'Poor - Critical issues requiring immediate attention'],
        ]
        
        grade_table = Table(grade_data, colWidths=[0.8*inch, 1.2*inch, 4*inch])
        grade_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["dark"])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            # Color code the grades
            ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor(self.COLORS["grade_a"])),
            ('TEXTCOLOR', (0, 2), (0, 2), colors.HexColor(self.COLORS["grade_b"])),
            ('TEXTCOLOR', (0, 3), (0, 3), colors.HexColor(self.COLORS["grade_c"])),
            ('TEXTCOLOR', (0, 4), (0, 4), colors.HexColor(self.COLORS["grade_d"])),
            ('TEXTCOLOR', (0, 5), (0, 5), colors.HexColor(self.COLORS["grade_f"])),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        self.elements.append(grade_table)
        self.elements.append(Spacer(1, 0.2*inch))
        
        # AI Visibility explanation
        ai_note = """<b>Why AI Visibility Matters (35% Weight):</b> With the rise of AI-powered search 
        (ChatGPT, Google AI Overviews, Perplexity), traditional SEO is no longer enough. We measure 
        how often your brand appears in AI-generated responses—a critical factor that most SEO 
        agencies don't track. This is your competitive advantage."""
        self.elements.append(Paragraph(ai_note, self.styles['CustomBodyText']))
        
        self.elements.append(PageBreak())
    
    def _add_executive_summary(self):
        """Add executive summary with score visualization."""
        self.elements.append(Paragraph("1. Executive Summary", self.styles['SectionTitle']))
        self.elements.append(Spacer(1, 0.1*inch))
        
        # === Executive Quick-Scan Box for busy executives ===
        self._add_executive_quickscan()
        
        # Overall score chart
        score_chart = self._create_score_chart()
        if os.path.exists(score_chart):
            img = Image(score_chart, width=3.8*inch, height=2.6*inch)
            img.hAlign = 'CENTER'
            self.elements.append(img)
        
        self.elements.append(Spacer(1, 0.2*inch))
        
        # Component breakdown chart - smaller
        comp_chart = self._create_component_chart()
        if os.path.exists(comp_chart):
            img = Image(comp_chart, width=6*inch, height=3*inch)
            img.hAlign = 'CENTER'
            self.elements.append(img)
        
        self.elements.append(Spacer(1, 0.15*inch))
        
        # Key insights - use premium summary if available from market intelligence
        market_intel = self.data.get("market_intelligence", {})
        premium_summary = market_intel.get("premium_executive_summary")
        
        if premium_summary:
            # Use the AI-generated premium executive summary
            self.elements.append(Paragraph("<b>Strategic Assessment:</b>", self.styles['SubSection']))
            
            # Split into paragraphs for better formatting
            paragraphs = premium_summary.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    self.elements.append(Paragraph(para.strip(), self.styles['CustomBodyText']))
                    self.elements.append(Spacer(1, 0.08*inch))
        else:
            # Fallback to original Gemini summary or template
            score = self.data.get("overall_score", 0) or 0
            grade = self.data.get("grade", "F")
            tech_score = self.data.get("audits", {}).get("technical", {}).get("score", 0) or 0
            content_score = self.data.get("audits", {}).get("content", {}).get("score", 0) or 0
            ai_score = self.data.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0
            
            gemini_summary = generate_gemini_summary(
                self.company_name, score, grade,
                tech_score, content_score, ai_score,
                self.theme.get("industry", "Business")
            )
            
            if gemini_summary:
                insight = gemini_summary
            elif score >= 80:
                insight = f"Your website demonstrates strong SEO health. Focus on maintaining current performance and addressing minor optimizations."
            elif score >= 60:
                insight = f"Your website has a solid foundation but significant opportunities for improvement exist. Prioritize the recommendations below."
            else:
                insight = f"{self.company_name}'s website requires immediate attention. Critical issues are impacting your search visibility and AI presence. The good news: addressing the recommendations in this report can significantly improve your online visibility."
            
            # Summary box
            self.elements.append(Paragraph("<b>Key Insight:</b>", self.styles['SubSection']))
            self.elements.append(Paragraph(insight, self.styles['CustomBodyText']))
        
        # === ROI/Revenue Impact Section ===
        self._add_roi_section()
        
        self.elements.append(PageBreak())
    
    def _add_executive_quickscan(self):
        """Add a scannable quick-scan box for busy executives."""
        score = self.data.get("overall_score", 0) or 0
        grade = self.data.get("grade", "F")
        ai_score = self.data.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0
        
        market_intel = self.data.get("market_intelligence", {})
        benchmark = market_intel.get("benchmark", {})
        
        # Determine top issues
        issues = []
        gaps = benchmark.get("critical_gaps", [])
        
        if gaps:
            issues = gaps[:3]
        else:
            if ai_score < 60:
                issues.append(f"AI Visibility Crisis: Score of {ai_score}/100 means invisible to AI-driven buyers")
            tech_score = self.data.get("audits", {}).get("technical", {}).get("score", 0) or 0
            if tech_score < 70:
                issues.append(f"Technical SEO gaps limiting search performance ({tech_score}/100)")
            content_score = self.data.get("audits", {}).get("content", {}).get("score", 0) or 0
            if content_score < 70:
                issues.append(f"Content authority below competitive threshold ({content_score}/100)")
        
        if not issues:
            issues = ["Minor optimizations needed to maintain competitive position"]
        
        rank = benchmark.get("market_position_rank", "N/A")
        total = len(market_intel.get("competitors", [])) + 1 if market_intel.get("competitors") else "N/A"
        
        score_color = self._get_score_color(score)
        
        quickscan_data = [
            [Paragraph("<b>EXECUTIVE QUICK-SCAN</b>", 
                      ParagraphStyle('QSTitle', fontSize=11, textColor=colors.white, alignment=TA_CENTER))],
        ]
        
        score_text = f"<b>Overall Score:</b> <font color='{score_color}'>{score}/100 (Grade: {grade})</font>"
        if rank != "N/A":
            score_text += f" | <b>Market Position:</b> #{rank} of {total}"
        quickscan_data.append([Paragraph(score_text, ParagraphStyle('QSContent', fontSize=9, leading=12))])
        
        issues_text = "<b>Top Issues:</b><br/>"
        for i, issue in enumerate(issues[:3], 1):
            issues_text += f"{i}. {issue}<br/>"
        quickscan_data.append([Paragraph(issues_text, ParagraphStyle('QSIssues', fontSize=9, leading=12))])
        
        roi_data = self.data.get("roi_projection", {})
        if roi_data:
            cost_of_inaction = roi_data.get("cost_of_inaction", {})
            monthly_cost = cost_of_inaction.get("monthly_opportunity_cost", "")
            if monthly_cost:
                roi_text = f"<b>Cost of Inaction:</b> {monthly_cost}/month in missed opportunities"
                quickscan_data.append([Paragraph(roi_text, ParagraphStyle('QSROI', fontSize=9, textColor=colors.HexColor("#dc2626")))])
        
        quickscan_table = Table(quickscan_data, colWidths=[6*inch])
        quickscan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["primary"])),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(self.COLORS["primary"])),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        self.elements.append(quickscan_table)
        self.elements.append(Spacer(1, 0.2*inch))
    
    def _add_roi_section(self):
        """Add ROI and revenue impact section to executive summary."""
        roi_data = self.data.get("roi_projection", {})
        if not roi_data:
            return
        
        self.elements.append(Spacer(1, 0.15*inch))
        self.elements.append(Paragraph("<b>Revenue Impact &amp; ROI Analysis</b>", self.styles['SubSection']))
        
        current = roi_data.get("current_state", {})
        projected = roi_data.get("projected_improvement", {})
        roi = roi_data.get("roi_analysis", {})
        inaction = roi_data.get("cost_of_inaction", {})
        
        if current.get("monthly_lost_revenue"):
            current_text = f"""<b>Current Impact:</b> Your visibility gap is costing an estimated <font color="#dc2626"><b>{current['monthly_lost_revenue']}</b></font> in missed revenue each month ({current.get('monthly_missed_leads', 0)} missed leads)."""
            self.elements.append(Paragraph(current_text, self.styles['CustomBodyText']))
        
        if projected.get("monthly_revenue_gain"):
            proj_text = f"""<b>Projected Improvement:</b> By improving from {current.get('visibility_score', 0)} to {projected.get('visibility_score', 0)}, we project a <font color="#16a34a"><b>{projected.get('lead_increase_pct', 0)}% increase</b></font> in qualified leads, translating to <font color="#16a34a"><b>{projected['monthly_revenue_gain']}</b></font> in additional monthly revenue."""
            self.elements.append(Paragraph(proj_text, self.styles['CustomBodyText']))
        
        if inaction.get("six_month_cost"):
            inaction_text = f"""<b>Cost of Inaction:</b> Every month of delay costs {inaction.get('monthly_opportunity_cost', 'significant revenue')}. Over six months, this compounds to <font color="#dc2626"><b>{inaction['six_month_cost']}</b></font> in unrealized revenue."""
            self.elements.append(Paragraph(inaction_text, self.styles['CustomBodyText']))
        
        if roi.get("estimated_roi"):
            roi_text = f"""<b>Investment ROI:</b> A typical engagement ({roi.get('engagement_cost_range', '$5,000-$15,000')}) delivers an estimated <font color="#16a34a"><b>{roi['estimated_roi']} return</b></font> within the first year, with payback typically achieved within {roi.get('payback_period_months', 3)} months."""
            self.elements.append(Paragraph(roi_text, self.styles['CustomBodyText']))
    
    def _add_market_position_section(self):
        """Add market position analysis section - premium feature."""
        market_intel = self.data.get("market_intelligence", {})
        if not market_intel:
            return
        
        classification = market_intel.get("classification", {})
        benchmark = market_intel.get("benchmark", {})
        landscape = market_intel.get("market_landscape", {})
        
        self.elements.append(Paragraph("3. Market Position Analysis", self.styles['SectionTitle']))
        self.elements.append(Spacer(1, 0.1*inch))
        
        # Industry classification
        niche = classification.get("niche", "Unknown")
        sub_niche = classification.get("sub_niche", "")
        industry = classification.get("industry", "Unknown")
        vertical = classification.get("vertical", "Unknown")
        
        classification_text = f"""<b>Industry Classification:</b> {industry} &gt; {vertical} &gt; {niche}"""
        if sub_niche:
            classification_text += f"<br/><b>Sub-niche:</b> {sub_niche}"
        
        self.elements.append(Paragraph(classification_text, self.styles['CustomBodyText']))
        self.elements.append(Spacer(1, 0.15*inch))
        
        # Market position summary
        rank = benchmark.get("market_position_rank", 0)
        percentile = benchmark.get("market_position_percentile", 0)
        total_competitors = len(market_intel.get("competitors", [])) + 1
        
        position_color = self.COLORS["grade_a"] if rank <= 2 else self.COLORS["grade_c"] if rank <= 4 else self.COLORS["grade_f"]
        
        position_text = f"""<font color="{position_color}"><b>Market Position: #{rank} of {total_competitors} analyzed</b></font>
        <br/>Percentile: {percentile}th (higher is better)"""
        self.elements.append(Paragraph(position_text, self.styles['SubSection']))
        self.elements.append(Spacer(1, 0.15*inch))
        
        # Vs market average table
        vs_avg = benchmark.get("vs_market_average", {})
        if vs_avg:
            data = [["Metric", "Your Score", "vs Market Avg", "Status"]]
            
            overall = self.data.get("overall_score", 0) or 0
            tech = self.data.get("audits", {}).get("technical", {}).get("score", 0) or 0
            content = self.data.get("audits", {}).get("content", {}).get("score", 0) or 0
            ai = self.data.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0
            
            metrics = [
                ("Overall Score", overall, vs_avg.get("overall", 0)),
                ("Technical SEO", tech, vs_avg.get("technical", 0)),
                ("Content & Authority", content, vs_avg.get("content", 0)),
                ("AI Visibility", ai, vs_avg.get("ai_visibility", 0)),
            ]
            
            for name, score, diff in metrics:
                diff_str = f"+{diff}" if diff >= 0 else str(diff)
                status = "Above Avg" if diff > 0 else "At Avg" if diff == 0 else "Below Avg"
                data.append([name, str(score), diff_str, status])
            
            table = Table(data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["primary"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            self.elements.append(table)
        
        self.elements.append(Spacer(1, 0.2*inch))
        
        # Competitive advantages and gaps
        advantages = benchmark.get("competitive_advantages", [])
        gaps = benchmark.get("critical_gaps", [])
        
        if advantages:
            self.elements.append(Paragraph("<b>Competitive Advantages:</b>", self.styles['SubSection']))
            for adv in advantages[:3]:
                self.elements.append(Paragraph(f"+ {adv}", self.styles['Finding']))
        
        if gaps:
            self.elements.append(Spacer(1, 0.1*inch))
            self.elements.append(Paragraph("<b>Critical Gaps:</b>", self.styles['SubSection']))
            for gap in gaps[:3]:
                self.elements.append(Paragraph(f"- {gap}", self.styles['Finding']))
        
        # AI Visibility opportunity
        ai_opportunity = landscape.get("ai_visibility_opportunity", "")
        if ai_opportunity:
            self.elements.append(Spacer(1, 0.15*inch))
            self.elements.append(Paragraph(f"<b>AI Visibility Opportunity:</b> {ai_opportunity}", self.styles['CustomBodyText']))
        
        self.elements.append(PageBreak())
    
    def _add_competitor_benchmarking_section(self):
        """Add competitor benchmarking section - premium feature."""
        market_intel = self.data.get("market_intelligence", {})
        if not market_intel:
            return
        
        competitors = market_intel.get("competitors", [])
        benchmarks = market_intel.get("competitor_benchmarks", [])
        
        if not competitors:
            return
        
        self.elements.append(Paragraph("4. Competitor Benchmarking", self.styles['SectionTitle']))
        self.elements.append(Spacer(1, 0.1*inch))
        
        intro = f"""We identified and analyzed {len(competitors)} competitors in your niche. 
        This side-by-side comparison shows where you stand and what you need to do to gain market share."""
        self.elements.append(Paragraph(intro, self.styles['CustomBodyText']))
        self.elements.append(Spacer(1, 0.15*inch))
        
        # Competitor overview table
        self.elements.append(Paragraph("<b>Competitor Landscape:</b>", self.styles['SubSection']))
        
        data = [["Competitor", "Strength", "Geographic", "Why They Compete"]]
        for comp in competitors[:6]:
            data.append([
                comp.get("name", "Unknown")[:25],
                comp.get("estimated_strength", "").title(),
                comp.get("geographic_overlap", "").title(),
                comp.get("why_competitor", "")[:40] + "..." if len(comp.get("why_competitor", "")) > 40 else comp.get("why_competitor", "")
            ])
        
        table = Table(data, colWidths=[1.5*inch, 1*inch, 1*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (2, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.2*inch))
        
        # Score comparison chart
        if benchmarks:
            self._create_competitor_comparison_chart(benchmarks)
        
        # Detailed benchmarks for top competitors
        self.elements.append(Paragraph("<b>Head-to-Head Analysis:</b>", self.styles['SubSection']))
        self.elements.append(Spacer(1, 0.1*inch))
        
        for benchmark in benchmarks[:3]:
            comp_name = benchmark.get("competitor_name", "Competitor")
            overall_diff = benchmark.get("overall_score_diff", 0)
            
            # Status indicator
            if overall_diff > 0:
                status = f"<font color='{self.COLORS['grade_a']}'>You lead by {overall_diff} points</font>"
            elif overall_diff < 0:
                status = f"<font color='{self.COLORS['grade_f']}'>Behind by {abs(overall_diff)} points</font>"
            else:
                status = "Tied"
            
            self.elements.append(Paragraph(f"<b>vs {comp_name}:</b> {status}", self.styles['Finding']))
            
            # Quick wins
            quick_wins = benchmark.get("quick_wins", [])
            if quick_wins:
                for win in quick_wins[:2]:
                    self.elements.append(Paragraph(f"  - Quick win: {win}", self.styles['BulletItem']))
            
            self.elements.append(Spacer(1, 0.08*inch))
        
        self.elements.append(PageBreak())
    
    def _create_competitor_comparison_chart(self, benchmarks: list):
        """Create a bar chart comparing scores against competitors."""
        if not benchmarks:
            return
        
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Prepare data
        labels = [self.company_name[:15]]
        overall_scores = [self.data.get("overall_score", 0) or 0]
        ai_scores = [self.data.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0]
        
        for b in benchmarks[:4]:
            labels.append(b.get("competitor_name", "Comp")[:15])
            # Calculate competitor scores from differences
            overall_scores.append((self.data.get("overall_score", 0) or 0) - b.get("overall_score_diff", 0))
            ai_scores.append((self.data.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0) - b.get("ai_visibility_score_diff", 0))
        
        x = np.arange(len(labels))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(7, 3))
        bars1 = ax.bar(x - width/2, overall_scores, width, label='Overall Score', color=self.COLORS["primary"])
        bars2 = ax.bar(x + width/2, ai_scores, width, label='AI Visibility', color='#7c3aed')
        
        ax.set_ylabel('Score')
        ax.set_title('Competitive Score Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=15, ha='right', fontsize=8)
        ax.legend(loc='upper right', fontsize=8)
        ax.set_ylim(0, 100)
        ax.axhline(y=70, color='gray', linestyle='--', alpha=0.5, linewidth=1)
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width()/2, height),
                       xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=7)
        
        plt.tight_layout()
        chart_path = str(self.charts_dir / "competitor_comparison.png")
        plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        if os.path.exists(chart_path):
            img = Image(chart_path, width=6.5*inch, height=2.8*inch)
            img.hAlign = 'CENTER'
            self.elements.append(img)
            self.elements.append(Spacer(1, 0.15*inch))
    
    def _add_technical_section(self):
        """Add technical audit section."""
        tech = self.data.get("audits", {}).get("technical", {})
        if not tech:
            return
            
        score = tech.get("score", 0) or 0
        self.elements.append(Paragraph("3. Technical SEO Analysis", self.styles['SectionTitle']))
        
        # Score with visual indicator
        score_color = self._get_score_color(score)
        status = "Good" if score >= 70 else "Needs Improvement" if score >= 50 else "Critical"
        score_text = f'<font color="{score_color}"><b>Score: {score}/100</b></font> — {status}'
        self.elements.append(Paragraph(score_text, self.styles['SubSection']))
        self.elements.append(Spacer(1, 0.1*inch))
        
        # Intro text
        intro = "Technical SEO forms the foundation of your website's search visibility. This section analyzes crawlability, page speed, security, mobile optimization, and structured data implementation."
        self.elements.append(Paragraph(intro, self.styles['CustomBodyText']))
        self.elements.append(Spacer(1, 0.15*inch))
        
        # Components table
        components = tech.get("components", {})
        if components:
            data = [["Component", "Score", "Max", "Status"]]
            for name, comp_data in components.items():
                if isinstance(comp_data, dict):
                    comp_score = comp_data.get("score", 0) or 0
                    max_score = comp_data.get("max", 100) or 100
                    pct = comp_score / max_score * 100 if max_score > 0 else 0
                    status = "✓ Good" if pct >= 80 else "⚠ Needs Work" if pct >= 50 else "✗ Poor"
                    data.append([
                        name.replace("_", " ").title(),
                        str(comp_score),
                        str(max_score),
                        status
                    ])
            
            table = Table(data, colWidths=[2.2*inch, 0.8*inch, 0.8*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["primary"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            self.elements.append(table)
        
        # Key findings
        self.elements.append(Spacer(1, 0.15*inch))
        self.elements.append(Paragraph("Key Findings:", self.styles['SubSection']))
        
        findings = []
        for comp_name, comp_data in components.items():
            if isinstance(comp_data, dict):
                for finding in comp_data.get("findings", [])[:2]:
                    findings.append(f"• {finding}")
        
        for finding in findings[:6]:
            self.elements.append(Paragraph(finding, self.styles['Finding']))
        
        self.elements.append(PageBreak())
    
    def _add_content_section(self):
        """Add content audit section."""
        content = self.data.get("audits", {}).get("content", {})
        if not content:
            return
            
        score = content.get("score", 0) or 0
        self.elements.append(Paragraph("4. Content & Authority Analysis", self.styles['SectionTitle']))
        
        # Score with status
        score_color = self._get_score_color(score)
        status = "Good" if score >= 70 else "Needs Improvement" if score >= 50 else "Critical"
        score_text = f'<font color="{score_color}"><b>Score: {score}/100</b></font> — {status}'
        self.elements.append(Paragraph(score_text, self.styles['SubSection']))
        self.elements.append(Spacer(1, 0.1*inch))
        
        # Intro
        intro = "Content quality and authority signals are critical for search rankings. This section evaluates your content depth, E-E-A-T signals (Experience, Expertise, Authoritativeness, Trust), topical coverage, and link profile."
        self.elements.append(Paragraph(intro, self.styles['CustomBodyText']))
        self.elements.append(Spacer(1, 0.15*inch))
        
        # Components table
        components = content.get("components", {})
        if components:
            data = [["Component", "Score", "Max", "Status"]]
            for name, comp_data in components.items():
                if isinstance(comp_data, dict):
                    comp_score = comp_data.get("score", 0) or 0
                    max_score = comp_data.get("max", 100) or 100
                    pct = comp_score / max_score * 100 if max_score > 0 else 0
                    status = "✓ Good" if pct >= 80 else "⚠ Needs Work" if pct >= 50 else "✗ Poor"
                    data.append([
                        name.replace("_", " ").title(),
                        str(comp_score),
                        str(max_score),
                        status
                    ])
            
            table = Table(data, colWidths=[2.2*inch, 0.8*inch, 0.8*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["secondary"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            self.elements.append(table)
        
        # Findings
        self.elements.append(Spacer(1, 0.15*inch))
        self.elements.append(Paragraph("<b>Key Findings:</b>", self.styles['SubSection']))
        
        findings = []
        for comp_name, comp_data in components.items():
            if isinstance(comp_data, dict):
                for finding in comp_data.get("findings", [])[:2]:
                    findings.append(f"• {finding}")
        
        for finding in findings[:6]:
            self.elements.append(Paragraph(finding, self.styles['Finding']))
        
        self.elements.append(PageBreak())
    
    def _add_ai_visibility_section(self):
        """Add AI visibility section - the differentiator."""
        ai = self.data.get("audits", {}).get("ai_visibility", {})
        if not ai:
            return
            
        score = ai.get("score", 0) or 0
        self.elements.append(Paragraph("AI Visibility Analysis", self.styles['SectionTitle']))
        
        # Score with status
        score_color = self._get_score_color(score)
        status = "Good" if score >= 70 else "Needs Improvement" if score >= 50 else "Critical"
        score_text = f'<font color="{score_color}"><b>Score: {score}/100</b></font> — {status}'
        self.elements.append(Paragraph(score_text, self.styles['SubSection']))
        self.elements.append(Spacer(1, 0.1*inch))
        
        # Highlight - this is unique
        highlight = """<b>Why This Matters:</b> AI-powered search (ChatGPT, Claude, Perplexity, Google AI Overviews) is rapidly changing how customers find businesses. This analysis evaluates how your brand appears in AI-generated responses — a critical competitive advantage that most SEO agencies don't measure."""
        self.elements.append(Paragraph(highlight, self.styles['CustomBodyText']))
        self.elements.append(Spacer(1, 0.15*inch))
        self.elements.append(Paragraph(score_text, self.styles['SubSection']))
        
        # Components
        components = ai.get("components", {})
        if components:
            data = [["Component", "Score", "Max", "Status"]]
            for name, comp_data in components.items():
                if isinstance(comp_data, dict):
                    comp_score = comp_data.get("score", 0) or 0
                    max_score = comp_data.get("max", 100) or 100
                    pct = comp_score / max_score * 100 if max_score > 0 else 0
                    status = "✓ Good" if pct >= 80 else "⚠ Needs Work" if pct >= 50 else "✗ Poor"
                    data.append([
                        name.replace("_", " ").title(),
                        str(comp_score),
                        str(max_score),
                        status
                    ])
            
            table = Table(data, colWidths=[2.2*inch, 0.8*inch, 0.8*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#7c3aed")),  # Purple for AI
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            self.elements.append(table)
        
        # Findings
        self.elements.append(Spacer(1, 0.15*inch))
        self.elements.append(Paragraph("<b>Key Findings:</b>", self.styles['SubSection']))
        
        findings = []
        for comp_name, comp_data in components.items():
            if isinstance(comp_data, dict):
                for finding in comp_data.get("findings", [])[:2]:
                    findings.append(f"• {finding}")
        
        for finding in findings[:6]:
            self.elements.append(Paragraph(finding, self.styles['Finding']))
        
        self.elements.append(PageBreak())
    
    def _add_recommendations(self):
        """Add prioritized recommendations."""
        self.elements.append(Paragraph("Prioritized Action Plan", self.styles['SectionTitle']))
        
        intro = """The following recommendations are prioritized by potential impact and implementation effort. Focus on HIGH priority items first for maximum return on investment."""
        self.elements.append(Paragraph(intro, self.styles['CustomBodyText']))
        self.elements.append(Spacer(1, 0.15*inch))
        
        # Collect all recommendations
        all_recs = []
        for audit_name, audit_data in self.data.get("audits", {}).items():
            if audit_data and "recommendations" in audit_data:
                for rec in audit_data["recommendations"]:
                    rec["source"] = audit_name
                    all_recs.append(rec)
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2, "quick_win": 1}
        all_recs.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 99))
        
        # High priority section
        high_recs = [r for r in all_recs if r.get("priority") == "high"]
        if high_recs:
            self.elements.append(Paragraph("<font color='#dc2626'><b>HIGH PRIORITY</b></font>", self.styles['SubSection']))
            for i, rec in enumerate(high_recs[:5], 1):
                action = rec.get("action", "")
                details = rec.get("details", "")
                source = rec.get("source", "").replace("_", " ").title()
                text = f"<b>{i}. {action}</b><br/><font size=8 color='#666'>{details}</font>"
                self.elements.append(Paragraph(text, self.styles['Finding']))
            self.elements.append(Spacer(1, 0.15*inch))
        
        # Medium priority section
        med_recs = [r for r in all_recs if r.get("priority") in ["medium", "quick_win"]]
        if med_recs:
            self.elements.append(Paragraph("<font color='#d97706'><b>MEDIUM PRIORITY</b></font>", self.styles['SubSection']))
            for i, rec in enumerate(med_recs[:5], 1):
                action = rec.get("action", "")
                details = rec.get("details", "")
                text = f"<b>{i}. {action}</b><br/><font size=8 color='#666'>{details}</font>"
                self.elements.append(Paragraph(f"• {text}", self.styles['Finding']))
        
        # === NEW: Next Steps / Call to Action Section ===
        self._add_next_steps_section()
        
        self.elements.append(PageBreak())
    
    def _add_next_steps_section(self):
        """Add next steps and call to action to close the sale."""
        self.elements.append(Spacer(1, 0.25*inch))
        
        # Create a highlighted box for next steps
        next_steps_title = Paragraph(
            "<b>RECOMMENDED NEXT STEPS</b>",
            ParagraphStyle('NextStepsTitle', fontSize=12, textColor=colors.white, alignment=TA_CENTER)
        )
        
        # Get ROI data for the CTA
        roi_data = self.data.get("roi_projection", {})
        roi_analysis = roi_data.get("roi_analysis", {})
        inaction = roi_data.get("cost_of_inaction", {})
        
        # Build next steps content
        steps_content = """
        <b>1. Schedule Strategy Call</b> — Review findings and discuss priorities with our team<br/><br/>
        <b>2. Approve Engagement Plan</b> — We recommend a 4-6 month SEO acceleration program covering:<br/>
        &nbsp;&nbsp;&nbsp;• Technical SEO fixes and site optimization<br/>
        &nbsp;&nbsp;&nbsp;• Content strategy and authority building<br/>
        &nbsp;&nbsp;&nbsp;• AI visibility optimization (our differentiator)<br/><br/>
        <b>3. Begin Implementation</b> — Quick wins in 30 days, measurable results in 90 days
        """
        
        steps_para = Paragraph(steps_content, ParagraphStyle('NextStepsContent', fontSize=9, leading=13))
        
        # Urgency statement
        if inaction.get("monthly_opportunity_cost"):
            urgency = f"<i>Every month of delay costs {inaction['monthly_opportunity_cost']} in missed opportunities.</i>"
        else:
            urgency = "<i>The window for AI visibility advantage is closing — competitors who move first will establish lasting market position.</i>"
        
        urgency_para = Paragraph(urgency, ParagraphStyle('Urgency', fontSize=9, textColor=colors.HexColor("#dc2626"), alignment=TA_CENTER))
        
        # Contact info
        contact = """
        <b>Ready to get started?</b><br/>
        Contact: info@raaptech.com | www.raaptech.com
        """
        contact_para = Paragraph(contact, ParagraphStyle('Contact', fontSize=9, alignment=TA_CENTER))
        
        # Build the table
        next_steps_data = [
            [next_steps_title],
            [steps_para],
            [urgency_para],
            [contact_para],
        ]
        
        next_steps_table = Table(next_steps_data, colWidths=[6*inch])
        next_steps_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["primary"])),
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#f0fdf4")),  # Light green
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f8f9fa")),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor(self.COLORS["primary"])),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        self.elements.append(next_steps_table)
    
    def _add_appendix(self):
        """Add appendix with methodology."""
        self.elements.append(Paragraph("7. Appendix", self.styles['SectionTitle']))
        
        methodology = """
        <b>Scoring Methodology</b><br/><br/>
        
        The overall SEO Health Score is calculated using a weighted average of three components:<br/><br/>
        
        • <b>Technical SEO (30%)</b> - Crawlability, page speed, security, mobile optimization, structured data<br/>
        • <b>Content & Authority (35%)</b> - Content quality, E-E-A-T signals, topical authority, backlinks<br/>
        • <b>AI Visibility (35%)</b> - Brand presence in AI responses, parseability, knowledge graph, citation likelihood<br/><br/>
        
        <b>Grade Scale</b><br/><br/>
        
        • A (90-100): Excellent - Industry leader<br/>
        • B (80-89): Good - Above average performance<br/>
        • C (70-79): Average - Room for improvement<br/>
        • D (60-69): Below Average - Significant gaps<br/>
        • F (0-59): Poor - Urgent attention needed<br/><br/>
        
        <b>Data Sources</b><br/><br/>
        
        • Live website crawling and analysis<br/>
        • Google PageSpeed Insights API<br/>
        • AI system queries (Claude, ChatGPT, Perplexity)<br/>
        • Knowledge graph verification<br/>
        • Structured data validation
        """
        
        self.elements.append(Paragraph(methodology, self.styles['CustomBodyText']))
    
    def generate(self) -> str:
        """Generate the PDF report."""
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )
        
        # Build report sections
        self._add_cover_page()
        self._add_table_of_contents()
        self._add_executive_summary()
        self._add_methodology_section()
        
        # Add market intelligence sections if available (premium feature)
        if "market_intelligence" in self.data:
            self._add_market_position_section()
            self._add_competitor_benchmarking_section()
        
        self._add_technical_section()
        self._add_content_section()
        self._add_ai_visibility_section()
        self._add_recommendations()
        self._add_appendix()
        
        # Build PDF
        doc.build(self.elements)
        
        return self.output_path


def generate_premium_report(json_path: str, output_path: str = None) -> str:
    """Generate premium PDF report from JSON audit data."""
    with open(json_path) as f:
        data = json.load(f)
    
    if output_path is None:
        output_path = json_path.replace(".json", "_PREMIUM.pdf")
    
    generator = PremiumReportGenerator(data, output_path)
    result = generator.generate()
    
    print(f"✅ Premium PDF report generated: {result}")
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_premium_report.py <json_file> [output_file]")
        sys.exit(1)
    
    json_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    generate_premium_report(json_path, output_path)
