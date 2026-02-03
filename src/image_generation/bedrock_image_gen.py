"""AWS Bedrock Titan Image Generator for hero images."""

import base64
import json
import boto3
from pathlib import Path
from datetime import datetime
from typing import Optional


def generate_titan_image(
    prompt: str,
    output_dir: str = "output/images",
    negative_prompt: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    cfg_scale: float = 8.0,
    seed: Optional[int] = None,
    profile_name: str = "mll-dev",
) -> dict:
    """
    Generate an image using AWS Bedrock Titan Image Generator.

    Args:
        prompt: Text description of the image to generate
        output_dir: Directory to save the generated image
        negative_prompt: Things to avoid in the image
        width: Image width (must be multiple of 64, max 2048)
        height: Image height (must be multiple of 64, max 2048)
        cfg_scale: How closely to follow the prompt (1-10)
        seed: Random seed for reproducibility
        profile_name: AWS profile to use

    Returns:
        Dictionary with image path and metadata
    """
    try:
        # Create Bedrock client
        session = boto3.Session(profile_name=profile_name)
        bedrock_runtime = session.client(
            service_name='bedrock-runtime',
            region_name='us-east-1'  # Titan Image is in us-east-1
        )

        # Build request body
        request_body = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": prompt
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "width": width,
                "height": height,
                "cfgScale": cfg_scale,
            }
        }

        if negative_prompt:
            request_body["textToImageParams"]["negativeText"] = negative_prompt

        if seed is not None:
            request_body["imageGenerationConfig"]["seed"] = seed

        # Call Bedrock
        response = bedrock_runtime.invoke_model(
            modelId="amazon.titan-image-generator-v2:0",
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )

        # Parse response
        response_body = json.loads(response['body'].read())

        # Extract base64 image
        image_base64 = response_body['images'][0]
        image_data = base64.b64decode(image_base64)

        # Save image
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hero_{timestamp}.png"
        output_path = Path(output_dir) / filename

        with open(output_path, 'wb') as f:
            f.write(image_data)

        return {
            "success": True,
            "path": str(output_path),
            "prompt": prompt,
            "width": width,
            "height": height,
            "type": "hero_image",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prompt": prompt,
        }


def generate_technical_hero_bedrock(
    topic: str,
    style: str = "professional technical illustration",
    output_dir: str = "output/images",
) -> dict:
    """
    Generate a hero image for a technical article.

    Args:
        topic: Article topic
        style: Visual style description
        output_dir: Output directory

    Returns:
        Dictionary with image details
    """
    # Build detailed prompt
    prompt = f"""A professional, eye-catching hero image for a technical article about {topic}.

Style: {style}, clean and modern, suitable for Medium publication.

The image should include:
- Technical elements (code, diagrams, circuits, or abstract tech patterns)
- Professional color scheme (blues, purples, or tech-industry colors)
- Clear focal point
- High quality, publication-ready
- No text or words in the image

The mood should be: innovative, sophisticated, trustworthy, cutting-edge."""

    negative_prompt = "text, words, letters, watermark, blurry, low quality, amateur, messy, cluttered"

    return generate_titan_image(
        prompt=prompt,
        output_dir=output_dir,
        negative_prompt=negative_prompt,
        width=1024,
        height=1024,
        cfg_scale=8.0,
    )
