"""State management for the newsletter system."""

from src.state.newsletter_state import (
    NewsletterState,
    create_initial_newsletter_state,
    QUALITY_THRESHOLDS,
)

# Legacy import for backwards compatibility
from src.state.article_state import ArticleState, create_initial_state

__all__ = [
    "NewsletterState",
    "create_initial_newsletter_state",
    "QUALITY_THRESHOLDS",
    "ArticleState",
    "create_initial_state",
]
