"""Configuration module for the newsletter agent system."""

from src.config.sources import (
    Source,
    SourceCategory,
    SourceCredibility,
    MASTER_SOURCE_LIST,
    get_sources_by_category,
    get_sources_by_relevance,
    get_tui_source,
    TOPIC_CATEGORY_MAPPING,
)

__all__ = [
    "Source",
    "SourceCategory",
    "SourceCredibility",
    "MASTER_SOURCE_LIST",
    "get_sources_by_category",
    "get_sources_by_relevance",
    "get_tui_source",
    "TOPIC_CATEGORY_MAPPING",
]
