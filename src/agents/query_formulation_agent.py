"""
Query Formulation & Research Strategy Agent.

Transforms user prompts into structured, actionable research plans.
Based on IMPLEMENTATION_GUIDE.md section 3.2.

Responsibilities:
- Analyze input topic and decompose into sub-questions
- Filter sources from Master Source List by relevance
- Generate optimized search queries with temporal qualifiers
- Output structured research_plan.json
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.agents.base_agent import LLMAgent, AgentResult
from src.state.shared_state import SharedState
from src.config.sources import (
    Source,
    SourceCategory,
    MASTER_SOURCE_LIST,
    get_sources_by_relevance,
    get_tui_source,
    TOPIC_CATEGORY_MAPPING,
)
from src.utils.logging import AgentLogger


@dataclass
class QueryFormulationInput:
    """Input for the Query Formulation Agent."""
    topic: str
    key_concepts: list[str]
    sub_topics: list[dict]
    target_audience: str


@dataclass
class SubTopicPlan:
    """Research plan for a single sub-topic."""
    sub_topic: str
    queries: list[str]
    sources: list[str]
    focus_areas: list[str]


@dataclass
class ResearchPlan:
    """Complete research plan output."""
    main_topic: str
    target_audience: str
    sub_topic_plans: list[SubTopicPlan]
    tui_source: str  # Always included
    total_sources: int
    generated_at: str


QUERY_FORMULATION_PROMPT = """You are an expert research strategist. Your task is to create a comprehensive research plan.

## Input
Topic: {topic}
Target Audience: {target_audience}
Key Concepts: {key_concepts}
Sub-topics to research: {sub_topics}

## Available Sources
{available_sources}

## Your Task
For EACH sub-topic, create:
1. 3-5 optimized search queries
2. Select 3-5 most relevant sources from the available list
3. Identify 2-3 specific focus areas

## Query Optimization Rules
- Include temporal qualifiers (e.g., "2025", "2026")
- Use domain-specific terminology
- Be specific, not broad
- For site-specific searches, use format: "site:example.com query terms"

## Output Format
Return a JSON object with this EXACT structure:
```json
{{
  "sub_topic_plans": [
    {{
      "sub_topic": "Technical architecture of UCP",
      "queries": [
        "Universal Commerce Protocol technical specification 2025",
        "site:phocuswire.com UCP architecture agentic AI",
        "Model Context Protocol commerce integration"
      ],
      "sources": ["Phocuswire", "Google AI Blog", "MIT Technology Review"],
      "focus_areas": ["API design patterns", "Protocol specifications", "Integration architecture"]
    }}
  ]
}}
```

