"""
Master Source List for the newsletter research pipeline.

Based on IMPLEMENTATION_GUIDE.md section 4.1.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SourceCategory(str, Enum):
    """Categories of sources for research."""
    TECHNOLOGY_RESEARCH = "technology_research"
    TRAVEL_INDUSTRY = "travel_industry"
    BIG_TECH = "big_tech"
    VENTURE_CAPITAL = "venture_capital"
    TRAVEL_INNOVATION = "travel_innovation"
    CONSULTANCIES = "consultancies"
    TUI_SPECIFIC = "tui_specific"


class SourceCredibility(str, Enum):
    """Credibility levels for sources."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Source:
    """A research source configuration."""
    name: str
    url: str
    category: SourceCategory
    credibility: SourceCredibility
    relevance_keywords: list[str] = field(default_factory=list)
    search_prefix: Optional[str] = None  # For site-specific searches


# Master Source List from IMPLEMENTATION_GUIDE.md
MASTER_SOURCE_LIST: list[Source] = [
    # Technology Research
    Source(
        name="MIT Technology Review",
        url="https://www.technologyreview.com/",
        category=SourceCategory.TECHNOLOGY_RESEARCH,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["ai", "technology", "innovation", "research", "emerging tech"],
        search_prefix="site:technologyreview.com",
    ),
    Source(
        name="Deep Learning AI (The Batch)",
        url="https://www.deeplearning.ai/the-batch/",
        category=SourceCategory.TECHNOLOGY_RESEARCH,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["ai", "ml", "deep learning", "neural networks", "agentic"],
        search_prefix="site:deeplearning.ai",
    ),

    # Travel Industry
    Source(
        name="Skift",
        url="https://skift.com/",
        category=SourceCategory.TRAVEL_INDUSTRY,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["travel", "hospitality", "tourism", "airlines", "hotels", "ota"],
        search_prefix="site:skift.com",
    ),
    Source(
        name="Phocuswire",
        url="https://www.phocuswire.com/",
        category=SourceCategory.TRAVEL_INDUSTRY,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["travel tech", "hospitality", "booking", "ota", "travel innovation"],
        search_prefix="site:phocuswire.com",
    ),

    # Big Tech
    Source(
        name="Google AI Blog",
        url="https://ai.googleblog.com/",
        category=SourceCategory.BIG_TECH,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["google", "ai", "machine learning", "gemini", "agents"],
        search_prefix="site:ai.googleblog.com OR site:blog.google/technology",
    ),
    Source(
        name="AWS Blog",
        url="https://aws.amazon.com/blogs/",
        category=SourceCategory.BIG_TECH,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["aws", "cloud", "bedrock", "ai services", "serverless"],
        search_prefix="site:aws.amazon.com/blogs",
    ),
    Source(
        name="Microsoft Research",
        url="https://www.microsoft.com/en-us/research/",
        category=SourceCategory.BIG_TECH,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["microsoft", "azure", "ai", "research", "copilot"],
        search_prefix="site:microsoft.com/research",
    ),
    Source(
        name="Meta AI",
        url="https://ai.meta.com/",
        category=SourceCategory.BIG_TECH,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["meta", "llama", "ai research", "open source ai"],
        search_prefix="site:ai.meta.com",
    ),
    Source(
        name="Anthropic",
        url="https://www.anthropic.com/",
        category=SourceCategory.BIG_TECH,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["claude", "anthropic", "ai safety", "constitutional ai", "mcp"],
        search_prefix="site:anthropic.com",
    ),
    Source(
        name="OpenAI",
        url="https://openai.com/",
        category=SourceCategory.BIG_TECH,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["openai", "gpt", "chatgpt", "ai agents", "assistants api"],
        search_prefix="site:openai.com",
    ),

    # Venture Capital
    Source(
        name="Sequoia Capital",
        url="https://www.sequoiacap.com/",
        category=SourceCategory.VENTURE_CAPITAL,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["venture capital", "investment", "startups", "ai companies"],
        search_prefix="site:sequoiacap.com",
    ),
    Source(
        name="Softbank Vision Fund",
        url="https://visionfund.com/",
        category=SourceCategory.VENTURE_CAPITAL,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["softbank", "investment", "ai portfolio", "tech investment"],
        search_prefix="site:visionfund.com",
    ),
    Source(
        name="Andreessen Horowitz (a16z)",
        url="https://a16z.com/",
        category=SourceCategory.VENTURE_CAPITAL,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["a16z", "venture capital", "ai investment", "tech trends"],
        search_prefix="site:a16z.com",
    ),
    Source(
        name="TechCrunch",
        url="https://techcrunch.com/",
        category=SourceCategory.VENTURE_CAPITAL,
        credibility=SourceCredibility.MEDIUM,
        relevance_keywords=["startups", "funding", "tech news", "ai startups"],
        search_prefix="site:techcrunch.com",
    ),

    # Travel Innovation
    Source(
        name="Lufthansa Innovation Hub",
        url="https://lh-innovationhub.de/",
        category=SourceCategory.TRAVEL_INNOVATION,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["aviation", "travel innovation", "airlines", "digital travel"],
        search_prefix="site:lh-innovationhub.de",
    ),
    Source(
        name="Booking.com Corporate",
        url="https://www.booking.com/",
        category=SourceCategory.TRAVEL_INNOVATION,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["booking", "ota", "travel tech", "accommodation"],
        search_prefix="site:booking.com OR site:news.booking.com",
    ),
    Source(
        name="Expedia Group",
        url="https://www.expediagroup.com/",
        category=SourceCategory.TRAVEL_INNOVATION,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["expedia", "ota", "travel platform", "vrbo"],
        search_prefix="site:expediagroup.com",
    ),
    Source(
        name="Trip.com Group",
        url="https://www.trip.com/",
        category=SourceCategory.TRAVEL_INNOVATION,
        credibility=SourceCredibility.MEDIUM,
        relevance_keywords=["ctrip", "chinese travel", "ota", "asia travel"],
        search_prefix="site:trip.com",
    ),

    # Consultancies
    Source(
        name="McKinsey Insights",
        url="https://www.mckinsey.com/insights",
        category=SourceCategory.CONSULTANCIES,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["strategy", "digital transformation", "ai adoption", "business"],
        search_prefix="site:mckinsey.com",
    ),
    Source(
        name="Accenture Research",
        url="https://www.accenture.com/us-en/insights",
        category=SourceCategory.CONSULTANCIES,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["digital", "technology", "consulting", "transformation"],
        search_prefix="site:accenture.com",
    ),
    Source(
        name="Deloitte Insights",
        url="https://www2.deloitte.com/insights",
        category=SourceCategory.CONSULTANCIES,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["business", "technology", "trends", "industry analysis"],
        search_prefix="site:deloitte.com",
    ),
    Source(
        name="BCG",
        url="https://www.bcg.com/",
        category=SourceCategory.CONSULTANCIES,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["strategy", "digital", "ai transformation", "business"],
        search_prefix="site:bcg.com",
    ),
    Source(
        name="Gartner",
        url="https://www.gartner.com/",
        category=SourceCategory.CONSULTANCIES,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["technology trends", "hype cycle", "market analysis", "it"],
        search_prefix="site:gartner.com",
    ),

    # TUI Specific (MANDATORY)
    Source(
        name="TUI Group Investor Relations",
        url="https://www.tuigroup.com/en/investors",
        category=SourceCategory.TUI_SPECIFIC,
        credibility=SourceCredibility.HIGH,
        relevance_keywords=["tui", "travel", "strategy", "investor", "annual report"],
        search_prefix="site:tuigroup.com",
    ),
]


