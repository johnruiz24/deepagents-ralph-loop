"""Hero image generation using AWS Bedrock Titan Image Generator."""

import base64
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.utils.bedrock_config import create_bedrock_runtime_client


def generate_hero_image(
    prompt: str,
    output_dir: str = "output/images",
    filename: Optional[str] = None,
    style: str = "technical",
    width: int = 1024,
    height: int = 1024,
) -> dict:
    """
    Generate a hero image using AWS Bedrock Titan Image Generator.

    Args:
        prompt: Description of the image to generate
        output_dir: Directory to save generated images
        filename: Optional filename (without extension)
        style: Style hint ('technical', 'artistic', 'professional')
        width: Image width in pixels (default: 1024)
        height: Image height in pixels (default: 1024)

    Returns:
        Dictionary with image path, URL placeholder, and metadata
    """
    client = create_bedrock_runtime_client()

    # Enhance prompt based on style
    style_enhancements = {
        "technical": "professional technical illustration, clean modern design, subtle gradients, dark background with accent colors, suitable for tech blog",
        "artistic": "creative digital art, vibrant colors, abstract tech elements, visually striking",
        "professional": "clean professional business illustration, corporate style, minimalist design",
    }

    enhanced_prompt = f"{prompt}. {style_enhancements.get(style, style_enhancements['technical'])}"

    # Prepare request body for Titan Image Generator
    request_body = {
        "taskType": "TEXT_IMAGE",
        "textToImageParams": {
            "text": enhanced_prompt,
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "width": width,
            "height": height,
            "cfgScale": 8.0,
            "seed": int(datetime.now().timestamp()) % 2147483647,
        },
    }

    try:
        response = client.invoke_model(
            modelId="amazon.titan-image-generator-v1",
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())

        # Extract the generated image
        if "images" in response_body and response_body["images"]:
            image_data = base64.b64decode(response_body["images"][0])

            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"hero_{timestamp}"

            # Save image
            image_path = Path(output_dir) / f"{filename}.png"
            with open(image_path, "wb") as f:
                f.write(image_data)

            return {
                "success": True,
                "path": str(image_path),
                "type": "hero",
                "description": prompt,
                "url": f"file://{image_path.absolute()}",  # Placeholder until uploaded
                "width": width,
                "height": height,
                "model": "amazon.titan-image-generator-v1",
            }
        else:
            return {
                "success": False,
                "error": "No image generated",
                "response": response_body,
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def generate_technical_hero(
    topic: str,
    elements: Optional[list[str]] = None,
    output_dir: str = "output/images",
) -> dict:
    """
    Generate a technical hero image for an article.

    Args:
        topic: The article topic
        elements: Optional list of elements to include (e.g., ['AWS', 'Python', 'agents'])
        output_dir: Directory to save generated images

    Returns:
        Dictionary with image details
    """
    # Build prompt
    base_prompt = f"Technical illustration for article about {topic}"

    if elements:
        elements_str = ", ".join(elements)
        base_prompt += f", featuring {elements_str}"

    base_prompt += ", modern tech aesthetic, dark theme with blue and purple accents, code visualization elements, professional publication quality"

    return generate_hero_image(
        prompt=base_prompt,
        output_dir=output_dir,
        style="technical",
    )


def generate_placeholder_hero(
    topic: str,
    output_dir: str = "output/images",
    filename: Optional[str] = None,
) -> dict:
    """
    Generate a placeholder hero image when Bedrock is not available.

    This creates a simple SVG placeholder that can be used during development.

    Args:
        topic: The article topic
        output_dir: Directory to save the placeholder
        filename: Optional filename

    Returns:
        Dictionary with placeholder image details
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hero_placeholder_{timestamp}"

    # Create simple SVG placeholder
    svg_content = f'''<svg width="1024" height="1024" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1a1a2e;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#16213e;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#bg)"/>
  <text x="512" y="480" font-family="Arial, sans-serif" font-size="36" fill="#3B82F6" text-anchor="middle">
    Hero Image
  </text>
  <text x="512" y="540" font-family="Arial, sans-serif" font-size="24" fill="#94a3b8" text-anchor="middle">
    {topic[:50]}{"..." if len(topic) > 50 else ""}
  </text>
  <text x="512" y="600" font-family="Arial, sans-serif" font-size="16" fill="#64748b" text-anchor="middle">
    [Placeholder - Generate with Bedrock]
  </text>
</svg>'''

    svg_path = Path(output_dir) / f"{filename}.svg"
    with open(svg_path, "w") as f:
        f.write(svg_content)

    return {
        "success": True,
        "path": str(svg_path),
        "type": "hero",
        "description": f"Placeholder hero for: {topic}",
        "url": f"file://{svg_path.absolute()}",
        "is_placeholder": True,
    }
