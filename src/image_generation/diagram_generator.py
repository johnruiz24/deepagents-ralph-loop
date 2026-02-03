"""Diagram generation using Mermaid syntax with rendering to PNG."""

import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


def render_mermaid_to_png(
    mermaid_code: str,
    output_path: str,
    width: int = 1200,
    height: int = 800,
    background_color: str = "#1a1a1a",
) -> dict:
    """
    Render Mermaid diagram to PNG using mermaid-cli (mmdc).

    Requires: npm install -g @mermaid-js/mermaid-cli

    Args:
        mermaid_code: Mermaid diagram code
        output_path: Path to save the PNG
        width: Image width in pixels
        height: Image height in pixels
        background_color: Background color (hex)

    Returns:
        Dictionary with render status and path
    """
    # Create temp file for mermaid code
    temp_dir = Path("output/.temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    mmd_file = temp_dir / f"diagram_{timestamp}.mmd"

    # Write mermaid code
    with open(mmd_file, "w") as f:
        f.write(mermaid_code)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try using mmdc (mermaid-cli)
        result = subprocess.run(
            [
                "mmdc",
                "-i", str(mmd_file),
                "-o", output_path,
                "-w", str(width),
                "-H", str(height),
                "-b", background_color,
                "--pdfFit",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return {
                "success": True,
                "path": output_path,
                "mermaid_code": mermaid_code,
            }
        else:
            return {
                "success": False,
                "error": result.stderr or "mmdc command failed",
                "mermaid_code": mermaid_code,
            }

    except FileNotFoundError:
        # mmdc not installed, save as .mmd file with instructions
        mmd_output = Path(output_path).with_suffix(".mmd")
        with open(mmd_output, "w") as f:
            f.write(mermaid_code)

        return {
            "success": True,
            "path": str(mmd_output),
            "mermaid_code": mermaid_code,
            "note": "Saved as .mmd file. Install mermaid-cli to render PNG: npm install -g @mermaid-js/mermaid-cli",
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Mermaid rendering timed out",
            "mermaid_code": mermaid_code,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "mermaid_code": mermaid_code,
        }

    finally:
        # Cleanup temp file
        if mmd_file.exists():
            mmd_file.unlink()


def generate_comparison_diagram(
    left_title: str,
    left_items: list[str],
    right_title: str,
    right_items: list[str],
    output_dir: str = "output/images",
    filename: Optional[str] = None,
) -> dict:
    """
    Generate a side-by-side comparison diagram.

    Args:
        left_title: Title for left side (e.g., "Simple Approach")
        left_items: Items/limitations for left side
        right_title: Title for right side (e.g., "Advanced Approach")
        right_items: Items/advantages for right side
        output_dir: Directory to save diagram
        filename: Optional filename

    Returns:
        Dictionary with diagram details
    """
    # Build Mermaid flowchart
    left_items_formatted = "<br/>".join(f"- {item}" for item in left_items)
    right_items_formatted = "<br/>".join(f"+ {item}" for item in right_items)

    mermaid_code = f'''flowchart LR
    subgraph LEFT["{left_title}"]
        direction TB
        L1["{left_items_formatted}"]
    end

    subgraph RIGHT["{right_title}"]
        direction TB
        R1["{right_items_formatted}"]
    end

    LEFT --> |"vs"| RIGHT

    style LEFT fill:#ef4444,stroke:#dc2626,color:#fff
    style RIGHT fill:#10b981,stroke:#059669,color:#fff
    style L1 fill:#fecaca,stroke:#ef4444,color:#000
    style R1 fill:#a7f3d0,stroke:#10b981,color:#000'''

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comparison_{timestamp}"

    output_path = str(Path(output_dir) / f"{filename}.png")

    result = render_mermaid_to_png(mermaid_code, output_path)
    result["type"] = "comparison_diagram"
    result["description"] = f"Comparison: {left_title} vs {right_title}"

    return result


def generate_architecture_diagram(
    title: str,
    components: list[dict],
    output_dir: str = "output/images",
    filename: Optional[str] = None,
) -> dict:
    """
    Generate an architecture diagram.

    Args:
        title: Diagram title
        components: List of components, each with 'name', 'description', and optional 'children'
        output_dir: Directory to save diagram
        filename: Optional filename

    Returns:
        Dictionary with diagram details
    """
    # Build component lines
    component_lines = []
    style_lines = []

    colors = ["#3B82F6", "#10B981", "#A855F7", "#F59E0B", "#EF4444"]

    for i, comp in enumerate(components):
        comp_id = f"C{i}"
        comp_name = comp.get("name", f"Component {i}")
        comp_desc = comp.get("description", "")

        component_lines.append(f'    {comp_id}["{comp_name}<br/><small>{comp_desc}</small>"]')
        style_lines.append(f"    style {comp_id} fill:{colors[i % len(colors)]},stroke:#fff,color:#fff")

        # Add children if present
        children = comp.get("children", [])
        for j, child in enumerate(children):
            child_id = f"C{i}_{j}"
            component_lines.append(f'    {comp_id} --> {child_id}["{child}"]')

    # Build connections between main components
    connections = []
    for i in range(len(components) - 1):
        connections.append(f"    C{i} --> C{i+1}")

    mermaid_code = f'''flowchart TB
    subgraph ARCH["{title}"]
        direction TB
{chr(10).join(component_lines)}
{chr(10).join(connections)}
    end

{chr(10).join(style_lines)}'''

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"architecture_{timestamp}"

    output_path = str(Path(output_dir) / f"{filename}.png")

    result = render_mermaid_to_png(mermaid_code, output_path)
    result["type"] = "architecture_diagram"
    result["description"] = title

    return result


def generate_flow_diagram(
    title: str,
    steps: list[dict],
    output_dir: str = "output/images",
    filename: Optional[str] = None,
) -> dict:
    """
    Generate a flow/process diagram.

    Args:
        title: Diagram title
        steps: List of steps, each with 'name' and optional 'description'
        output_dir: Directory to save diagram
        filename: Optional filename

    Returns:
        Dictionary with diagram details
    """
    step_lines = []
    style_lines = []
    colors = ["#3B82F6", "#10B981", "#A855F7", "#F59E0B"]

    for i, step in enumerate(steps):
        step_id = f"S{i}"
        step_name = step.get("name", f"Step {i+1}")
        step_desc = step.get("description", "")

        if step_desc:
            step_lines.append(f'    {step_id}["Step {i+1}: {step_name}<br/>{step_desc}"]')
        else:
            step_lines.append(f'    {step_id}["Step {i+1}: {step_name}"]')

        style_lines.append(f"    style {step_id} fill:{colors[i % len(colors)]},stroke:#fff,color:#fff")

    # Connect steps
    connections = []
    for i in range(len(steps) - 1):
        connections.append(f"    S{i} --> S{i+1}")

    mermaid_code = f'''flowchart TB
    subgraph FLOW["{title}"]
        direction TB
{chr(10).join(step_lines)}
{chr(10).join(connections)}
    end

{chr(10).join(style_lines)}'''

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"flow_{timestamp}"

    output_path = str(Path(output_dir) / f"{filename}.png")

    result = render_mermaid_to_png(mermaid_code, output_path)
    result["type"] = "flow_diagram"
    result["description"] = title

    return result


def generate_sequence_diagram(
    title: str,
    participants: list[str],
    interactions: list[dict],
    output_dir: str = "output/images",
    filename: Optional[str] = None,
) -> dict:
    """
    Generate a sequence diagram.

    Args:
        title: Diagram title
        participants: List of participant names
        interactions: List of interactions with 'from', 'to', 'message', and optional 'type' (sync/async)
        output_dir: Directory to save diagram
        filename: Optional filename

    Returns:
        Dictionary with diagram details
    """
    # Build participant declarations
    participant_lines = [f"    participant {p}" for p in participants]

    # Build interaction lines
    interaction_lines = []
    for interaction in interactions:
        from_p = interaction.get("from", participants[0] if participants else "A")
        to_p = interaction.get("to", participants[1] if len(participants) > 1 else "B")
        message = interaction.get("message", "")
        int_type = interaction.get("type", "sync")

        arrow = "->>" if int_type == "async" else "->"
        interaction_lines.append(f"    {from_p}{arrow}{to_p}: {message}")

    mermaid_code = f'''sequenceDiagram
    title {title}
{chr(10).join(participant_lines)}
{chr(10).join(interaction_lines)}'''

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sequence_{timestamp}"

    output_path = str(Path(output_dir) / f"{filename}.png")

    result = render_mermaid_to_png(mermaid_code, output_path)
    result["type"] = "sequence_diagram"
    result["description"] = title

    return result


def save_mermaid_as_file(
    mermaid_code: str,
    output_dir: str = "output/images",
    filename: Optional[str] = None,
) -> dict:
    """
    Save Mermaid code to a .mmd file (for later rendering or embedding).

    Args:
        mermaid_code: Mermaid diagram code
        output_dir: Directory to save file
        filename: Optional filename

    Returns:
        Dictionary with file details
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"diagram_{timestamp}"

    output_path = Path(output_dir) / f"{filename}.mmd"

    with open(output_path, "w") as f:
        f.write(mermaid_code)

    return {
        "success": True,
        "path": str(output_path),
        "mermaid_code": mermaid_code,
        "type": "mermaid_source",
    }
