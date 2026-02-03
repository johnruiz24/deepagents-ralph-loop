"""AWS Bedrock configuration with exponential backoff retry logic.

Supports Cross-Region Inference (CRIS) with EU models.
Default configuration:
- Profile: mll-sandbox (configurable via AWS_PROFILE)
- Region: eu-central-1
- Model: eu.anthropic.claude-opus-4-5-20251101-v1:0 (CRIS)
"""

import os
from typing import Optional, Literal

import boto3
from botocore.config import Config
from langchain_aws import ChatBedrockConverse


# Model presets for different use cases
MODEL_PRESETS = {
    # Primary model for high-quality content generation (CRIS)
    "opus": "eu.anthropic.claude-opus-4-5-20251101-v1:0",
    # Fast model for quick tasks
    "haiku": "eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    # Sonnet for balanced performance
    "sonnet": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
}


def get_boto_config(
    max_attempts: int = 5,
    read_timeout: int = 300,
    connect_timeout: int = 60,
) -> Config:
    """
    Create boto3 Config with exponential backoff for AWS Bedrock.

    Args:
        max_attempts: Maximum number of retry attempts (default: 5)
        read_timeout: Read timeout in seconds (default: 300 = 5 minutes)
        connect_timeout: Connection timeout in seconds (default: 60 = 1 minute)

    Returns:
        Configured boto3 Config object with adaptive retry mode
    """
    return Config(
        read_timeout=read_timeout,
        connect_timeout=connect_timeout,
        retries={
            'max_attempts': max_attempts,
            'mode': 'adaptive'  # Exponential backoff with adaptive retry
        }
    )


def create_boto_session(profile_name: Optional[str] = None) -> boto3.Session:
    """
    Create boto3 session with optional profile.

    Args:
        profile_name: AWS profile name (default: from AWS_PROFILE env var or mll-sandbox)

    Returns:
        Configured boto3 Session
    """
    profile = profile_name or os.getenv("AWS_PROFILE", "mll-sandbox")
    return boto3.Session(profile_name=profile)


def create_bedrock_llm(
    model: Optional[str] = None,
    model_preset: Optional[Literal["opus", "haiku", "sonnet"]] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    region_name: Optional[str] = None,
    profile_name: Optional[str] = None,
) -> ChatBedrockConverse:
    """
    Create ChatBedrockConverse LLM with exponential backoff configuration.

    Supports Cross-Region Inference (CRIS) with EU Anthropic models.

    Args:
        model: Full model ID (overrides model_preset)
        model_preset: Preset name ("opus", "haiku", "sonnet") - default: opus
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens to generate (default: 4096)
        region_name: AWS region (default: from AWS_REGION env var or eu-central-1)
        profile_name: AWS profile (default: from AWS_PROFILE env var or mll-sandbox)

    Returns:
        Configured ChatBedrockConverse instance
    """
    # Determine model
    if model:
        model_id = model
    elif model_preset:
        model_id = MODEL_PRESETS.get(model_preset, MODEL_PRESETS["opus"])
    else:
        model_id = os.getenv("ANTHROPIC_MODEL", MODEL_PRESETS["opus"])

    region_name = region_name or os.getenv("AWS_REGION", "eu-central-1")

    boto_config = get_boto_config()

    # Create credentials provider if profile specified
    credentials_profile = profile_name or os.getenv("AWS_PROFILE", "mll-sandbox")

    return ChatBedrockConverse(
        model=model_id,
        region_name=region_name,
        temperature=temperature,
        max_tokens=max_tokens,
        config=boto_config,
        credentials_profile_name=credentials_profile,
    )


def create_bedrock_llm_for_content(
    max_tokens: int = 8192,
    temperature: float = 0.7,
) -> ChatBedrockConverse:
    """
    Create LLM optimized for long-form content generation.

    Uses Claude Opus 4.5 with higher token limit for article writing.

    Args:
        max_tokens: Maximum tokens (default: 8192 for longer content)
        temperature: Sampling temperature (default: 0.7)

    Returns:
        ChatBedrockConverse configured for content generation
    """
    return create_bedrock_llm(
        model_preset="opus",
        max_tokens=max_tokens,
        temperature=temperature,
    )


def create_bedrock_llm_for_editing(
    temperature: float = 0.3,
) -> ChatBedrockConverse:
    """
    Create LLM optimized for editing tasks.

    Uses lower temperature for more consistent editing.

    Args:
        temperature: Sampling temperature (default: 0.3 for consistency)

    Returns:
        ChatBedrockConverse configured for editing
    """
    return create_bedrock_llm(
        model_preset="opus",
        max_tokens=8192,
        temperature=temperature,
    )


def create_bedrock_runtime_client(
    region_name: Optional[str] = None,
) -> boto3.client:
    """
    Create bedrock-runtime client for image generation with exponential backoff.

    Args:
        region_name: AWS region (default: from AWS_REGION env var or eu-central-1)

    Returns:
        Configured boto3 bedrock-runtime client
    """
    region_name = region_name or os.getenv("AWS_REGION", "eu-central-1")
    boto_config = get_boto_config()

    return boto3.client(
        'bedrock-runtime',
        region_name=region_name,
        config=boto_config,
    )