def get_sources_by_category(category: SourceCategory) -> list[Source]:
    """Get all sources for a specific category."""
    return [s for s in MASTER_SOURCE_LIST if s.category == category]


def get_sources_by_relevance(keywords: list[str], min_credibility: SourceCredibility = SourceCredibility.MEDIUM) -> list[Source]:
    """
    Get sources relevant to the given keywords.

    Args:
        keywords: Keywords to match against source relevance keywords
        min_credibility: Minimum credibility level

    Returns:
        List of relevant sources sorted by credibility
    """
    credibility_order = {
        SourceCredibility.HIGH: 3,
        SourceCredibility.MEDIUM: 2,
        SourceCredibility.LOW: 1,
    }

    min_cred_value = credibility_order[min_credibility]
    keywords_lower = [k.lower() for k in keywords]

    relevant = []
    for source in MASTER_SOURCE_LIST:
        # Check credibility
        if credibility_order[source.credibility] < min_cred_value:
            continue

        # Check keyword relevance
        source_keywords = [k.lower() for k in source.relevance_keywords]
        if any(kw in " ".join(source_keywords) for kw in keywords_lower):
            relevant.append(source)
        elif any(sk in " ".join(keywords_lower) for sk in source_keywords):
            relevant.append(source)

    # Sort by credibility (high first)
    relevant.sort(key=lambda s: credibility_order[s.credibility], reverse=True)

    return relevant


def get_tui_source() -> Source:
    """Get the mandatory TUI source."""
    for source in MASTER_SOURCE_LIST:
        if source.category == SourceCategory.TUI_SPECIFIC:
            return source
    raise ValueError("TUI source not found in master list!")


# Topic to category mapping for automatic source selection
TOPIC_CATEGORY_MAPPING: dict[str, list[SourceCategory]] = {
    "ai": [SourceCategory.TECHNOLOGY_RESEARCH, SourceCategory.BIG_TECH],
    "agentic": [SourceCategory.TECHNOLOGY_RESEARCH, SourceCategory.BIG_TECH],
    "travel": [SourceCategory.TRAVEL_INDUSTRY, SourceCategory.TRAVEL_INNOVATION],
    "commerce": [SourceCategory.BIG_TECH, SourceCategory.TECHNOLOGY_RESEARCH],
    "protocol": [SourceCategory.BIG_TECH, SourceCategory.TECHNOLOGY_RESEARCH],
    "investment": [SourceCategory.VENTURE_CAPITAL],
    "strategy": [SourceCategory.CONSULTANCIES],
    "digital transformation": [SourceCategory.CONSULTANCIES, SourceCategory.BIG_TECH],
    "ota": [SourceCategory.TRAVEL_INDUSTRY, SourceCategory.TRAVEL_INNOVATION],
    "booking": [SourceCategory.TRAVEL_INNOVATION, SourceCategory.TRAVEL_INDUSTRY],
}
