"""Tests for the Orchestrator."""

import pytest
from pathlib import Path

from src.orchestrator.orchestrator import (
    Orchestrator,
    OrchestratorConfig,
    WorkflowPhase,
    AgentExecution,
)
from src.state.shared_state import SharedState
from src.agents.base_agent import BaseAgent, AgentResult


class MockSuccessAgent(BaseAgent):
    """Mock agent that always succeeds."""

    agent_name = "MockSuccessAgent"
    phase = "test"

    async def read_from_state(self):
        return {"topic": self.shared_state.state.get("topic")}

    async def process(self, input_data):
        return {"result": f"Processed: {input_data.get('topic')}"}

    async def write_to_state(self, output_data):
        pass

    async def validate_output(self, output_data):
        return True, "OK"


class MockFailAgent(BaseAgent):
    """Mock agent that always fails."""

    agent_name = "MockFailAgent"
    phase = "test"

    async def read_from_state(self):
        return {}

    async def process(self, input_data):
        raise RuntimeError("Simulated failure")

    async def write_to_state(self, output_data):
        pass

    async def validate_output(self, output_data):
        return True, "OK"


class TestOrchestratorConfig:
    """Test OrchestratorConfig defaults."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OrchestratorConfig()

        assert config.max_retries_per_agent == 3
        assert config.retry_base_delay == 1.0
        assert config.retry_max_delay == 60.0
        assert config.max_total_duration == 1800.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = OrchestratorConfig(
            max_retries_per_agent=5,
            max_total_duration=3600.0,
        )

        assert config.max_retries_per_agent == 5
        assert config.max_total_duration == 3600.0


class TestOrchestratorRegistration:
    """Test agent registration."""

    def test_register_agent(self):
        """Test registering an agent for a phase."""
        orchestrator = Orchestrator()

        def mock_factory(state):
            return MockSuccessAgent(state)

        orchestrator.register_agent(WorkflowPhase.RESEARCH, mock_factory)

        assert WorkflowPhase.RESEARCH in orchestrator._agents


class TestOrchestratorExecution:
    """Test orchestrator execution."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> Orchestrator:
        """Create orchestrator with temp output directory."""
        config = OrchestratorConfig(
            output_base_dir=str(tmp_path),
            max_retries_per_agent=2,
            retry_base_delay=0.1,
        )
        return Orchestrator(config)

    @pytest.mark.asyncio
    async def test_run_creates_output_directory(self, orchestrator: Orchestrator, tmp_path: Path):
        """Test that run creates output directory structure."""
        state = await orchestrator.run(
            topic="Test Topic",
            target_audience="Test Audience",
        )

        assert state.output_dir.exists()
        assert state.input_dir.exists()
        assert state.research_dir.exists()

    @pytest.mark.asyncio
    async def test_run_initializes_state(self, orchestrator: Orchestrator):
        """Test that run initializes state correctly."""
        state = await orchestrator.run(
            topic="Universal Commerce Protocol",
            key_concepts=["AI", "Commerce"],
        )

        assert state.state["topic"] == "Universal Commerce Protocol"
        assert state.state["key_concepts"] == ["AI", "Commerce"]

    @pytest.mark.asyncio
    async def test_run_with_subtopics(self, orchestrator: Orchestrator):
        """Test run with subtopics provided."""
        sub_topics = [
            {"name": "Tech Architecture", "queries": ["UCP spec"]},
        ]
        state = await orchestrator.run(
            topic="Test",
            sub_topics=sub_topics,
        )

        # Check subtopics file was written
        assert (state.input_dir / "topics_and_subtopics.json").exists()


class TestWorkflowPhase:
    """Test WorkflowPhase enum."""

    def test_phase_values(self):
        """Test all workflow phases are defined."""
        assert WorkflowPhase.QUERY_FORMULATION.value == "query_formulation"
        assert WorkflowPhase.RESEARCH.value == "research"
        assert WorkflowPhase.TUI_ANALYSIS.value == "tui_analysis"
        assert WorkflowPhase.SYNTHESIS.value == "synthesis"
        assert WorkflowPhase.EDITING.value == "editing"
        assert WorkflowPhase.VISUALS.value == "visuals"
        assert WorkflowPhase.MULTIMEDIA.value == "multimedia"
        assert WorkflowPhase.ASSEMBLY.value == "assembly"
        assert WorkflowPhase.COMPLETE.value == "complete"


class TestAgentExecution:
    """Test AgentExecution dataclass."""

    def test_agent_execution_creation(self):
        """Test creating AgentExecution record."""
        from datetime import datetime

        execution = AgentExecution(
            agent_name="research",
            phase=WorkflowPhase.RESEARCH,
            start_time=datetime.now(),
        )

        assert execution.agent_name == "research"
        assert execution.phase == WorkflowPhase.RESEARCH
        assert execution.success is False  # default
        assert execution.retry_count == 0


class TestExecutionSummary:
    """Test execution summary generation."""

    @pytest.mark.asyncio
    async def test_get_execution_summary(self, tmp_path: Path):
        """Test getting execution summary after run."""
        config = OrchestratorConfig(output_base_dir=str(tmp_path))
        orchestrator = Orchestrator(config)

        await orchestrator.run(topic="Test")

        summary = orchestrator.get_execution_summary()

        assert "total_duration_ms" in summary
        assert "phases_executed" in summary
        assert "output_dir" in summary
