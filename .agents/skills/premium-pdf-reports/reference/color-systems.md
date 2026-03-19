# Premium Report Color Systems

## Neutral Palette (Primary)
Use these for text, backgrounds, and borders.

```python
NEUTRALS = {
    "text_primary": "#1F2937",    # Gray 800 - headings, emphasis
    "text_secondary": "#4B5563",  # Gray 600 - body text
    "text_muted": "#6B7280",      # Gray 500 - captions, metadata
    "border": "#E5E7EB",          # Gray 200 - lines, dividers
    "background": "#F9FAFB",      # Gray 50 - card backgrounds
    "white": "#FFFFFF",
}
```

## Semantic Colors
Use these sparingly for meaning, not decoration.

```python
SEMANTIC = {
    # Severity
    "critical": "#DC2626",  # Red 600
    "high": "#EA580C",      # Orange 600
    "medium": "#D97706",    # Amber 600
    "low": "#65A30D",       # Lime 600
    
    # Status
    "success": "#10B981",   # Emerald 500
    "warning": "#F59E0B",   # Amber 500
    "info": "#3B82F6",      # Blue 500
    "danger": "#EF4444",    # Red 500
}
```

## Grade Colors
For A/B/C/D/F scoring display.

```python
GRADES = {
    "A": "#10B981",  # Emerald - excellent
    "B": "#3B82F6",  # Blue - good
    "C": "#F59E0B",  # Amber - average
    "D": "#EA580C",  # Orange - below average
    "F": "#DC2626",  # Red - failing
}
```

## Chart Color Palette
Sequential palette for charts (8 colors max).

```python
CHART_PALETTE = [
    "#3B82F6",  # Blue 500 - primary
    "#10B981",  # Emerald 500
    "#F59E0B",  # Amber 500
    "#EF4444",  # Red 500
    "#8B5CF6",  # Violet 500
    "#EC4899",  # Pink 500
    "#06B6D4",  # Cyan 500
    "#84CC16",  # Lime 500
]
```

## Usage Rules

1. **Text**: Always use neutral palette
2. **Severity indicators**: Use semantic colors only for badges/pills
3. **Backgrounds**: White or Gray 50 only
4. **Borders**: Gray 200 (subtle) or brand color (emphasis)
5. **Charts**: Use CHART_PALETTE sequentially
6. **Never**: Use more than 3 colors in a single component

## ReportLab Implementation

```python
from reportlab.lib import colors

def hex_to_color(hex_str):
    """Convert hex to ReportLab color."""
    return colors.HexColor(hex_str)

# Pre-defined colors for easy use
class ReportColors:
    text_primary = colors.HexColor("#1F2937")
    text_secondary = colors.HexColor("#4B5563")
    text_muted = colors.HexColor("#6B7280")
    border = colors.HexColor("#E5E7EB")
    background = colors.HexColor("#F9FAFB")
    
    critical = colors.HexColor("#DC2626")
    high = colors.HexColor("#EA580C")
    medium = colors.HexColor("#D97706")
    low = colors.HexColor("#65A30D")
    
    success = colors.HexColor("#10B981")
    warning = colors.HexColor("#F59E0B")
    info = colors.HexColor("#3B82F6")
    danger = colors.HexColor("#EF4444")
    
    @classmethod
    def grade(cls, grade: str):
        grades = {"A": "#10B981", "B": "#3B82F6", "C": "#F59E0B", "D": "#EA580C", "F": "#DC2626"}
        return colors.HexColor(grades.get(grade, "#6B7280"))
```
