"""
Chart generation module for SEO Health Reports.

Provides consistent matplotlib styling and chart functions.
NO emojis - B2B professional output only.
"""

import matplotlib

matplotlib.use('Agg')  # Non-interactive backend

import matplotlib.pyplot as plt
import numpy as np

# Chart color palette (from color-systems.md)
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

# Grade colors
GRADE_COLORS = {
    "A": "#10B981",
    "B": "#3B82F6",
    "C": "#F59E0B",
    "D": "#EA580C",
    "F": "#DC2626",
}


def setup_chart_style():
    """Apply consistent chart styling for all charts."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.color': '#E5E7EB',
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
    })


def save_chart(fig, path: str, dpi: int = 200):
    """Save chart with consistent settings.

    Args:
        fig: Matplotlib figure
        path: Output path
        dpi: Resolution (default 200 for print quality)
    """
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)


def get_score_color(score: int) -> str:
    """Get color based on score 0-100."""
    if score >= 90: return GRADE_COLORS["A"]
    if score >= 80: return GRADE_COLORS["B"]
    if score >= 70: return GRADE_COLORS["C"]
    if score >= 60: return GRADE_COLORS["D"]
    return GRADE_COLORS["F"]


def create_score_gauge(
    score: int,
    grade: str,
    company_name: str,
    output_path: str
) -> str:
    """Create semi-circle score gauge chart.

    Args:
        score: Overall score 0-100
        grade: Letter grade A-F
        company_name: Company name for title
        output_path: Path to save chart

    Returns:
        Path to saved chart
    """
    setup_chart_style()

    fig, ax = plt.subplots(figsize=(5, 3.5))

    # Background arc segments (gray zones for context)
    zones = [(0, 0.6, 0.15), (0.6, 0.7, 0.1), (0.7, 0.8, 0.08), (0.8, 1.0, 0.05)]
    for start, end, alpha in zones:
        segment_theta = np.linspace(start * np.pi, end * np.pi, 20)
        ax.fill_between(segment_theta, 0.6, 1, alpha=alpha, color='gray')

    # Score arc (filled portion)
    score_theta = np.linspace(0, np.pi * score / 100, 100)
    color = get_score_color(score)
    ax.fill_between(score_theta, 0.6, 1, alpha=0.9, color=color)

    # Inner circle (white center)
    inner_circle = plt.Circle((0, 0), 0.55, color='white', zorder=5)
    ax.add_patch(inner_circle)

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.3, 1.2)
    ax.set_aspect('equal')
    ax.axis('off')

    # Score text (large, centered)
    ax.text(0, 0.25, f"{score}", fontsize=42, ha='center', va='center',
            fontweight='bold', color=color, zorder=10)
    ax.text(0, -0.05, f"Grade: {grade}", fontsize=16, ha='center', va='center',
            color='#1F2937', fontweight='bold', zorder=10)

    # Company name at top
    ax.text(0, 1.1, company_name, fontsize=11, ha='center', va='center',
            color=CHART_PALETTE[0], fontweight='bold')

    save_chart(fig, output_path)
    return output_path


def create_component_bars(
    tech_score: int,
    content_score: int,
    ai_score: int,
    output_path: str
) -> str:
    """Create horizontal bar chart for component scores.

    Args:
        tech_score: Technical SEO score
        content_score: Content & Authority score
        ai_score: AI Visibility score
        output_path: Path to save chart

    Returns:
        Path to saved chart
    """
    setup_chart_style()

    fig, ax = plt.subplots(figsize=(6.5, 2.2))

    components = ['Technical SEO (30%)', 'Content & Authority (35%)', 'AI Visibility (35%)']
    scores = [tech_score, content_score, ai_score]
    colors_list = [get_score_color(s) for s in scores]

    y_pos = np.arange(len(components))

    # Background bars (to 100)
    ax.barh(y_pos, [100]*3, color='#f0f0f0', height=0.5, zorder=0)

    # Score bars
    bars = ax.barh(y_pos, scores, color=colors_list, height=0.5, edgecolor='white', linewidth=1)

    # Score labels
    for i, (_bar, score) in enumerate(zip(bars, scores)):
        label_x = max(score - 8, 5) if score > 20 else score + 3
        label_color = 'white' if score > 20 else '#1F2937'
        ha = 'center' if score > 20 else 'left'
        ax.text(label_x, i, f'{score}', va='center', ha=ha,
                fontsize=11, fontweight='bold', color=label_color, zorder=10)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(components, fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis='x', labelsize=8)
    ax.spines['left'].set_visible(False)

    # Target line
    ax.axvline(x=70, color='#666', linestyle='--', alpha=0.7, linewidth=1)
    ax.text(71, 2.3, 'Target: 70', fontsize=7, color='#666')

    save_chart(fig, output_path)
    return output_path


def create_ranked_bar_chart(
    categories: list[str],
    scores: list[int],
    max_scores: list[int],
    title: str,
    output_path: str,
    primary_color: str = None
) -> str:
    """Create a ranked bar chart (replacement for radar chart).

    Args:
        categories: List of category names
        scores: List of scores
        max_scores: List of max possible scores
        title: Chart title
        output_path: Path to save chart
        primary_color: Optional primary color (uses palette[0] by default)

    Returns:
        Path to saved chart
    """
    setup_chart_style()

    color = primary_color or CHART_PALETTE[0]

    # Normalize scores to percentages
    percentages = [s/m*100 if m > 0 else 0 for s, m in zip(scores, max_scores)]

    # Sort by score descending
    sorted_data = sorted(zip(categories, percentages, scores, max_scores),
                        key=lambda x: x[1], reverse=True)

    fig, ax = plt.subplots(figsize=(6, max(3, len(categories) * 0.5)))

    y_pos = np.arange(len(sorted_data))
    cats = [d[0] for d in sorted_data]
    pcts = [d[1] for d in sorted_data]

    # Background bars
    ax.barh(y_pos, [100]*len(cats), color='#f0f0f0', height=0.6, zorder=0)

    # Score bars
    bars = ax.barh(y_pos, pcts, color=color, height=0.6, alpha=0.8)

    # Labels
    for i, (_bar, pct) in enumerate(zip(bars, pcts)):
        score, max_s = sorted_data[i][2], sorted_data[i][3]
        label = f'{int(pct)}% ({score}/{max_s})'
        label_x = pct + 2 if pct < 80 else pct - 5
        label_color = '#1F2937' if pct < 80 else 'white'
        ha = 'left' if pct < 80 else 'right'
        ax.text(label_x, i, label, va='center', ha=ha, fontsize=8, color=label_color)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(cats, fontsize=9)
    ax.set_xlim(0, 110)
    ax.set_title(title, fontsize=12, fontweight='bold', color='#1F2937', pad=10)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.set_xticks([])

    save_chart(fig, output_path)
    return output_path


def create_competitor_comparison(
    company_name: str,
    company_scores: dict,
    competitor_data: list[dict],
    output_path: str
) -> str:
    """Create competitor comparison bar chart.

    Args:
        company_name: Your company name
        company_scores: Dict with 'overall' and 'ai_visibility' keys
        competitor_data: List of dicts with 'name', 'overall_diff', 'ai_visibility_diff'
        output_path: Path to save chart

    Returns:
        Path to saved chart
    """
    setup_chart_style()

    labels = [company_name[:15]]
    overall_scores = [company_scores.get('overall', 0)]
    ai_scores = [company_scores.get('ai_visibility', 0)]

    for comp in competitor_data[:4]:
        labels.append(comp.get('name', 'Competitor')[:15])
        overall_scores.append(company_scores.get('overall', 0) - comp.get('overall_diff', 0))
        ai_scores.append(company_scores.get('ai_visibility', 0) - comp.get('ai_diff', 0))

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 3))
    bars1 = ax.bar(x - width/2, overall_scores, width, label='Overall Score', color=CHART_PALETTE[0])
    ax.bar(x + width/2, ai_scores, width, label='AI Visibility', color='#8B5CF6')

    ax.set_ylabel('Score')
    ax.set_title('Competitive Score Comparison', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha='right', fontsize=8)
    ax.legend(loc='upper right', fontsize=8)
    ax.set_ylim(0, 100)
    ax.axhline(y=70, color='gray', linestyle='--', alpha=0.5, linewidth=1)

    # Value labels
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width()/2, height),
                   xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=7)

    save_chart(fig, output_path)
    return output_path
