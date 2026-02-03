"""Publishing quality gate validator."""

import os
from typing import Optional

import requests


def validate_publishing_package(article_package: dict) -> tuple[bool, list[str]]:
    """
    Validate publishing package completeness and accessibility.

    Args:
        article_package: Publishing package metadata

    Returns:
        Tuple of (passed: bool, issues: list[str])
    """
    issues = []

    # Required files
    required_files = [
        "article.md",
        "preview.html",
        "images_manifest.json",
        "metadata.json",
        "PUBLISHING_GUIDE.md",
    ]

    package_path = article_package.get("path", "")
    if not package_path or not os.path.exists(package_path):
        issues.append(f"Package path does not exist: {package_path}")
        return False, issues

    # Check all required files exist
    for filename in required_files:
        filepath = os.path.join(package_path, filename)
        if not os.path.exists(filepath):
            issues.append(f"Missing required file: {filename}")

    # Validate markdown content
    article_md_path = os.path.join(package_path, "article.md")
    if os.path.exists(article_md_path):
        with open(article_md_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        if len(markdown_content) < 100:
            issues.append("article.md is suspiciously short")

        # Check for image embeds
        if "![" not in markdown_content:
            issues.append("article.md contains no image embeds")

    # Validate image URLs
    images = article_package.get("images", [])
    if len(images) < 6:
        issues.append(f"Only {len(images)} images in package, need at least 6")

    inaccessible_images = []
    for img in images:
        url = img.get("url", "")
        if not url:
            inaccessible_images.append(img.get("description", "unknown"))
        elif not check_url_accessible(url):
            inaccessible_images.append(f"{img.get('description', 'unknown')} at {url}")

    if inaccessible_images:
        issues.append(f"{len(inaccessible_images)} images not accessible: {', '.join(inaccessible_images[:3])}")

    passed = len(issues) == 0
    return passed, issues


def check_url_accessible(url: str, timeout: int = 5) -> bool:
    """
    Check if URL is accessible via HEAD request.

    Args:
        url: URL to check
        timeout: Request timeout in seconds

    Returns:
        True if URL is accessible (status 200-299)
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return 200 <= response.status_code < 300
    except Exception:
        return False


def validate_markdown(markdown_content: str) -> bool:
    """
    Validate markdown syntax.

    Args:
        markdown_content: Markdown text to validate

    Returns:
        True if markdown appears valid
    """
    # Basic validation checks
    if not markdown_content or len(markdown_content) < 100:
        return False

    # Check for at least one header
    if not any(line.startswith("#") for line in markdown_content.split("\n")):
        return False

    # Check for balanced code fences
    code_fence_count = markdown_content.count("```")
    if code_fence_count % 2 != 0:
        return False

    return True
