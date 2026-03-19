"""
Setup Basic Assets

Generates formatted placeholder assets for report profiles.
This allows the system to run without needing live AI image generation for every report.
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageColor
from pathlib import Path

# Configuration
ASSET_DIR = Path("assets")
BANNERS_DIR = ASSET_DIR / "banners" / "industry"
BADGES_DIR = ASSET_DIR / "score_badges" / "templates"

# Brand Colors (RaapTech / Premium)
COLORS = {
    "manufacturing": ["#1a365d", "#2a4365"],  # Navy/Steel
    "professional_services": ["#2c5282", "#2b6cb0"],  # Trust Blue
    "healthcare": ["#276749", "#2f855a"],  # Medical Green
    "technology": ["#44337a", "#553c9a"],  # Tech Purple
    "general": ["#2d3748", "#4a5568"],  # Neutral Gray
    
    # Utilities
    "overlay_text": "#ffffff",
    "badge_bg": "#ffffff",
    "badge_border": "#e2e8f0"
}

def create_gradient_banner(name: str, colors: list[str], width=1200, height=300):
    """Create a professional gradient banner."""
    base = Image.new('RGB', (width, height), colors[0])
    top = Image.new('RGB', (width, height), colors[1])
    mask = Image.new('L', (width, height))
    mask_data = []
    
    for y in range(height):
        # Linear gradient
        mask_data.extend([int(255 * (y / height))] * width)
        
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    
    # Save
    path = BANNERS_DIR / f"{name}.png"
    base.save(path)
    print(f"✅ Generated banner: {path}")

def create_badge_template(score_range: str, color_hex: str, width=500, height=500):
    """Create a clean score badge template for dynamic scoring."""
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Circular gauge background
    padding = 20
    bbox = (padding, padding, width-padding, height-padding)
    
    # Outer ring
    draw.arc(bbox, start=0, end=360, fill="#e2e8f0", width=40)
    
    # Active arc (placeholder - effectively full for the template, 
    # but practically we would draw this consistently or leave it blank for overlay)
    # For a template, we just want the branded container. 
    # Actually, let's make a base template that the code will draw the score ON TOP of.
    
    # Inner circle
    inner_bbox = (padding+40, padding+40, width-padding-40, height-padding-40)
    # draw.ellipse(inner_bbox, fill="#ffffff", outline=None)
    
    # Save
    path = BADGES_DIR / f"template_{score_range}.png"
    img.save(path)
    print(f"✅ Generated badge template: {path}")

def main():
    # Ensure directories exist
    os.makedirs(BANNERS_DIR, exist_ok=True)
    os.makedirs(BADGES_DIR, exist_ok=True)
    
    print("🎨 Generating Industry Banners...")
    create_gradient_banner("manufacturing", COLORS["manufacturing"])
    create_gradient_banner("professional_services", COLORS["professional_services"])
    create_gradient_banner("healthcare", COLORS["healthcare"])
    create_gradient_banner("technology", COLORS["technology"])
    create_gradient_banner("default", COLORS["general"])
    
    print("\n🏆 Generating Badge Templates...")
    # These are just base assets; the report generator will overlay dynamic scores
    create_badge_template("excellent", "#38a169") # Green
    create_badge_template("good", "#3182ce")      # Blue
    create_badge_template("average", "#d69e2e")   # Yellow
    create_badge_template("poor", "#e53e3e")      # Red
    
    print("\n✨ Assets setup complete!")

if __name__ == "__main__":
    main()
