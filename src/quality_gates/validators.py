"""Quality gate validators for research, writing, and publishing phases."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False


@dataclass
class QualityGateResult:
    """Result of a quality gate validation."""
    passed: bool
    score: float
    message: str
    details: dict


# Quality gate thresholds (can be overridden by environment variables)
def get_threshold(name: str, default: int) -> int:
    """Get threshold from environment or use default."""
    return int(os.getenv(name, default))


RESEARCH_QUALITY_THRESHOLD = get_threshold("RESEARCH_QUALITY_THRESHOLD", 85)
SOURCE_COUNT_THRESHOLD = get_threshold("SOURCE_COUNT_THRESHOLD", 5)
READABILITY_THRESHOLD = get_threshold("READABILITY_THRESHOLD", 60)
MIN_WORD_COUNT = 3000
MAX_WORD_COUNT = 6000
MIN_HERO_IMAGES = 2
MIN_DIAGRAMS = 4


def validate_research_quality(report: dict) -> QualityGateResult:
    """
    Validate research report quality.

    Args:
        report: Research report dictionary

    Returns:
        QualityGateResult with validation outcome
    """
    if "error" in report:
        return QualityGateResult(
            passed=False,
            score=0,
            message=f"Research error: {report['error']}",
            details={"error": report["error"]},
        )

    quality_score = report.get("quality_score", 0)
    sources = report.get("sources", [])
    num_sources = len(sources)

    # Count high credibility sources
    high_cred_sources = sum(
        1 for s in sources
        if s.get("credibility") in ["high", "medium"]
    )

    # Check key findings
    key_findings = report.get("key_findings", [])
    code_examples = report.get("code_examples", [])

    issues = []
    warnings = []

    # Quality score check
    if quality_score < RESEARCH_QUALITY_THRESHOLD:
        issues.append(f"Quality score {quality_score}/100 (need >= {RESEARCH_QUALITY_THRESHOLD})")

    # Source count check
    if num_sources < SOURCE_COUNT_THRESHOLD:
        issues.append(f"Only {num_sources} sources (need >= {SOURCE_COUNT_THRESHOLD})")

    # High credibility sources
    if high_cred_sources < 2:
        warnings.append(f"Only {high_cred_sources} high/medium credibility sources (recommend >= 2)")

    # Key findings
    if len(key_findings) < 5:
        warnings.append(f"Only {len(key_findings)} key findings (recommend >= 5)")

    # Code examples
    if len(code_examples) < 2:
        warnings.append(f"Only {len(code_examples)} code examples (recommend >= 2)")

    passed = len(issues) == 0

    return QualityGateResult(
        passed=passed,
        score=quality_score,
        message=(
            f"Research gate {'PASSED' if passed else 'FAILED'}: "
            f"Score {quality_score}/100, {num_sources} sources"
            + (f". Issues: {'; '.join(issues)}" if issues else "")
            + (f". Warnings: {'; '.join(warnings)}" if warnings else "")
        ),
        details={
            "quality_score": quality_score,
            "source_count": num_sources,
            "high_cred_sources": high_cred_sources,
            "key_findings_count": len(key_findings),
            "code_examples_count": len(code_examples),
            "issues": issues,
            "warnings": warnings,
        },
    )


def calculate_readability_score(text: str) -> float:
    """Calculate readability score using textstat or estimation."""
    if not text:
        return 0

    if TEXTSTAT_AVAILABLE:
        return textstat.flesch_reading_ease(text)

    # Simple estimation if textstat not available
    words = text.split()
    sentences = text.count(".") + text.count("!") + text.count("?")
    if sentences == 0:
        sentences = 1

    avg_words_per_sentence = len(words) / sentences
    # Flesch estimation: higher score = easier to read
    score = max(0, min(100, 100 - (avg_words_per_sentence - 15) * 2))
    return score


def validate_code_syntax(code: str, language: str = "python") -> tuple[bool, Optional[str]]:
    """
    Validate code syntax.

    Args:
        code: Code string to validate
        language: Programming language

    Returns:
        Tuple of (is_valid, error_message)
    """
    if language.lower() != "python":
        return True, None  # Only validate Python for now

    try:
        compile(code, "<string>", "exec")
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"


def validate_writing_quality(article: dict) -> QualityGateResult:
    """
    Validate article writing quality.

    Args:
        article: Article dictionary

    Returns:
        QualityGateResult with validation outcome
    """
    if "error" in article:
        return QualityGateResult(
            passed=False,
            score=0,
            message=f"Writing error: {article['error']}",
            details={"error": article["error"]},
        )

    content = article.get("content", "")
    word_count = article.get("word_count", len(content.split()))
    readability = article.get("readability_score", calculate_readability_score(content))
    images = article.get("images", [])
    code_examples = article.get("code_examples", [])
    sections = article.get("sections", [])

    # Count image types
    hero_images = [img for img in images if img.get("type") == "hero"]
    diagrams = [img for img in images if "diagram" in img.get("type", "")]

    # Validate code examples
    invalid_code = []
    for i, example in enumerate(code_examples):
        code = example.get("code", "")
        language = example.get("language", "python")
        is_valid, error = validate_code_syntax(code, language)
        if not is_valid:
            invalid_code.append(f"Example {i+1}: {error}")

    issues = []
    warnings = []

    # Word count
    if word_count < MIN_WORD_COUNT:
        issues.append(f"Word count {word_count} (need >= {MIN_WORD_COUNT})")
    elif word_count > MAX_WORD_COUNT:
        warnings.append(f"Word count {word_count} (recommend <= {MAX_WORD_COUNT})")

    # Readability
    if readability < READABILITY_THRESHOLD:
        issues.append(f"Readability {readability:.1f} (need >= {READABILITY_THRESHOLD})")

    # Hero images
    if len(hero_images) < MIN_HERO_IMAGES:
        issues.append(f"Only {len(hero_images)} hero images (need >= {MIN_HERO_IMAGES})")

    # Diagrams
    if len(diagrams) < MIN_DIAGRAMS:
        issues.append(f"Only {len(diagrams)} diagrams (need >= {MIN_DIAGRAMS})")

    # Code validation
    if invalid_code:
        issues.append(f"Invalid code: {'; '.join(invalid_code)}")

    # Sections
    if len(sections) < 3:
        warnings.append(f"Only {len(sections)} sections (recommend >= 5)")

    passed = len(issues) == 0

    # Calculate overall score
    score_components = {
        "word_count": min(25, int((word_count / MIN_WORD_COUNT) * 25)) if word_count <= MAX_WORD_COUNT else 20,
        "readability": min(25, int((readability / READABILITY_THRESHOLD) * 25)),
        "hero_images": min(15, len(hero_images) * 7),
        "diagrams": min(20, len(diagrams) * 5),
        "code_quality": 15 if len(invalid_code) == 0 else 0,
    }
    total_score = sum(score_components.values())

    return QualityGateResult(
        passed=passed,
        score=total_score,
        message=(
            f"Writing gate {'PASSED' if passed else 'FAILED'}: "
            f"{word_count} words, readability {readability:.1f}, "
            f"{len(hero_images)} hero images, {len(diagrams)} diagrams"
            + (f". Issues: {'; '.join(issues)}" if issues else "")
            + (f". Warnings: {'; '.join(warnings)}" if warnings else "")
        ),
        details={
            "word_count": word_count,
            "readability": readability,
            "hero_images": len(hero_images),
            "diagrams": len(diagrams),
            "code_examples": len(code_examples),
            "sections": len(sections),
            "invalid_code": invalid_code,
            "score_breakdown": score_components,
            "issues": issues,
            "warnings": warnings,
        },
    )


def validate_publishing_quality(package: dict) -> QualityGateResult:
    """
    Validate publishing package quality.

    Args:
        package: Publishing package dictionary

    Returns:
        QualityGateResult with validation outcome
    """
    if not package.get("success"):
        return QualityGateResult(
            passed=False,
            score=0,
            message=f"Package generation failed: {package.get('error', 'Unknown')}",
            details={"error": package.get("error")},
        )

    package_path = package.get("package_path", "")
    files = package.get("files", {})
    validation = package.get("validation", {})

    required_files = ["article_md", "preview_html", "images_manifest", "metadata", "publishing_guide"]

    issues = []
    warnings = []

    # Check required files
    missing_files = []
    for f in required_files:
        file_path = files.get(f, "")
        if not file_path or not Path(file_path).exists():
            missing_files.append(f)

    if missing_files:
        issues.append(f"Missing files: {', '.join(missing_files)}")

    # Check image validation
    all_accessible = validation.get("all_accessible", False)
    accessible_count = validation.get("accessible_count", 0)
    total_images = validation.get("total", 0)

    if not all_accessible and total_images > 0:
        issues.append(f"Image validation failed: {accessible_count}/{total_images} accessible")

    if total_images < 6:
        warnings.append(f"Only {total_images} images (recommend >= 6)")

    passed = len(issues) == 0

    # Calculate score
    files_present = len(required_files) - len(missing_files)
    image_score = (accessible_count / max(total_images, 1)) * 40 if total_images > 0 else 0
    file_score = (files_present / len(required_files)) * 60
    total_score = int(file_score + image_score)

    return QualityGateResult(
        passed=passed,
        score=total_score,
        message=(
            f"Publishing gate {'PASSED' if passed else 'FAILED'}: "
            f"{files_present}/{len(required_files)} files, "
            f"{accessible_count}/{total_images} images accessible"
            + (f". Issues: {'; '.join(issues)}" if issues else "")
            + (f". Warnings: {'; '.join(warnings)}" if warnings else "")
        ),
        details={
            "package_path": package_path,
            "files_present": files_present,
            "missing_files": missing_files,
            "images_accessible": accessible_count,
            "images_total": total_images,
            "issues": issues,
            "warnings": warnings,
        },
    )


def validate_all_gates(
    research_report: Optional[dict] = None,
    article: Optional[dict] = None,
    package: Optional[dict] = None,
) -> dict:
    """
    Validate all quality gates and return combined result.

    Args:
        research_report: Research report dictionary (optional)
        article: Article dictionary (optional)
        package: Publishing package dictionary (optional)

    Returns:
        Dictionary with validation results for all gates
    """
    results = {}

    if research_report is not None:
        results["research"] = validate_research_quality(research_report)

    if article is not None:
        results["writing"] = validate_writing_quality(article)

    if package is not None:
        results["publishing"] = validate_publishing_quality(package)

    all_passed = all(r.passed for r in results.values())
    total_score = sum(r.score for r in results.values()) / max(len(results), 1)

    return {
        "all_passed": all_passed,
        "average_score": total_score,
        "results": {name: {"passed": r.passed, "score": r.score, "message": r.message}
                    for name, r in results.items()},
    }
