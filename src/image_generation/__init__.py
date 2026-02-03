"""Image generation module for the Agent Newsletter System."""

from src.image_generation.hero_image_generator import (
    generate_hero_image,
    generate_technical_hero,
    generate_placeholder_hero,
)
from src.image_generation.bedrock_image_gen import (
    generate_technical_hero_bedrock,
    generate_titan_image,
)
from src.image_generation.diagram_generator import (
    render_mermaid_to_png,
    generate_comparison_diagram,
    generate_architecture_diagram,
    generate_flow_diagram,
    generate_sequence_diagram,
    save_mermaid_as_file,
)

__all__ = [
    "generate_hero_image",
    "generate_technical_hero",
    "generate_technical_hero_bedrock",
    "generate_titan_image",
    "generate_placeholder_hero",
    "render_mermaid_to_png",
    "generate_comparison_diagram",
    "generate_architecture_diagram",
    "generate_flow_diagram",
    "generate_sequence_diagram",
    "save_mermaid_as_file",
]
