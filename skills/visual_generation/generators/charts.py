"""
Professional chart generation using matplotlib and seaborn.

Generates HBR-quality bar charts, line charts, and area charts
at 300 DPI resolution with professional styling.
"""

from pathlib import Path
from typing import Any, Literal, Optional
from dataclasses import dataclass

# Use Agg backend for headless rendering
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Professional color palettes
PALETTES = {
    "hbr": ["#1E3A5F", "#3D7EAA", "#6BA3BE", "#9FC5D8", "#D4E8F2"],
    "contrast": ["#D32F2F", "#1976D2", "#388E3C", "#F57C00", "#7B1FA2"],
    "tui": ["#003580", "#0071C2", "#4A90D9", "#8AB4F8", "#C6DBEF"],
}


@dataclass
class ChartConfig:
    """Configuration for chart generation."""
    figsize: tuple = (12, 7)
    dpi: int = 300
    font_family: str = "sans-serif"
    title_size: int = 16
    label_size: int = 12
    palette: str = "hbr"


def generate_chart(
    chart_type: Literal["horizontal_bar", "vertical_bar", "line", "area"],
    data: dict[str, Any],
    title: str,
    output_path: str | Path,
    config: Optional[ChartConfig] = None,
    subtitle: Optional[str] = None,
    highlight: Optional[str] = None,
    annotations: Optional[list[dict]] = None,
) -> Path:
    """
    Generate a professional chart.
    
    Args:
        chart_type: Type of chart to generate
        data: Chart data with 'labels' and 'values' keys
        title: Chart title
        output_path: Path to save the chart
        config: Optional chart configuration
        subtitle: Optional subtitle
        highlight: Optional label to highlight
        annotations: Optional list of annotation dicts
        
    Returns:
        Path to the generated chart
    """
    config = config or ChartConfig()
    output_path = Path(output_path)
    
    # Setup style
    sns.set_style("whitegrid")
    plt.rcParams["font.family"] = config.font_family
    plt.rcParams["font.size"] = config.label_size
    plt.rcParams["figure.dpi"] = config.dpi
    
    # Get colors
    colors = PALETTES.get(config.palette, PALETTES["hbr"])
    
    # Create figure
    fig, ax = plt.subplots(figsize=config.figsize)
    
    labels = data["labels"]
    values = data["values"]
    
    # Generate colors with highlight
    bar_colors = []
    for label in labels:
        if highlight and label == highlight:
            bar_colors.append(colors[0])  # Primary color for highlight
        else:
            bar_colors.append(colors[2])  # Lighter color for others
    
    if chart_type == "horizontal_bar":
        bars = ax.barh(labels, values, color=bar_colors, edgecolor="white", linewidth=1.5)
        _add_bar_labels_horizontal(ax, bars, values)
        ax.set_xlabel(data.get("xlabel", "Value"), fontsize=config.label_size, fontweight="bold")
        
    elif chart_type == "vertical_bar":
        bars = ax.bar(labels, values, color=bar_colors, edgecolor="white", linewidth=1.5)
        _add_bar_labels_vertical(ax, bars, values)
        ax.set_ylabel(data.get("ylabel", "Value"), fontsize=config.label_size, fontweight="bold")
        plt.xticks(rotation=45, ha="right")
        
    elif chart_type == "line":
        ax.plot(labels, values, color=colors[0], linewidth=2.5, marker="o", markersize=8)
        ax.fill_between(labels, values, alpha=0.1, color=colors[0])
        ax.set_ylabel(data.get("ylabel", "Value"), fontsize=config.label_size, fontweight="bold")
        
    elif chart_type == "area":
        ax.fill_between(labels, values, alpha=0.3, color=colors[0])
        ax.plot(labels, values, color=colors[0], linewidth=2)
        ax.set_ylabel(data.get("ylabel", "Value"), fontsize=config.label_size, fontweight="bold")
    
    # Add title and subtitle
    ax.set_title(title, fontsize=config.title_size, fontweight="bold", pad=20)
    if subtitle:
        ax.text(0.5, 1.02, subtitle, transform=ax.transAxes, fontsize=config.label_size - 2,
                ha="center", style="italic", color="#666")
    
    # Style improvements
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x" if chart_type == "horizontal_bar" else "y", alpha=0.3, linestyle="--")
    
    # Add annotations
    if annotations:
        for ann in annotations:
            ax.annotate(
                ann["text"],
                xy=(ann["x"], ann["y"]),
                fontsize=10,
                fontweight="bold",
                ha="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF3CD", edgecolor="#856404")
            )
    
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=config.dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    
    return output_path


def _add_bar_labels_horizontal(ax, bars, values):
    """Add value labels to horizontal bars."""
    for bar, value in zip(bars, values):
        width = bar.get_width()
        ax.text(
            width + max(values) * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"${value:,.0f}M" if isinstance(value, (int, float)) else str(value),
            va="center",
            ha="left",
            fontsize=11,
            fontweight="bold"
        )


def _add_bar_labels_vertical(ax, bars, values):
    """Add value labels to vertical bars."""
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + max(values) * 0.02,
            f"${value:,.0f}M" if isinstance(value, (int, float)) else str(value),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold"
        )


# Convenience functions for common chart types
def generate_investment_chart(
    companies: list[str],
    investments: list[float],
    output_path: str | Path,
    highlight_company: Optional[str] = None,
) -> Path:
    """Generate technology investment comparison chart."""
    return generate_chart(
        chart_type="horizontal_bar",
        data={
            "labels": companies,
            "values": investments,
            "xlabel": "Technology Investment (USD Millions)"
        },
        title="Strategic Technology Investment Landscape",
        subtitle="Annual technology spending by major travel industry players",
        output_path=output_path,
        highlight=highlight_company,
    )


def generate_efficiency_chart(
    categories: list[str],
    gains: list[float],
    output_path: str | Path,
) -> Path:
    """Generate AI efficiency gains chart."""
    return generate_chart(
        chart_type="vertical_bar",
        data={
            "labels": categories,
            "values": gains,
            "ylabel": "Efficiency Gain (%)"
        },
        title="AI-Driven Operational Efficiency Gains",
        subtitle="Percentage improvement in key operational areas",
        output_path=output_path,
        config=ChartConfig(palette="contrast"),
    )