Generate the research plan now. Return ONLY valid JSON, no markdown code blocks."""


class QueryFormulationAgent(LLMAgent[QueryFormulationInput, ResearchPlan]):
    """
    Agent that formulates research queries and strategies.

    Takes a topic and key concepts, produces a structured research plan
    with optimized queries and source selection.
    """

    agent_name = "QueryFormulationAgent"
    phase = "query_formulation"

    async def read_from_state(self) -> QueryFormulationInput:
        """Read input from shared state."""
        state = self.shared_state.state

        topic = state.get("topic", "")
        if not topic:
            raise ValueError("Topic is required for query formulation")

        # Get sub_topics from state or generate from key_concepts
        sub_topics = state.get("sub_topics", [])
        if not sub_topics and state.get("key_concepts"):
            # Generate sub_topics from key concepts if not provided
            sub_topics = [
                {"name": concept, "description": f"Research on {concept}"}
                for concept in state["key_concepts"]
            ]

        return QueryFormulationInput(
            topic=topic,
            key_concepts=state.get("key_concepts", []),
            sub_topics=sub_topics,
            target_audience=state.get("target_audience", "TUI Leadership and Strategy Teams"),
        )

    async def process(self, input_data: QueryFormulationInput) -> ResearchPlan:
        """
        Process input and generate research plan.

        Steps:
        1. Identify relevant sources based on topic keywords
        2. Use LLM to generate optimized queries and sub-topic plans
        3. Structure the research plan
        """
        self.logger.info(
            "Starting query formulation",
            topic=input_data.topic,
            num_subtopics=len(input_data.sub_topics),
        )

        # Step 1: Get relevant sources based on topic and concepts
        all_keywords = [input_data.topic.lower()] + [c.lower() for c in input_data.key_concepts]
        relevant_sources = get_sources_by_relevance(all_keywords)

        # Always include TUI source
        tui_source = get_tui_source()
        if tui_source not in relevant_sources:
            relevant_sources.insert(0, tui_source)

        # Format sources for prompt
        sources_text = self._format_sources_for_prompt(relevant_sources)

        # Format sub-topics
        sub_topics_text = json.dumps(
            [{"name": st.get("name", st), "description": st.get("description", "")}
             for st in input_data.sub_topics],
            indent=2
        )

        # Step 2: Generate research plan with LLM
        prompt = QUERY_FORMULATION_PROMPT.format(
            topic=input_data.topic,
            target_audience=input_data.target_audience,
            key_concepts=", ".join(input_data.key_concepts),
            sub_topics=sub_topics_text,
            available_sources=sources_text,
        )

        response = await self.invoke_llm(prompt)

        # Step 3: Parse response and structure plan
        plan = self._parse_llm_response(response, input_data, relevant_sources)

        self.logger.info(
            "Query formulation complete",
            num_plans=len(plan.sub_topic_plans),
            total_sources=plan.total_sources,
        )

        return plan

    async def write_to_state(self, output_data: ResearchPlan) -> None:
        """Write research plan to shared state."""
        # Convert to dict for JSON serialization
        plan_dict = {
            "main_topic": output_data.main_topic,
            "target_audience": output_data.target_audience,
            "tui_source": output_data.tui_source,
            "total_sources": output_data.total_sources,
            "generated_at": output_data.generated_at,
            "research_plan": [
                {
                    "sub_topic": plan.sub_topic,
                    "queries": plan.queries,
                    "sources": plan.sources,
                    "focus_areas": plan.focus_areas,
                }
                for plan in output_data.sub_topic_plans
            ],
        }

        # Write to file
        self.shared_state.write_research_plan(plan_dict)

        # Update state
        self.shared_state.update_state(
            research_plan=plan_dict,
            current_phase="research",
        )

    async def validate_output(self, output_data: ResearchPlan) -> tuple[bool, str]:
        """Validate the research plan meets requirements."""
        issues = []

        # Check we have sub-topic plans
        if not output_data.sub_topic_plans:
            issues.append("No sub-topic plans generated")

        # Check each plan has queries and sources
        for plan in output_data.sub_topic_plans:
            if len(plan.queries) < 2:
                issues.append(f"Sub-topic '{plan.sub_topic}' has fewer than 2 queries")
            if len(plan.sources) < 2:
                issues.append(f"Sub-topic '{plan.sub_topic}' has fewer than 2 sources")

        # Check TUI source is included
        if not output_data.tui_source:
            issues.append("TUI source is missing (MANDATORY)")

        if issues:
            return False, f"Research plan validation failed: {'; '.join(issues)}"

        return True, f"Research plan valid: {len(output_data.sub_topic_plans)} sub-topics, {output_data.total_sources} sources"

    async def calculate_quality_score(self, output_data: ResearchPlan) -> float:
        """Calculate quality score for the research plan."""
        score = 0.0

        # Base score for having plans (40 points)
        if output_data.sub_topic_plans:
            score += 40.0

        # Score for query quantity (20 points)
        total_queries = sum(len(p.queries) for p in output_data.sub_topic_plans)
        query_score = min(20.0, (total_queries / 10) * 20)
        score += query_score

        # Score for source diversity (20 points)
        all_sources = set()
        for plan in output_data.sub_topic_plans:
            all_sources.update(plan.sources)
        source_score = min(20.0, (len(all_sources) / 8) * 20)
        score += source_score

        # Score for TUI inclusion (10 points)
        if output_data.tui_source:
            score += 10.0

        # Score for focus areas (10 points)
        total_focus = sum(len(p.focus_areas) for p in output_data.sub_topic_plans)
        focus_score = min(10.0, (total_focus / 6) * 10)
        score += focus_score

        return min(100.0, score)

    def _format_sources_for_prompt(self, sources: list[Source]) -> str:
        """Format sources list for LLM prompt."""
        lines = []
        for source in sources[:15]:  # Limit to top 15 sources
            lines.append(
                f"- {source.name} ({source.category.value}): {source.url}"
                f"\n  Keywords: {', '.join(source.relevance_keywords[:5])}"
            )
        return "\n".join(lines)

    def _parse_llm_response(
        self,
        response: str,
        input_data: QueryFormulationInput,
        relevant_sources: list[Source],
    ) -> ResearchPlan:
        """Parse LLM response into ResearchPlan."""
        try:
            # Try to extract JSON from response
            response = response.strip()

            # Remove markdown code blocks if present
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            if response.endswith("```"):
                response = response[:-3]

            data = json.loads(response.strip())

            sub_topic_plans = []
            for plan_data in data.get("sub_topic_plans", []):
                sub_topic_plans.append(SubTopicPlan(
                    sub_topic=plan_data.get("sub_topic", ""),
                    queries=plan_data.get("queries", []),
                    sources=plan_data.get("sources", []),
                    focus_areas=plan_data.get("focus_areas", []),
                ))

            # Calculate total unique sources
            all_sources = set()
            for plan in sub_topic_plans:
                all_sources.update(plan.sources)

            return ResearchPlan(
                main_topic=input_data.topic,
                target_audience=input_data.target_audience,
                sub_topic_plans=sub_topic_plans,
                tui_source=get_tui_source().url,
                total_sources=len(all_sources),
                generated_at=datetime.now().isoformat(),
            )

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse LLM response: {e}, using fallback")
            return self._create_fallback_plan(input_data, relevant_sources)

    def _create_fallback_plan(
        self,
        input_data: QueryFormulationInput,
        relevant_sources: list[Source],
    ) -> ResearchPlan:
        """Create a fallback research plan if LLM parsing fails."""
        current_year = datetime.now().year

        sub_topic_plans = []
        for sub_topic in input_data.sub_topics:
            name = sub_topic.get("name", str(sub_topic)) if isinstance(sub_topic, dict) else str(sub_topic)

            # Generate basic queries
            queries = [
                f"{input_data.topic} {name} {current_year}",
                f"{name} implementation best practices",
                f"{name} industry analysis {current_year}",
            ]

            # Select top sources
            source_names = [s.name for s in relevant_sources[:4]]

            sub_topic_plans.append(SubTopicPlan(
                sub_topic=name,
                queries=queries,
                sources=source_names,
                focus_areas=[f"{name} overview", f"{name} trends"],
            ))

        return ResearchPlan(
            main_topic=input_data.topic,
            target_audience=input_data.target_audience,
            sub_topic_plans=sub_topic_plans,
            tui_source=get_tui_source().url,
            total_sources=len(relevant_sources),
            generated_at=datetime.now().isoformat(),
        )


def create_query_formulation_agent(shared_state: SharedState) -> QueryFormulationAgent:
    """Factory function to create QueryFormulationAgent."""
    return QueryFormulationAgent(shared_state)
