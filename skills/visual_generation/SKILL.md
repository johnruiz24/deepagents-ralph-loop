# Visual Generation Skill

Professional-grade visual asset generation for HBR-quality newsletters.

## Overview

This skill generates publication-quality charts, diagrams, and timelines using industry-standard Python libraries. No LLM code generation - direct, reliable output.

## Capabilities

| Type | Library | Output |
|------|---------|--------|
| Bar/Line Charts | matplotlib + seaborn | PNG (300 DPI) |
| Architecture Diagrams | diagrams | PNG (300 DPI) |
| Timelines | plotly + kaleido | PNG + HTML |

## Usage

```python
from skills.visual_generation import generate_chart, generate_architecture, generate_timeline

# Generate investment comparison chart
chart_path = generate_chart(
    chart_type="horizontal_bar",
    data={
        "labels": ["TUI", "Booking.com", "Expedia", "Airbnb"],
        "values": [150, 800, 650, 500],
        "highlight": "TUI"
    },
    title="Technology Investment Landscape",
    output_path="chart_investment.png"
)

# Generate architecture diagram
diagram_path = generate_architecture(
    diagram_type="comparison",
    entities={
        "left": {"name": "TUI Model", "components": ["Hotels", "Aircraft", "Cruises"]},
        "right": {"name": "OTA Model", "components": ["API", "Aggregation"]}
    },
    output_path="diagram_architecture.png"
)

# Generate timeline
timeline_path = generate_timeline(
    milestones=[
        {"year": 2024, "value": 35, "label": "Current"},
        {"year": 2026, "value": 50, "label": "Inflection Point"},
        {"year": 2027, "value": 62, "label": "Target"}
    ],
    output_path="timeline_market.png"
)
```

## Quality Standards

- **Resolution**: 300 DPI (print-ready)
- **Color Palette**: Professional HBR-style
- **Typography**: Arial/Helvetica
- **File Size**: 100KB-500KB per image

## Integration

Agents call these functions as tools:

```python
class VisualAssetAgent(BaseAgent):
    def __init__(self, shared_state):
        super().__init__(shared_state)
        # Register skills as tools
        self.tools = [
            generate_chart,
            generate_architecture,
            generate_timeline
        ]
```
