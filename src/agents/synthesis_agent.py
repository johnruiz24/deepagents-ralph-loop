"""
Synthesis & Narrative Agent.

THE MOST CRITICAL AGENT for content quality.
Based on IMPLEMENTATION_GUIDE.md section 3.5.

Responsibilities:
- Read ALL research data + tui_strategy_summary.md
- Identify COUNTERINTUITIVE insights (not just summarize!)
- Structure article following HBR model: Hook → Analysis → Solution/Implication
- Generate draft_article.md (2000-2500 words, 10-minute read)

QUALITY BAR: Harvard Business Review level - NON-NEGOTIABLE!
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.agents.base_agent import LLMAgent
from src.state.shared_state import SharedState
from src.state.newsletter_state import QUALITY_THRESHOLDS
from src.utils.bedrock_config import create_bedrock_llm_for_content


@dataclass
class SynthesisInput:
    """Input for synthesis agent."""
    topic: str
    target_audience: str
    research_data: dict[str, list[dict]]  # subtopic -> articles
    tui_strategy: str
    combined_research_summary: str


@dataclass
class DraftArticle:
    """Draft article output."""
    title: str
    subtitle: str
    content: str
    word_count: int
    sections: list[dict]
    key_insights: list[str]
    counterintuitive_insights: list[str]
    citations: list[dict]
    reading_time_minutes: float


# Multi-stage synthesis prompt
INSIGHT_EXTRACTION_PROMPT = """You are an expert strategic analyst tasked with identifying the MOST IMPORTANT and COUNTERINTUITIVE insights from research data.

## Research Data
{research_data}

## TUI Strategic Context
{tui_context}

## Your Task
Analyze this research and identify:

1. **KEY INSIGHTS** (5-7 insights)
   - The most significant findings that executives MUST know
   - Backed by evidence from the research

2. **COUNTERINTUITIVE INSIGHTS** (2-3 insights) - THIS IS CRITICAL!
   - Findings that challenge conventional wisdom
   - Unexpected connections or implications
   - "Aha moments" that make readers think differently
   - These are what make HBR articles exceptional

3. **TUI-SPECIFIC IMPLICATIONS** (3-5 implications)
   - How does each insight relate to TUI's strategic priorities?
   - What should TUI leadership do differently?

## Output Format
Return a JSON object:
```json
{{
  "key_insights": [
    {{"insight": "...", "evidence": "...", "source": "..."}},
  ],
  "counterintuitive_insights": [
    {{"insight": "...", "why_surprising": "...", "evidence": "..."}},
  ],
  "tui_implications": [
    {{"implication": "...", "strategic_priority": "...", "action": "..."}},
  ]
}}
```

Focus on QUALITY over quantity. Each insight must be substantive and actionable."""


ARTICLE_STRUCTURE_PROMPT = """You are a Harvard Business Review editor creating an article structure.

## Topic
{topic}

## Target Audience
{target_audience}

## Key Insights
{key_insights}

## Counterintuitive Insights (MUST feature prominently!)
{counterintuitive_insights}

## TUI Implications
{tui_implications}

## Article Structure Requirements

Create a detailed outline following the HBR model. Target: 2100 words total.

1. **THE HOOK (Opening)** - 230-270 words
   - Start with a compelling problem or opportunity
   - Make executives immediately see why this matters
   - Preview your counterintuitive insight

2. **CONTEXT SETTING** - 280-320 words
   - Background necessary to understand the topic
   - Current state of play

3. **CORE ANALYSIS** - 900-1000 words (THE MEAT)
   - Present your key insights with evidence
   - Feature the counterintuitive findings prominently
   - Connect to TUI strategic context

4. **STRATEGIC IMPLICATIONS** - 380-420 words
   - What this means for TUI leadership
   - Specific, actionable recommendations

5. **CONCLUSION** - 180-220 words
   - Reinforce the counterintuitive insight
   - Inspiring call to action

## Output Format
Return a JSON outline:
```json
{{
  "title": "Compelling title (60-80 chars)",
  "subtitle": "Elaboration (100-150 chars)",
  "sections": [
    {{
      "name": "The Hook",
      "target_words": 250,
      "key_points": ["point1", "point2"],
      "insight_to_feature": "...",
      "opening_angle": "..."
    }},
  ],
  "total_target_words": 2200
}}
```"""


ARTICLE_WRITING_PROMPT = """You are a Harvard Business Review writer. Your task is to write ONE section of a strategic article.

