"""Research quality gate validator."""


def validate_research(report: dict) -> tuple[bool, list[str]]:
    """
    Validate research quality against requirements.

    Args:
        report: Research report from Research Agent

    Returns:
        Tuple of (passed: bool, issues: list[str])
    """
    issues = []

    # Check quality score
    quality_score = report.get("quality_score", 0.0)
    if quality_score < 85.0:
        issues.append(f"Quality score {quality_score:.1f} below threshold of 85.0")

    # Check source count
    sources = report.get("sources", [])
    if len(sources) < 5:
        issues.append(f"Only {len(sources)} sources found, need at least 5")

    # Check source credibility
    high_cred_sources = [s for s in sources if s.get("credibility") == "high"]
    if len(high_cred_sources) < 2:
        issues.append(f"Only {len(high_cred_sources)} high-credibility sources, need at least 2")

    # Check key findings
    key_findings = report.get("key_findings", [])
    if len(key_findings) < 8:
        issues.append(f"Only {len(key_findings)} key findings, need at least 8")

    # Check technical concepts
    technical_concepts = report.get("technical_concepts", [])
    if len(technical_concepts) < 5:
        issues.append(f"Only {len(technical_concepts)} technical concepts identified, need at least 5")

    passed = len(issues) == 0
    return passed, issues


def calculate_research_quality_score(
    sources: list[dict],
    key_findings: list[str],
    technical_concepts: list[str],
    llm_assessment: float = 0.0,
) -> float:
    """
    Calculate overall research quality score.

    Args:
        sources: List of sources with credibility ratings
        key_findings: List of key findings extracted
        technical_concepts: List of technical concepts identified
        llm_assessment: LLM's qualitative assessment (0-100)

    Returns:
        Quality score (0-100)
    """
    # Count sources by credibility
    high_cred = len([s for s in sources if s.get("credibility") == "high"])
    medium_cred = len([s for s in sources if s.get("credibility") == "medium"])
    total_sources = len(sources)

    # Source quality component (40 points max)
    # High credibility sources worth 15 points each, medium worth 8
    source_quality = min(100, (high_cred * 15 + medium_cred * 8 + total_sources * 2))

    # Depth component (30 points max)
    # Based on key findings and technical concepts
    depth_score = min(100, (len(key_findings) * 2 + len(technical_concepts) * 3))

    # Combine with LLM assessment (30 points max)
    llm_quality = llm_assessment * 0.6

    # Final weighted score
    final_quality = (source_quality * 0.4 + depth_score * 0.3 + llm_quality * 0.3)

    return round(final_quality, 1)
