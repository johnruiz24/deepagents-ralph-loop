"""Tests for BaseAgent abstract class."""

import pytest
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.agents.base_agent import BaseAgent, LLMAgent, AgentResult, with_retry
from src.state.shared_state import SharedState


@dataclass
class MockInput:
    """Mock input for testing."""
    data: str


@dataclass
class MockOutput:
    """Mock output for testing."""
    result: str
    score: float


class MockAgent(BaseAgent[MockInput, MockOutput]):
    """Concrete implementation of BaseAgent for testing."""

    agent_name = "MockAgent"
    phase = "test"

    def __init__(self, shared_state: SharedState, should_fail: bool = False, fail_count: int = 0):
        super().__init__(shared_state)
        self.should_fail = should_fail
        self.fail_count = fail_count
        self._current_fails = 0

    async def read_from_state(self) -> MockInput:
        return MockInput(data=self.shared_state.state.get("topic", "test"))

    async def process(self, input_data: MockInput) -> MockOutput:
        if self.should_fail:
            if self._current_fails < self.fail_count:
                self._current_fails += 1
                raise ConnectionError("Simulated connection error")
        return MockOutput(result=f"Processed: {input_data.data}", score=90.0)

    async def write_to_state(self, output_data: MockOutput) -> None:
        self.shared_state.update_state(article_content=output_data.result)

    async def validate_output(self, output_data: MockOutput) -> tuple[bool, str]:
        if output_data.score >= 85:
            return True, f"Validation passed with score {output_data.score}"
        return False, f"Score {output_data.score} below threshold 85"

    async def calculate_quality_score(self, output_data: MockOutput) -> float:
        return output_data.score


class TestBaseAgentExecution:
    """Test BaseAgent execution flow."""

    @pytest.fixture
    def shared_state(self, tmp_path: Path) -> SharedState:
        """Create a shared state for testing."""
        return SharedState(output_dir=tmp_path / "test_output")

    @pytest.mark.asyncio
    async def test_execute_success(self, shared_state: SharedState):
        """Test successful agent execution."""
        agent = MockAgent(shared_state)
        result = await agent.execute()

        assert result.success is True
        assert result.quality_score == 90.0
        assert "completed successfully" in result.message
        assert result.duration_ms > 0

    @pytest.mark.asyncio
    async def test_execute_writes_to_state(self, shared_state: SharedState):
        """Test that agent writes output to state."""
        shared_state.update_state(topic="Test Topic")
        agent = MockAgent(shared_state)

        await agent.execute()

        assert "Processed: Test Topic" in shared_state.state["article_content"]

    @pytest.mark.asyncio
    async def test_execute_records_quality_gate(self, shared_state: SharedState):
        """Test that agent records quality gate passed."""
        agent = MockAgent(shared_state)

        await agent.execute()

        assert "MockAgent" in shared_state.state["quality_gates_passed"]

    @pytest.mark.asyncio
    async def test_execute_with_retry(self, shared_state: SharedState):
        """Test that agent retries on transient errors."""
        # Will fail twice then succeed
        agent = MockAgent(shared_state, should_fail=True, fail_count=2)
        agent.max_retries = 3

        result = await agent.execute()

        assert result.success is True
        assert agent._current_fails == 2  # Failed twice before success


class TestBaseAgentValidation:
    """Test BaseAgent validation behavior."""

    @pytest.fixture
    def shared_state(self, tmp_path: Path) -> SharedState:
        return SharedState(output_dir=tmp_path / "test_output")

    @pytest.mark.asyncio
    async def test_validation_failure_records_gate_failed(self, shared_state: SharedState):
        """Test that validation failure records gate failed."""

        class FailingAgent(MockAgent):
            async def validate_output(self, output_data: MockOutput) -> tuple[bool, str]:
                return False, "Score too low"

        agent = FailingAgent(shared_state)
        result = await agent.execute()

        assert result.success is False
        assert "MockAgent" in str(shared_state.state["quality_gates_failed"])


class TestAgentResult:
    """Test AgentResult dataclass."""

    def test_agent_result_creation(self):
        """Test creating AgentResult."""
        result = AgentResult(
            success=True,
            output={"data": "test"},
            quality_score=95.0,
            message="Test completed",
            duration_ms=1234.5,
        )

        assert result.success is True
        assert result.quality_score == 95.0
        assert result.duration_ms == 1234.5

    def test_agent_result_with_error(self):
        """Test AgentResult with error."""
        result = AgentResult(
            success=False,
            error="Connection timeout",
            message="Failed",
        )

        assert result.success is False
        assert result.error == "Connection timeout"


class TestWithRetryDecorator:
    """Test the with_retry decorator."""

    @pytest.mark.asyncio
    async def test_with_retry_success_after_failures(self):
        """Test that decorated function succeeds after retries."""
        call_count = 0

        @with_retry(max_attempts=3, min_wait=0, max_wait=1)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient error")
            return "success"

        result = await flaky_function()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_with_retry_max_attempts_exceeded(self):
        """Test that decorator raises after max attempts."""

        @with_retry(max_attempts=2, min_wait=0, max_wait=1)
        async def always_fails():
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            await always_fails()