## Article Context
Title: {title}
Topic: {topic}
Target Audience: {target_audience}

## This Section
Name: {section_name}
MINIMUM Words Required: {target_words}
Key Points to Cover: {key_points}
Insight to Feature: {insight_to_feature}

## Research Context (for evidence)
{research_context}

## TUI Context (for relevance)
{tui_context}

## Writing Guidelines

1. **TONE**: Authoritative but not condescending, sophisticated but accessible
2. **EVIDENCE**: Every claim backed by data or research
3. **SPECIFICITY**: Use concrete examples, numbers, company names
4. **ENGAGEMENT**: Vivid prose, varied sentence structure
5. **TUI RELEVANCE**: Ground insights in TUI's strategic reality

## Word Count Requirements
- Target: {target_words} words (acceptable range: ±15%)
- Maximum: {target_words_plus} words
- Be substantive and insightful

## Content Requirements
- Feature the specified insight prominently
- Include specific data points or examples
- Write for busy executives who scan before reading deeply

Write ONLY this section. No preamble. Start directly with compelling content."""


class SynthesisAgent(LLMAgent[SynthesisInput, DraftArticle]):
    """
    Agent that synthesizes research into a strategic narrative.

    Uses multi-stage process:
    1. Extract key and counterintuitive insights
    2. Create detailed article structure
    3. Write each section individually
    4. Assemble and validate final draft
    """

    agent_name = "SynthesisAgent"
    phase = "synthesis"

    # Word count constraints (NON-NEGOTIABLE!)
    MIN_WORDS = 2000
    MAX_WORDS = 2500
    TARGET_WORDS = 2200

    def __init__(self, shared_state: SharedState, **kwargs):
        super().__init__(shared_state, **kwargs)
        # Use content-optimized LLM
        self._llm = create_bedrock_llm_for_content(max_tokens=8192, temperature=0.7)

    async def read_from_state(self) -> SynthesisInput:
        """Read all research data from state."""
        state = self.shared_state.state

        # Read all research data from files
        research_data = self.shared_state.read_all_research_data()

        # Read TUI strategy summary
        tui_strategy = self.shared_state.read_tui_strategy_summary() or ""

        # Get combined research summary
        combined = state.get("combined_research") or {}
        summary = combined.get("summary", "")

        return SynthesisInput(
            topic=state.get("topic", ""),
            target_audience=state.get("target_audience", "TUI Leadership"),
            research_data=research_data,
            tui_strategy=tui_strategy,
            combined_research_summary=summary,
        )

    async def process(self, input_data: SynthesisInput) -> DraftArticle:
        """
        Multi-stage synthesis process.

        1. Extract insights (key + counterintuitive)
        2. Create article structure
        3. Write sections
        4. Assemble draft
        """
        self.logger.info(
            "Starting synthesis - CRITICAL PHASE",
            topic=input_data.topic,
            research_subtopics=len(input_data.research_data),
        )

        # Stage 1: Extract insights
        self.logger.info("Stage 1: Extracting insights")
        insights = await self._extract_insights(input_data)

        # Stage 2: Create structure
        self.logger.info("Stage 2: Creating article structure")
        structure = await self._create_structure(input_data, insights)

        # Stage 3: Write sections
        self.logger.info("Stage 3: Writing sections")
        sections_content = await self._write_sections(input_data, structure, insights)

        # Stage 4: Assemble draft
        self.logger.info("Stage 4: Assembling draft")
        draft = self._assemble_draft(structure, sections_content, insights)

        self.logger.info(
            "Synthesis complete",
            word_count=draft.word_count,
            counterintuitive_insights=len(draft.counterintuitive_insights),
        )

        return draft

    async def write_to_state(self, output_data: DraftArticle) -> None:
        """Write draft article to state."""
        # Write markdown file
        self.shared_state.write_draft_article(output_data.content)

        # Update state
        self.shared_state.update_state(
            article_content=output_data.content,
            word_count=output_data.word_count,
            article_sections=[
                {"title": s["name"], "word_count": s.get("actual_words", 0)}
                for s in output_data.sections
            ],
            synthesized_content={
                "title": output_data.title,
                "subtitle": output_data.subtitle,
                "key_insights": output_data.key_insights,
                "counterintuitive_insights": output_data.counterintuitive_insights,
            },
        )

    async def validate_output(self, output_data: DraftArticle) -> tuple[bool, str]:
        """Validate draft meets HBR quality requirements."""
        issues = []

        # Word count validation (NON-NEGOTIABLE!)
        if output_data.word_count < self.MIN_WORDS:
            issues.append(f"Too short: {output_data.word_count} words (need >= {self.MIN_WORDS})")
        if output_data.word_count > self.MAX_WORDS:
            issues.append(f"Too long: {output_data.word_count} words (need <= {self.MAX_WORDS})")

        # Counterintuitive insights (ESSENTIAL!)
        if len(output_data.counterintuitive_insights) < 1:
            issues.append("Missing counterintuitive insights (need >= 1)")

        # Sections validation
        if len(output_data.sections) < 4:
            issues.append(f"Only {len(output_data.sections)} sections (need >= 4)")

        # Reading time
        if output_data.reading_time_minutes < 8 or output_data.reading_time_minutes > 12:
            issues.append(f"Reading time {output_data.reading_time_minutes:.1f} min (target: 10 min)")

        if issues:
            return False, f"Draft validation failed: {'; '.join(issues)}"

        return True, f"Draft valid: {output_data.word_count} words, {len(output_data.counterintuitive_insights)} counterintuitive insights"

    async def calculate_quality_score(self, output_data: DraftArticle) -> float:
        """Calculate quality score for draft."""
        score = 0.0

        # Word count in range (30 points)
        if self.MIN_WORDS <= output_data.word_count <= self.MAX_WORDS:
            score += 30.0
        elif output_data.word_count > self.MIN_WORDS * 0.9:
            score += 20.0

        # Counterintuitive insights (25 points)
        insight_score = min(25.0, len(output_data.counterintuitive_insights) * 12.5)
        score += insight_score

        # Section structure (20 points)
        if len(output_data.sections) >= 5:
            score += 20.0
        elif len(output_data.sections) >= 4:
            score += 15.0

        # Key insights (15 points)
        key_insight_score = min(15.0, len(output_data.key_insights) * 3)
        score += key_insight_score

        # Title and subtitle (10 points)
        if output_data.title and output_data.subtitle:
            score += 10.0

        return min(100.0, score)

    async def _extract_insights(self, input_data: SynthesisInput) -> dict:
        """Extract key and counterintuitive insights from research."""
        # Prepare research data for prompt
        research_text = self._format_research_for_prompt(input_data.research_data)

        prompt = INSIGHT_EXTRACTION_PROMPT.format(
            research_data=research_text[:30000],  # Limit context
            tui_context=input_data.tui_strategy[:10000],
        )

        response = await self.invoke_llm(prompt)
        return self._parse_insights_response(response)

    async def _create_structure(self, input_data: SynthesisInput, insights: dict) -> dict:
        """Create detailed article structure."""
        prompt = ARTICLE_STRUCTURE_PROMPT.format(
            topic=input_data.topic,
            target_audience=input_data.target_audience,
            key_insights=self._format_insights_list(insights.get("key_insights", [])),
            counterintuitive_insights=self._format_insights_list(insights.get("counterintuitive_insights", [])),
            tui_implications=self._format_insights_list(insights.get("tui_implications", [])),
        )

        response = await self.invoke_llm(prompt)
        return self._parse_structure_response(response, input_data.topic)

    async def _write_sections(self, input_data: SynthesisInput, structure: dict, insights: dict) -> list[dict]:
        """Write each section of the article."""
        sections_content = []
        total_words = 0

        for section in structure.get("sections", []):
            self.logger.debug(f"Writing section: {section.get('name', 'Unknown')}")

            target_words = section.get("target_words", 300)

            prompt = ARTICLE_WRITING_PROMPT.format(
                title=structure.get("title", input_data.topic),
                topic=input_data.topic,
                target_audience=input_data.target_audience,
                section_name=section.get("name", ""),
                target_words=target_words,
                target_words_plus=int(target_words * 1.1),
                key_points="\n".join(f"- {p}" for p in section.get("key_points", [])),
                insight_to_feature=section.get("insight_to_feature", ""),
                research_context=self._get_relevant_research(input_data.research_data, section),
                tui_context=input_data.tui_strategy[:3000],
            )

            content = await self.invoke_llm(prompt)
            actual_words = len(content.split())
            total_words += actual_words

            sections_content.append({
                "name": section.get("name", ""),
                "content": content.strip(),
                "actual_words": actual_words,
                "target_words": target_words,
            })

        self.logger.info(f"All sections written: {total_words} total words")
        return sections_content

    def _assemble_draft(self, structure: dict, sections_content: list[dict], insights: dict) -> DraftArticle:
        """Assemble the final draft from sections."""
        title = structure.get("title", "Strategic Analysis")
        subtitle = structure.get("subtitle", "")

        # Assemble content
        content_parts = [
            f"# {title}",
            f"*{subtitle}*" if subtitle else "",
            "",
        ]

        for section in sections_content:
            content_parts.append(f"## {section['name']}")
            content_parts.append(section['content'])
            content_parts.append("")

        full_content = "\n".join(content_parts)
        word_count = len(full_content.split())

        # Extract key insights
        key_insights = [i.get("insight", "") for i in insights.get("key_insights", [])]
        counterintuitive = [i.get("insight", "") for i in insights.get("counterintuitive_insights", [])]

        return DraftArticle(
            title=title,
            subtitle=subtitle,
            content=full_content,
            word_count=word_count,
            sections=sections_content,
            key_insights=key_insights,
            counterintuitive_insights=counterintuitive,
            citations=[],  # Will be added by editor
            reading_time_minutes=word_count / 200,  # ~200 words per minute
        )

    def _format_research_for_prompt(self, research_data: dict[str, list[dict]]) -> str:
        """Format research data for LLM prompt."""
        parts = []
        for subtopic, articles in research_data.items():
            parts.append(f"\n### {subtopic}")
            for article in articles[:3]:  # Limit articles per subtopic
                content = article.get("content", "")[:3000]  # Limit content
                parts.append(f"\n**{article.get('filename', 'Article')}**\n{content}\n")
        return "\n".join(parts)

    def _format_insights_list(self, insights: list) -> str:
        """Format insights list for prompt."""
        if not insights:
            return "None identified"

        lines = []
        for i, insight in enumerate(insights, 1):
            if isinstance(insight, dict):
                text = insight.get("insight", str(insight))
            else:
                text = str(insight)
            lines.append(f"{i}. {text}")
        return "\n".join(lines)

    def _get_relevant_research(self, research_data: dict, section: dict) -> str:
        """Get research relevant to a specific section."""
        # Simple implementation - return sample from all research
        parts = []
        for subtopic, articles in research_data.items():
            if articles:
                content = articles[0].get("content", "")[:1500]
                parts.append(f"From {subtopic}:\n{content}")
        return "\n\n".join(parts[:2])

    def _parse_insights_response(self, response: str) -> dict:
        """Parse LLM insights response."""
        import json
        try:
            # Extract JSON from response
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response)
        except (json.JSONDecodeError, IndexError):
            # Fallback
            return {
                "key_insights": [{"insight": "Key insight from research", "evidence": "Research data"}],
                "counterintuitive_insights": [{"insight": "Counterintuitive finding", "why_surprising": "Challenges convention"}],
                "tui_implications": [{"implication": "Strategic implication for TUI"}],
            }

    def _parse_structure_response(self, response: str, topic: str) -> dict:
        """Parse LLM structure response."""
        import json
        try:
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response)
        except (json.JSONDecodeError, IndexError):
            # Fallback structure targeting ~2100 words
            return {
                "title": f"Strategic Analysis: {topic}",
                "subtitle": "Insights for TUI Leadership",
                "sections": [
                    {"name": "The Hook", "target_words": 250, "key_points": ["Opening problem", "Why this matters now"], "insight_to_feature": ""},
                    {"name": "Context and Background", "target_words": 300, "key_points": ["Market context", "Current challenges"], "insight_to_feature": ""},
                    {"name": "Core Analysis", "target_words": 950, "key_points": ["Key insight", "Counterintuitive finding", "Evidence", "Examples"], "insight_to_feature": ""},
                    {"name": "Strategic Implications for TUI", "target_words": 400, "key_points": ["Recommendations", "Action items", "Priorities"], "insight_to_feature": ""},
                    {"name": "Conclusion", "target_words": 200, "key_points": ["Key takeaway", "Call to action"], "insight_to_feature": ""},
                ],
            }


def create_synthesis_agent(shared_state: SharedState) -> SynthesisAgent:
    """Factory function to create SynthesisAgent."""
    return SynthesisAgent(shared_state)
