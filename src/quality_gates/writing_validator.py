"""Writing quality gate validator."""

import re
from typing import Optional

import textstat


def validate_writing(
    article: str,
    images: list[dict],
    code_validation_results: Optional[dict] = None,
) -> tuple[bool, list[str]]:
    """
    Validate writing quality against requirements.

    Args:
        article: Complete article text
        images: List of generated images with metadata
        code_validation_results: Results from code validation

    Returns:
        Tuple of (passed: bool, issues: list[str])
    """
    issues = []

    # Check word count
    word_count = len(article.split())
    if word_count < 3000:
        issues.append(f"Article only {word_count} words, need at least 3000")
    elif word_count > 6000:
        issues.append(f"Article {word_count} words, should be under 6000")

    # Check readability
    readability = textstat.flesch_reading_ease(article)
    if readability < 60:
        issues.append(f"Readability score {readability:.1f} below threshold of 60")

    # Check sections
    sections = extract_sections(article)
    if len(sections) < 5:
        issues.append(f"Only {len(sections)} sections found, need at least 5")

    # Check visual content
    hero_images = [img for img in images if img.get("type") == "hero"]
    diagrams = [img for img in images if img.get("type") == "diagram"]

    if len(hero_images) < 2:
        issues.append(f"Only {len(hero_images)} hero images, need at least 2")

    if len(diagrams) < 4:
        issues.append(f"Only {len(diagrams)} diagrams, need at least 4")

    if len(images) < 6:
        issues.append(f"Only {len(images)} total images, need at least 6")

    # Check code examples
    code_blocks = extract_code_blocks(article)
    if len(code_blocks) < 3:
        issues.append(f"Only {len(code_blocks)} code blocks, need at least 3")

    # Check code validation
    if code_validation_results:
        invalid_code = [
            block for block, result in code_validation_results.items()
            if not result.get("valid", False)
        ]
        if invalid_code:
            issues.append(f"{len(invalid_code)} code blocks have syntax errors")

    # Check image accessibility
    inaccessible_images = [
        img for img in images
        if not img.get("url") or img.get("url") == ""
    ]
    if inaccessible_images:
        issues.append(f"{len(inaccessible_images)} images have no accessible URL")

    passed = len(issues) == 0
    return passed, issues


def extract_sections(article: str) -> list[str]:
    """
    Extract section titles from article.

    Args:
        article: Article markdown text

    Returns:
        List of section titles
    """
    # Match markdown headers (# or ##)
    pattern = r'^#{1,2}\s+(.+)$'
    sections = re.findall(pattern, article, re.MULTILINE)
    return sections


def extract_code_blocks(article: str) -> list[str]:
    """
    Extract code blocks from article.

    Args:
        article: Article markdown text

    Returns:
        List of code block contents
    """
    # Match fenced code blocks
    pattern = r'```[\w]*\n(.*?)```'
    code_blocks = re.findall(pattern, article, re.DOTALL)
    return code_blocks


def calculate_readability_score(article: str) -> dict:
    """
    Calculate multiple readability metrics.

    Args:
        article: Article text

    Returns:
        Dictionary of readability metrics
    """
    return {
        "flesch_reading_ease": textstat.flesch_reading_ease(article),
        "flesch_kincaid_grade": textstat.flesch_kincaid_grade(article),
        "gunning_fog": textstat.gunning_fog(article),
        "automated_readability_index": textstat.automated_readability_index(article),
        "coleman_liau_index": textstat.coleman_liau_index(article),
    }
