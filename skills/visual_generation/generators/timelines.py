"""
Professional timeline and trajectory chart generation using plotly.

Generates interactive and static timeline visualizations
showing market trajectories, milestones, and inflection points.
"""

from pathlib import Path
from typing import Any, Literal, Optional
from dataclasses import dataclass


@dataclass 
class TimelineConfig:
    """Configuration for timeline generation."""
    width: int = 1200
    height: int = 700
    font_family: str = "Arial, sans-serif"
    line_color: str = "#1E3A5F"
    marker_color: str = "#3D7EAA"
    annotation_color: str = "#D32F2F"
    background_color: str = "white"
    grid_color: str = "#E0E0E0"


def generate_timeline(
    milestones: list[dict[str, Any]],
    output_path: str | Path,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    config: Optional[TimelineConfig] = None,
    generate_html: bool = False,
) -> Path:
    """
    Generate a professional timeline/trajectory chart.
    
    Args:
        milestones: List of milestone dicts with 'year', 'value', and optional 'label'
        output_path: Path to save the chart
        title: Optional chart title
        subtitle: Optional subtitle
        config: Optional configuration
        generate_html: Also generate interactive HTML version
        
    Returns:
        Path to the generated PNG
    """
    import plotly.graph_objects as go
    
    config = config or TimelineConfig()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract data
    years = [m["year"] for m in milestones]
    values = [m["value"] for m in milestones]
    labels = [m.get("label", "") for m in milestones]
    
    # Create figure
    fig = go.Figure()
    
    # Add main line
    fig.add_trace(go.Scatter(
        x=years,
        y=values,
        mode="lines+markers",
        name="Market Value",
        line=dict(color=config.line_color, width=3),
        marker=dict(size=12, color=config.marker_color, line=dict(width=2, color="white")),
        hovertemplate="Year: %{x}<br>Value: $%{y}B<extra></extra>"
    ))
    
    # Add area fill
    fig.add_trace(go.Scatter(
        x=years,
        y=values,
        fill="tozeroy",
        fillcolor="rgba(61, 126, 170, 0.15)",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    ))
    
    # Add annotations for labeled milestones
    annotations = []
    for year, value, label in zip(years, values, labels):
        if label:
            is_inflection = "inflection" in label.lower() or "critical" in label.lower()
            annotations.append(dict(
                x=year,
                y=value,
                text=f"<b>{label}</b><br>${value}B",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor=config.annotation_color if is_inflection else config.line_color,
                ax=0,
                ay=-50 if is_inflection else -40,
                font=dict(
                    size=12 if is_inflection else 10,
                    color=config.annotation_color if is_inflection else "#333"
                ),
                bgcolor="white" if is_inflection else None,
                bordercolor=config.annotation_color if is_inflection else None,
                borderwidth=2 if is_inflection else 0,
                borderpad=4 if is_inflection else 0,
            ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"<b>{title or 'Market Trajectory'}</b>" + 
                 (f"<br><sub>{subtitle}</sub>" if subtitle else ""),
            x=0.5,
            font=dict(size=18, family=config.font_family)
        ),
        xaxis=dict(
            title="Year",
            showgrid=True,
            gridcolor=config.grid_color,
            dtick=1,
            tickfont=dict(size=12),
        ),
        yaxis=dict(
            title="Market Value (USD Billions)",
            showgrid=True,
            gridcolor=config.grid_color,
            tickprefix="$",
            ticksuffix="B",
            tickfont=dict(size=12),
        ),
        annotations=annotations,
        font=dict(family=config.font_family),
        plot_bgcolor=config.background_color,
        paper_bgcolor=config.background_color,
        width=config.width,
        height=config.height,
        margin=dict(t=100, b=60, l=80, r=40),
        showlegend=False,
    )
    
    # Save PNG
    fig.write_image(str(output_path), scale=2)  # 2x scale for 300 DPI equivalent
    
    # Optionally save HTML
    if generate_html:
        html_path = output_path.with_suffix(".html")
        fig.write_html(str(html_path), include_plotlyjs="cdn")
    
    return output_path


def generate_market_trajectory(
    years: list[int],
    values: list[float],
    output_path: str | Path,
    inflection_year: Optional[int] = None,
    inflection_label: str = "Inflection Point",
) -> Path:
    """
    Generate a market trajectory chart with optional inflection point.
    
    Args:
        years: List of years
        values: List of market values (in billions)
        output_path: Output path
        inflection_year: Year to mark as inflection point
        inflection_label: Label for inflection point
        
    Returns:
        Path to generated chart
    """
    milestones = []
    for year, value in zip(years, values):
        milestone = {"year": year, "value": value}
        if inflection_year and year == inflection_year:
            milestone["label"] = inflection_label
        milestones.append(milestone)
    
    return generate_timeline(
        milestones=milestones,
        output_path=output_path,
        title="Travel Technology Market Evolution",
        subtitle="Projected market size and strategic inflection points",
    )


def generate_adoption_timeline(
    stages: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """
    Generate a technology adoption timeline.
    
    Args:
        stages: List of adoption stage dicts with 'year', 'adoption_rate', 'stage_name'
        output_path: Output path
        
    Returns:
        Path to generated chart
    """
    milestones = [
        {
            "year": s["year"],
            "value": s["adoption_rate"],
            "label": s.get("stage_name", "")
        }
        for s in stages
    ]
    
    return generate_timeline(
        milestones=milestones,
        output_path=output_path,
        title="AI Adoption Trajectory in Travel Industry",
        subtitle="Percentage of companies with deployed AI solutions",
        config=TimelineConfig(
            line_color="#388E3C",
            marker_color="#4CAF50",
            annotation_color="#1B5E20",
        )
    )
