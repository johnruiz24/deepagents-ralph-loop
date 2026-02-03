"""Expanded state management for the 9-agent newsletter system."""

from typing import TypedDict, Optional, Literal


class NewsletterState(TypedDict):
    """
    State object for the 9-agent newsletter generation workflow.

    This state is passed between agents in the LangGraph workflow,
    tracking progress through all phases: research, TUI analysis,
    content creation, multimedia, and assembly.
    """

    # ============== INPUT ==============
    topic: str
    target_audience: Optional[str]
    key_concepts: list[str]
    sub_topics: list[dict]  # From Query Formulation Agent
    desired_depth: Literal["overview", "intermediate", "comprehensive_guide"]

    # ============== PHASE 1: QUERY FORMULATION ==============
    research_plan: Optional[dict]  # {"sub_topics": [...], "sources_strategy": {...}}
    query_formulation_iteration: int

    # ============== PHASE 2: PARALLELIZED RESEARCH ==============
    research_results: list[dict]  # Results from parallel sub-agents
    combined_research: Optional[dict]  # Merged research report
    research_quality_score: float
    research_iteration: int

    # ============== PHASE 3: TUI STRATEGY ANALYSIS (MANDATORY) ==============
    tui_analysis: Optional[dict]  # TUI strategic context
    tui_strategic_priorities: list[str]
    tui_relevance_score: float
    tui_iteration: int

    # ============== PHASE 4: SYNTHESIS & NARRATIVE ==============
    synthesized_content: Optional[dict]  # Structured narrative
    narrative_outline: list[dict]  # Section-by-section plan
    synthesis_iteration: int

    # ============== PHASE 5: HBR STYLE EDITOR ==============
    article_content: str  # Final article text
    article_sections: list[dict]
    word_count: int  # MUST be 2000-2500
    readability_score: float
    hbr_quality_score: float  # Editorial quality
    editing_iteration: int

    # ============== PHASE 6: VISUAL ASSETS ==============
    generated_images: list[dict]  # {"type": "hero|diagram|chart", "path": str, "description": str}
    hero_images: list[dict]
    diagrams: list[dict]
    charts: list[dict]
    visual_quality_score: float
    visual_iteration: int

    # ============== PHASE 7: MULTIMEDIA (AUDIO + VIDEO) ==============
    # Audio
    audio_script: str
    audio_path: Optional[str]
    audio_duration_seconds: float
    audio_quality_score: float

    # Video
    video_script: str
    video_path: Optional[str]
    video_duration_seconds: float  # MUST be 60 ± 2 seconds
    video_quality_score: float

    multimedia_iteration: int

    # ============== PHASE 8: FINAL ASSEMBLY ==============
    article_package_path: str
    pdf_path: Optional[str]
    html_path: Optional[str]
    archive_path: Optional[str]
    publishing_package: Optional[dict]
    assembly_iteration: int

    # ============== QUALITY GATES ==============
    quality_gates_passed: list[str]
    quality_gates_failed: list[str]

    # ============== WORKFLOW CONTROL ==============
    iteration_count: int
    current_phase: Literal[
        "query_formulation",
        "research",
        "tui_analysis",
        "synthesis",
        "editing",
        "visuals",
        "multimedia",
        "assembly",
        "complete",
    ]
    error_messages: list[str]
    is_complete: bool


def create_initial_newsletter_state(
    topic: str,
    target_audience: str = "TUI Leadership and Strategy Teams",
    key_concepts: Optional[list[str]] = None,
    desired_depth: Literal["overview", "intermediate", "comprehensive_guide"] = "comprehensive_guide",
) -> NewsletterState:
    """
    Create initial state for a new newsletter generation workflow.

    Args:
        topic: The newsletter topic
        target_audience: Target reader audience (default: TUI Leadership)
        key_concepts: Key concepts to cover (optional)
        desired_depth: Desired depth of coverage

    Returns:
        Initial NewsletterState ready for workflow
    """
    return NewsletterState(
        # Input
        topic=topic,
        target_audience=target_audience,
        key_concepts=key_concepts or [],
        sub_topics=[],
        desired_depth=desired_depth,

        # Phase 1: Query Formulation
        research_plan=None,
        query_formulation_iteration=0,

        # Phase 2: Parallelized Research
        research_results=[],
        combined_research=None,
        research_quality_score=0.0,
        research_iteration=0,

        # Phase 3: TUI Strategy Analysis
        tui_analysis=None,
        tui_strategic_priorities=[],
        tui_relevance_score=0.0,
        tui_iteration=0,

        # Phase 4: Synthesis
        synthesized_content=None,
        narrative_outline=[],
        synthesis_iteration=0,

        # Phase 5: HBR Style Editor
        article_content="",
        article_sections=[],
        word_count=0,
        readability_score=0.0,
        hbr_quality_score=0.0,
        editing_iteration=0,

        # Phase 6: Visual Assets
        generated_images=[],
        hero_images=[],
        diagrams=[],
        charts=[],
        visual_quality_score=0.0,
        visual_iteration=0,

        # Phase 7: Multimedia
        audio_script="",
        audio_path=None,
        audio_duration_seconds=0.0,
        audio_quality_score=0.0,
        video_script="",
        video_path=None,
        video_duration_seconds=0.0,
        video_quality_score=0.0,
        multimedia_iteration=0,

        # Phase 8: Assembly
        article_package_path="",
        pdf_path=None,
        html_path=None,
        archive_path=None,
        publishing_package=None,
        assembly_iteration=0,

        # Quality Gates
        quality_gates_passed=[],
        quality_gates_failed=[],

        # Workflow Control
        iteration_count=0,
        current_phase="query_formulation",
        error_messages=[],
        is_complete=False,
    )


# Quality thresholds (NON-NEGOTIABLE from lessons.md)
QUALITY_THRESHOLDS = {
    "research_quality_min": 85,
    "source_count_min": 5,
    "article_word_count_min": 2000,
    "article_word_count_max": 2500,
    "readability_min": 60,
    "hbr_quality_min": 85,
    "video_duration_target": 60,
    "video_duration_tolerance": 2,
    "max_iterations_per_phase": 3,
}
