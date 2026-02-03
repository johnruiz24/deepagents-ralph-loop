"""State management for the agent newsletter LangGraph workflow."""

from typing import TypedDict, Optional, Literal


class ArticleState(TypedDict):
    """
    State object for article generation workflow.

    This state is passed between agents in the LangGraph workflow,
    tracking progress through research, writing, and publishing phases.
    """

    # Input
    topic: str
    target_audience: Optional[str]
    key_concepts: list[str]
    desired_depth: Literal["overview", "intermediate", "comprehensive_guide"]

    # Research phase
    research_report: Optional[dict]
    research_quality_score: float
    research_iteration: int

    # Writing phase
    article_content: str
    article_sections: list[dict]
    readability_score: float
    code_validation_results: dict
    generated_images: list[dict]  # [{"type": "hero|diagram|code", "url": str, "description": str}]
    image_generation_status: dict  # {"hero_images": int, "diagrams": int, "code_screenshots": int}
    writing_iteration: int

    # Publishing phase
    article_package_path: str
    publishing_package: Optional[dict]
    publishing_iteration: int

    # Quality gates
    quality_gates_passed: list[str]
    quality_gates_failed: list[str]

    # Workflow control
    iteration_count: int
    current_phase: Literal["research", "writing", "publishing", "complete"]
    error_messages: list[str]
    is_complete: bool


def create_initial_state(
    topic: str,
    target_audience: str = "Senior engineers and architects",
    key_concepts: Optional[list[str]] = None,
    desired_depth: Literal["overview", "intermediate", "comprehensive_guide"] = "comprehensive_guide",
) -> ArticleState:
    """
    Create initial state for a new article generation workflow.

    Args:
        topic: The article topic
        target_audience: Target reader audience
        key_concepts: Key concepts to cover (optional)
        desired_depth: Desired depth of coverage

    Returns:
        Initial ArticleState ready for workflow
    """
    return ArticleState(
        topic=topic,
        target_audience=target_audience,
        key_concepts=key_concepts or [],
        desired_depth=desired_depth,
        research_report=None,
        research_quality_score=0.0,
        research_iteration=0,
        article_content="",
        article_sections=[],
        readability_score=0.0,
        code_validation_results={},
        generated_images=[],
        image_generation_status={
            "hero_images": 0,
            "diagrams": 0,
            "code_screenshots": 0,
        },
        writing_iteration=0,
        article_package_path="",
        publishing_package=None,
        publishing_iteration=0,
        quality_gates_passed=[],
        quality_gates_failed=[],
        iteration_count=0,
        current_phase="research",
        error_messages=[],
        is_complete=False,
    )
