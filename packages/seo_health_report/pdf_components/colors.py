"""Premium Report Color Systems - Centralized color definitions."""
from reportlab.lib import colors


class ReportColors:
    """Pre-defined colors for consistent report styling."""
    # Neutrals
    text_primary = colors.HexColor("#1F2937")
    text_secondary = colors.HexColor("#4B5563")
    text_muted = colors.HexColor("#6B7280")
    border = colors.HexColor("#E5E7EB")
    background = colors.HexColor("#F9FAFB")
    white = colors.HexColor("#FFFFFF")

    # Severity
    critical = colors.HexColor("#DC2626")
    high = colors.HexColor("#EA580C")
    medium = colors.HexColor("#D97706")
    low = colors.HexColor("#65A30D")

    # Status
    success = colors.HexColor("#10B981")
    warning = colors.HexColor("#F59E0B")
    info = colors.HexColor("#3B82F6")
    danger = colors.HexColor("#EF4444")

    # Chart palette (sequential, 8 colors max)
    CHART_PALETTE = [
        "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
        "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16",
    ]

    @classmethod
    def grade(cls, grade: str) -> colors.Color:
        """Get color for grade A/B/C/D/F."""
        grades = {
            "A": "#10B981", "B": "#3B82F6", "C": "#F59E0B",
            "D": "#EA580C", "F": "#DC2626"
        }
        return colors.HexColor(grades.get(grade.upper(), "#6B7280"))

    @classmethod
    def score_color(cls, score: int) -> colors.Color:
        """Get color based on score 0-100."""
        if score >= 90: return cls.grade("A")
        if score >= 80: return cls.grade("B")
        if score >= 70: return cls.grade("C")
        if score >= 60: return cls.grade("D")
        return cls.grade("F")
