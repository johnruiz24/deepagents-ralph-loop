"""
HBR Content Processor.

Generates HBR-specific structural elements:
- "Idea in Brief" sidebar (Problem/Argument/Solution)
- Pull quotes extraction
- Author byline

Based on hbr-article-standards skill guidelines.
"""

import json
from dataclasses import dataclass
from typing import Optional

from src.utils.bedrock_config import create_bedrock_llm
from src.utils.logging import get_agent_logger


@dataclass
class IdeaInBrief:
    """HBR 'Idea in Brief' sidebar content."""
    problem: str
    argument: str
    solution: str


@dataclass
class HBRContent:
    """HBR structural elements."""
    idea_in_brief: IdeaInBrief
    pull_quotes: list[str]
    author_name: str
    author_credentials: str


logger = get_agent_logger("HBRContentProcessor", "content")


async def generate_idea_in_brief(article_text: str) -> IdeaInBrief:
    """
    Generate HBR 'Idea in Brief' sidebar from article content.

    Uses LLM to extract:
    - The Problem: What business challenge is addressed?
    - The Argument: What is the core counterintuitive insight?
    - The Solution: What are the key actions/takeaways?

    Total: 100-150 words across all three parts.
    """
    llm = create_bedrock_llm(model_preset="haiku", temperature=0.3)

    prompt = f"""Analyze this article and create an HBR-style "Idea in Brief" sidebar.

ARTICLE:
{article_text[:8000]}

Generate exactly 3 parts (total 100-150 words):

1. THE PROBLEM (30-50 words): What is the business challenge or strategic question this article addresses? Be specific about the tension or dilemma.

2. THE ARGUMENT (40-60 words): What is the author's core insight? This should be somewhat counterintuitive - challenging conventional wisdom.

3. THE SOLUTION (30-50 words): What are the key actions or strategic takeaways for leaders?

Return ONLY valid JSON:
{{"problem": "...", "argument": "...", "solution": "..."}}
"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        # Extract JSON from response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            data = json.loads(content[json_start:json_end])
            return IdeaInBrief(
                problem=data.get("problem", ""),
                argument=data.get("argument", ""),
                solution=data.get("solution", ""),
            )
    except Exception as e:
        logger.warning(f"Failed to generate Idea in Brief: {e}")

    # Fallback
    return IdeaInBrief(
        problem="Organizations face critical decisions about technology adoption and strategic positioning.",
        argument="Success requires balancing innovation with operational excellence.",
        solution="Leaders must act decisively while maintaining flexibility for market changes.",
    )


async def extract_pull_quotes(article_text: str) -> list[str]:
    """
    Extract 2-3 impactful pull quotes from the article.

    Pull quotes are short, provocative sentences that:
    - Capture key insights
    - Are visually striking when displayed large
    - Work out of context
    """
    llm = create_bedrock_llm(model_preset="haiku", temperature=0.3)

    prompt = f"""Extract 2-3 powerful pull quotes from this article.

ARTICLE:
{article_text[:8000]}

CRITERIA for good pull quotes:
- Short (10-25 words max)
- Provocative or surprising
- Self-contained (works without context)
- Captures a key insight
- Would look impactful displayed in large font

Return ONLY valid JSON array:
["quote 1", "quote 2", "quote 3"]
"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        # Extract JSON array from response
        json_start = content.find('[')
        json_end = content.rfind(']') + 1
        if json_start >= 0 and json_end > json_start:
            quotes = json.loads(content[json_start:json_end])
            # Ensure we have 2-3 quotes
            return quotes[:3] if len(quotes) > 3 else quotes
    except Exception as e:
        logger.warning(f"Failed to extract pull quotes: {e}")

    # Fallback
    return [
        "The biggest risk isn't failing to adopt AI—it's over-automating the human experiences that customers value most.",
        "In a world of algorithmic sameness, human judgment becomes the ultimate competitive advantage.",
    ]


async def generate_hbr_content(
    article_text: str,
    author_name: str = "TUI Strategy Group",
    author_credentials: str = "Specialists in travel industry transformation and competitive strategy."
) -> HBRContent:
    """
    Generate all HBR structural elements for an article.

    Args:
        article_text: The full article content
        author_name: Author/team name for byline
        author_credentials: Short description of author expertise

    Returns:
        HBRContent with idea_in_brief, pull_quotes, and author info
    """
    idea_in_brief = await generate_idea_in_brief(article_text)
    pull_quotes = await extract_pull_quotes(article_text)

    return HBRContent(
        idea_in_brief=idea_in_brief,
        pull_quotes=pull_quotes,
        author_name=author_name,
        author_credentials=author_credentials,
    )


def format_idea_in_brief_html(idea: IdeaInBrief) -> str:
    """Format Idea in Brief as HTML sidebar."""
    return f"""
    <aside class="idea-in-brief">
        <h3>Idea in Brief</h3>
        <div class="iib-section">
            <h4>THE PROBLEM</h4>
            <p>{idea.problem}</p>
        </div>
        <div class="iib-section">
            <h4>THE ARGUMENT</h4>
            <p>{idea.argument}</p>
        </div>
        <div class="iib-section">
            <h4>THE SOLUTION</h4>
            <p>{idea.solution}</p>
        </div>
    </aside>
    """


def format_pull_quotes_html(quotes: list[str]) -> str:
    """Format pull quotes as HTML."""
    if not quotes:
        return ""

    quotes_html = ""
    for quote in quotes:
        quotes_html += f"""
        <blockquote class="pull-quote">
            "{quote}"
        </blockquote>
        """
    return quotes_html


def format_author_byline_html(name: str, credentials: str) -> str:
    """Format author byline as HTML."""
    return f"""
    <div class="author-byline">
        <p class="author-name">by <strong>{name}</strong></p>
        <p class="author-credentials">{credentials}</p>
    </div>
    """
