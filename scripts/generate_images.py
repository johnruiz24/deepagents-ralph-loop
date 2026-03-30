#!/usr/bin/env python3
"""Generate 2 Gemini images for Medium article on Quantum Computing + ML"""

import os
import sys
from google import genai
from google.genai import types
from PIL import Image

# Check API key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# Image 1: Quantum Computing Visualization
print("Generating Image 1: Quantum Computing Visualization...")
prompt1 = "Abstract visualization of quantum computing: glowing quantum bits (qubits) in superposition, entanglement connections shown as light bridges between spheres, blue and purple neon colors, futuristic technology aesthetic, digital art style"

response1 = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[prompt1],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        ),
    ),
)

# Save first image
for part in response1.parts:
    if part.inline_data:
        image1 = part.as_image()
        image1.save("/Users/john.ruiz/Documents/projects/inkforge/ralph/quantum_visualization.jpg")
        print("✓ Image 1 saved: quantum_visualization.jpg")

# Image 2: Machine Learning Neural Network
print("\nGenerating Image 2: Machine Learning Neural Network...")
prompt2 = "Visualization of machine learning neural network: interconnected nodes forming layers, data flow represented as glowing particles, nodes light up with activation, gradient colors from green to orange to red, representing data intensity, modern AI aesthetic"

response2 = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[prompt2],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        ),
    ),
)

# Save second image
for part in response2.parts:
    if part.inline_data:
        image2 = part.as_image()
        image2.save("/Users/john.ruiz/Documents/projects/inkforge/ralph/neural_network.jpg")
        print("✓ Image 2 saved: neural_network.jpg")

print("\n✓ Both images generated successfully!")
