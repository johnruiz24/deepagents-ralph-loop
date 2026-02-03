"""Tests for Phase 2: Research Pipeline agents."""

import pytest
from pathlib import Path
import json

from src.state.shared_state import SharedState, create_shared_state
from src.config.sources import (
    MASTER_SOURCE_LIST,
    get_sources_by_relevance,
    get_tui_source,
    SourceCategory,
)


class TestMasterSourceList:
    """Test the Master Source List configuration."""

    def test_master_source_list_populated(self):
        """Test that master source list is populated."""
        assert len(MASTER_SOURCE_LIST) > 15
        assert len(MASTER_SOURCE_LIST) < 50  # Reasonable size

    def test_all_categories_represented(self):
        """Test that all source categories are represented."""
        categories = set(s.category for s in MASTER_SOURCE_LIST)

        assert SourceCategory.TECHNOLOGY_RESEARCH in categories
        assert SourceCategory.TRAVEL_INDUSTRY in categories
        assert SourceCategory.BIG_TECH in categories
        assert SourceCategory.TUI_SPECIFIC in categories

    def test_tui_source_exists(self):
        """Test that TUI source is in the list."""
        tui_source = get_tui_source()

        assert tui_source is not None
        assert "tuigroup.com" in tui_source.url
        assert tui_source.category == SourceCategory.TUI_SPECIFIC

    def test_get_sources_by_relevance(self):
        """Test filtering sources by relevance."""
        # Test AI-related keywords
        ai_sources = get_sources_by_relevance(["ai", "agentic"])
        assert len(ai_sources) > 0

        # Test travel keywords
        travel_sources = get_sources_by_relevance(["travel", "tourism"])
        assert len(travel_sources) > 0

        # Should have different results
        ai_names = {s.name for s in ai_sources}
        travel_names = {s.name for s in travel_sources}
        assert ai_names != travel_names


class TestQueryFormulationAgent:
    """Test the Query Formulation Agent."""

    @pytest.fixture
    def shared_state(self, tmp_path: Path) -> SharedState:
        """Create shared state for testing."""
        return create_shared_state(
            topic="Universal Commerce Protocol (UCP)",
            target_audience="TUI Leadership",
            key_concepts=["Agentic AI", "Commerce Protocols", "Travel Technology"],
            output_base_dir=str(tmp_path),
        )

    def test_agent_initialization(self, shared_state: SharedState):
        """Test agent can be initialized."""
        from src.agents.query_formulation_agent import QueryFormulationAgent

        agent = QueryFormulationAgent(shared_state)
        assert agent.agent_name == "QueryFormulationAgent"
        assert agent.phase == "query_formulation"

    @pytest.mark.asyncio
    async def test_read_from_state(self, shared_state: SharedState):
        """Test reading input from state."""
        from src.agents.query_formulation_agent import QueryFormulationAgent

        agent = QueryFormulationAgent(shared_state)
        input_data = await agent.read_from_state()

        assert input_data.topic == "Universal Commerce Protocol (UCP)"
        assert "Agentic AI" in input_data.key_concepts

    def test_fallback_plan_generation(self, shared_state: SharedState):
        """Test fallback plan generation when LLM fails."""
        from src.agents.query_formulation_agent import QueryFormulationAgent, QueryFormulationInput

        agent = QueryFormulationAgent(shared_state)
        relevant_sources = get_sources_by_relevance(["ai", "travel"])

        input_data = QueryFormulationInput(
            topic="Test Topic",
            key_concepts=["AI", "Travel"],
            sub_topics=[{"name": "Technical Architecture"}, {"name": "Business Impact"}],
            target_audience="Executives",
        )

        plan = agent._create_fallback_plan(input_data, relevant_sources)

        assert plan.main_topic == "Test Topic"
        assert len(plan.sub_topic_plans) == 2
        assert plan.tui_source  # TUI should always be included


class TestParallelizedResearchAgent:
    """Test the Parallelized Research Agent."""

    @pytest.fixture
    def shared_state_with_plan(self, tmp_path: Path) -> SharedState:
        """Create shared state with a research plan."""
        state = create_shared_state(
            topic="Test Topic",
            output_base_dir=str(tmp_path),
        )

        # Add a mock research plan
        research_plan = {
            "main_topic": "Test Topic",
            "research_plan": [
                {
                    "sub_topic": "Technical Architecture",
                    "queries": ["test query 1", "test query 2"],
                    "sources": ["MIT Technology Review", "Google AI Blog"],
                    "focus_areas": ["API design"],
                },
            ],
        }
        state.write_research_plan(research_plan)
        state.update_state(research_plan=research_plan)

        return state

    def test_agent_initialization(self, shared_state_with_plan: SharedState):
        """Test agent can be initialized."""
        from src.agents.research_agent import ParallelizedResearchAgent, ResearchConfig

        config = ResearchConfig(max_concurrent_agents=2)
        agent = ParallelizedResearchAgent(shared_state_with_plan, config=config)

        assert agent.agent_name == "ParallelizedResearchAgent"
        assert agent.config.max_concurrent_agents == 2

    @pytest.mark.asyncio
    async def test_read_from_state(self, shared_state_with_plan: SharedState):
        """Test reading research plan from state."""
        from src.agents.research_agent import ParallelizedResearchAgent

        agent = ParallelizedResearchAgent(shared_state_with_plan)
        input_data = await agent.read_from_state()

        assert "research_plan" in input_data
        assert len(input_data["research_plan"]) > 0

    def test_quality_calculation(self, shared_state_with_plan: SharedState):
        """Test quality score calculation."""
        from src.agents.research_agent import ParallelizedResearchAgent

        agent = ParallelizedResearchAgent(shared_state_with_plan)

        # Test with good results
        score = agent._calculate_quality(
            total_articles=10,
            num_subtopics=3,
            successful_subtopics=3,
            num_sources=6,
        )
        assert score >= 80  # Should be high quality

        # Test with poor results
        score_low = agent._calculate_quality(
            total_articles=1,
            num_subtopics=3,
            successful_subtopics=1,
            num_sources=1,
        )
        assert score_low < score  # Should be lower


class TestTUIStrategyAgent:
    """Test the TUI Strategy Analysis Agent."""

    @pytest.fixture
    def shared_state(self, tmp_path: Path) -> SharedState:
        """Create shared state for testing."""
        return create_shared_state(
            topic="Universal Commerce Protocol",
            output_base_dir=str(tmp_path),
        )

    def test_agent_initialization(self, shared_state: SharedState):
        """Test agent can be initialized."""
        from src.agents.tui_strategy_agent import TUIStrategyAgent

        agent = TUIStrategyAgent(shared_state)

        assert agent.agent_name == "TUIStrategyAgent"
        assert agent.phase == "tui_analysis"
        assert "tuigroup.com" in agent.TUI_INVESTOR_URL

    @pytest.mark.asyncio
    async def test_read_from_state(self, shared_state: SharedState):
        """Test reading topic from state."""
        from src.agents.tui_strategy_agent import TUIStrategyAgent

        agent = TUIStrategyAgent(shared_state)
        topic = await agent.read_from_state()

        assert topic == "Universal Commerce Protocol"

    def test_fallback_analysis_creation(self, shared_state: SharedState):
        """Test fallback analysis is comprehensive."""
        from src.agents.tui_strategy_agent import TUIStrategyAgent

        agent = TUIStrategyAgent(shared_state)
        fallback = agent._create_fallback_analysis()

        assert len(fallback.business_model) > 50
        assert len(fallback.strategic_priorities) >= 3
        assert len(fallback.risks_and_challenges) >= 3
        assert fallback.technology_strategy

    def test_summary_markdown_generation(self, shared_state: SharedState):
        """Test markdown summary generation."""
        from src.agents.tui_strategy_agent import TUIStrategyAgent

        agent = TUIStrategyAgent(shared_state)
        fallback = agent._create_fallback_analysis()
        markdown = agent._generate_summary_markdown(fallback)

        assert "# TUI Group Strategic Analysis" in markdown
        assert "Business Model" in markdown
        assert "Strategic Priorities" in markdown
        assert "Technology" in markdown
        assert "Risks" in markdown

    @pytest.mark.asyncio
    async def test_validate_output_comprehensive(self, shared_state: SharedState):
        """Test output validation requires comprehensive analysis."""
        from src.agents.tui_strategy_agent import TUIStrategyAgent, TUIStrategicInfo

        agent = TUIStrategyAgent(shared_state)

        # Good analysis should pass
        good_analysis = agent._create_fallback_analysis()
        passes, msg = await agent.validate_output(good_analysis)
        assert passes

        # Incomplete analysis should fail
        incomplete = TUIStrategicInfo(
            business_model="Short",  # Too brief
            market_positioning="",
            strategic_priorities=["One"],  # Too few
            financial_highlights="",
            technology_strategy="",  # Missing
            digital_initiatives=[],
            risks_and_challenges=[],  # Too few
            recent_developments=[],
            source_documents=[],
            extracted_at="",
        )
        passes, msg = await agent.validate_output(incomplete)
        assert not passes
        assert "incomplete" in msg.lower() or "missing" in msg.lower() or "brief" in msg.lower()


class TestResearchPipelineIntegration:
    """Integration tests for the research pipeline."""

    @pytest.fixture
    def shared_state(self, tmp_path: Path) -> SharedState:
        """Create shared state for integration testing."""
        return create_shared_state(
            topic="Universal Commerce Protocol (UCP)",
            target_audience="TUI Leadership and Strategy Teams",
            key_concepts=["Agentic AI", "Commerce Protocols", "Travel Technology"],
            output_base_dir=str(tmp_path),
        )

    def test_shared_state_directories_created(self, shared_state: SharedState):
        """Test that all required directories are created."""
        assert shared_state.research_dir.exists()
        assert shared_state.raw_data_dir.exists()
        assert shared_state.content_dir.exists()

    def test_research_plan_file_writing(self, shared_state: SharedState):
        """Test that research plan can be written."""
        plan = {
            "main_topic": "Test",
            "research_plan": [{"sub_topic": "Test", "queries": ["query"]}],
        }
        path = shared_state.write_research_plan(plan)

        assert path.exists()
        loaded = json.loads(path.read_text())
        assert loaded["main_topic"] == "Test"

    def test_research_data_file_writing(self, shared_state: SharedState):
        """Test that research data can be written per subtopic."""
        shared_state.write_research_data(
            subtopic="Technical Architecture",
            filename="article_1.md",
            content="# Test Article\n\nContent here.",
        )

        # Check file was created in correct location
        data = shared_state.read_all_research_data()
        assert len(data) > 0

    def test_tui_summary_file_writing(self, shared_state: SharedState):
        """Test that TUI summary can be written."""
        summary = "# TUI Strategy Summary\n\nKey insights here."
        path = shared_state.write_tui_strategy_summary(summary)

        assert path.exists()
        assert shared_state.read_tui_strategy_summary() == summary
