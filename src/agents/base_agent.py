"""
Base Agent abstract class for the 9-agent newsletter system.

All agents inherit from this class and implement:
- read_from_state(): Extract required inputs from shared state
- process(): Perform the agent's designated task
- write_to_state(): Write outputs back to shared state
- signal_completion(): Signal completion to the orchestrator

Also includes exponential backoff retry logic for LLM calls.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, TypeVar, Generic
from functools import wraps

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

from src.state.shared_state import SharedState
from src.state.newsletter_state import QUALITY_THRESHOLDS
from src.utils.logging import AgentLogger, get_agent_logger


# Type variable for agent input/output
TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


@dataclass
class AgentResult:
    """
    Standard result object returned by all agents.

    Attributes:
        success: Whether the agent completed successfully
        output: The agent's output data
        quality_score: Quality score for the output (0-100)
        message: Human-readable status message
        duration_ms: Execution time in milliseconds
        error: Error message if failed
    """
    success: bool
    output: Optional[Any] = None
    quality_score: float = 0.0
    message: str = ""
    duration_ms: float = 0.0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC, Generic[TInput, TOutput]):
    """
    Abstract base class for all newsletter agents.

    Provides:
    - Structured logging
    - Exponential backoff retry logic
    - Quality gate validation
    - Standardized execution flow
    """

    # Agent configuration
    agent_name: str = "BaseAgent"
    phase: str = "unknown"
    max_retries: int = 3
    retry_min_wait: int = 1  # seconds
    retry_max_wait: int = 60  # seconds

    def __init__(
        self,
        shared_state: SharedState,
        logger: Optional[AgentLogger] = None,
    ):
        """
        Initialize the agent.

        Args:
            shared_state: The shared state object
            logger: Optional custom logger
        """
        self.shared_state = shared_state
        self.logger = logger or get_agent_logger(self.agent_name, self.phase)
        self._start_time: float = 0.0

    # ============== Abstract Methods (Must Implement) ==============

    @abstractmethod
    async def read_from_state(self) -> TInput:
        """
        Extract required inputs from the shared state.

        Returns:
            The extracted input data for this agent

        Raises:
            ValueError: If required inputs are missing
        """
        pass

    @abstractmethod
    async def process(self, input_data: TInput) -> TOutput:
        """
        Perform the agent's designated task.

        Args:
            input_data: The input data from read_from_state()

        Returns:
            The processed output data
        """
        pass

    @abstractmethod
    async def write_to_state(self, output_data: TOutput) -> None:
        """
        Write the agent's outputs back to the shared state.

        Args:
            output_data: The output from process()
        """
        pass

    @abstractmethod
    async def validate_output(self, output_data: TOutput) -> tuple[bool, str]:
        """
        Validate the output meets quality requirements.

        Args:
            output_data: The output to validate

        Returns:
            Tuple of (passes: bool, message: str)
        """
        pass

    # ============== Main Execution Flow ==============

    async def execute(self) -> AgentResult:
        """
        Execute the full agent workflow.

        Flow:
        1. Read inputs from state
        2. Process with retry logic
        3. Validate output
        4. Write to state
        5. Signal completion

        Returns:
            AgentResult with execution details
        """
        self._start_time = time.time()

        self.logger.info(
            f"Starting {self.agent_name}",
            status="starting",
            phase=self.phase,
        )

        try:
            # Step 1: Read from state
            input_data = await self.read_from_state()
            self.logger.debug("Read input from state", input_keys=str(type(input_data)))

            # Step 2: Process with retry logic
            output_data = await self._process_with_retry(input_data)

            # Step 3: Validate output
            passes, message = await self.validate_output(output_data)

            if not passes:
                self.logger.warning(
                    f"Quality gate failed: {message}",
                    status="validation_failed",
                    quality_score=0.0,
                )
                self.shared_state.record_gate_failed(self.agent_name, message)
                return self._create_result(
                    success=False,
                    output=output_data,
                    message=message,
                    error=f"Quality gate failed: {message}",
                )

            # Step 4: Write to state
            await self.write_to_state(output_data)
            self.logger.debug("Wrote output to state")

            # Step 5: Signal completion
            result = await self.signal_completion(output_data)

            self.logger.info(
                f"{self.agent_name} completed successfully",
                status="completed",
                duration_ms=result.duration_ms,
                quality_score=result.quality_score,
            )

            return result

        except RetryError as e:
            error_msg = f"Max retries exceeded: {str(e.last_attempt.exception())}"
            self.logger.error(error_msg, status="failed", error_details={"retries": self.max_retries})
            self.shared_state.add_error(error_msg)
            return self._create_result(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            self.logger.error(error_msg, status="failed", error_details={"exception": type(e).__name__})
            self.shared_state.add_error(error_msg)
            return self._create_result(success=False, error=error_msg)

    async def _process_with_retry(self, input_data: TInput) -> TOutput:
        """
        Process with exponential backoff retry logic.

        Uses tenacity for retry handling with:
        - Exponential backoff (1s -> 2s -> 4s -> ... up to 60s)
        - Max 3 retries by default
        - Retry on common transient errors
        """
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=1,
                min=self.retry_min_wait,
                max=self.retry_max_wait,
            ),
            retry=retry_if_exception_type((
                ConnectionError,
                TimeoutError,
                asyncio.TimeoutError,
            )),
            reraise=True,
        )
        async def _execute_with_retry() -> TOutput:
            return await self.process(input_data)

        return await _execute_with_retry()

    async def signal_completion(self, output_data: TOutput) -> AgentResult:
        """
        Signal completion to the orchestrator.

        Updates the shared state with:
        - Quality gate passed
        - Next phase (if applicable)
        - Iteration count

        Args:
            output_data: The successfully processed output

        Returns:
            AgentResult with final status
        """
        # Record quality gate passed
        self.shared_state.record_gate_passed(self.agent_name)

        # Calculate quality score (can be overridden)
        quality_score = await self.calculate_quality_score(output_data)

        # Create result
        return self._create_result(
            success=True,
            output=output_data,
            quality_score=quality_score,
            message=f"{self.agent_name} completed successfully",
        )

    async def calculate_quality_score(self, output_data: TOutput) -> float:
        """
        Calculate quality score for the output.

        Override in subclasses for specific scoring logic.

        Args:
            output_data: The output to score

        Returns:
            Quality score (0-100)
        """
        return 0.0

    def _create_result(
        self,
        success: bool,
        output: Optional[Any] = None,
        quality_score: float = 0.0,
        message: str = "",
        error: Optional[str] = None,
    ) -> AgentResult:
        """Create a standardized AgentResult."""
        duration_ms = (time.time() - self._start_time) * 1000

        return AgentResult(
            success=success,
            output=output,
            quality_score=quality_score,
            message=message,
            duration_ms=duration_ms,
            error=error,
            metadata={
                "agent_name": self.agent_name,
                "phase": self.phase,
            },
        )

    # ============== Utility Methods ==============

    def get_threshold(self, name: str) -> Any:
        """Get a quality threshold value."""
        return QUALITY_THRESHOLDS.get(name)

    def get_max_iterations(self) -> int:
        """Get max iterations per phase."""
        return QUALITY_THRESHOLDS.get("max_iterations_per_phase", 3)


class LLMAgent(BaseAgent[TInput, TOutput]):
    """
    Base class for agents that use LLM for processing.

    Adds:
    - LLM configuration
    - Token tracking
    - Rate limiting awareness
    """

    def __init__(
        self,
        shared_state: SharedState,
        llm: Optional[Any] = None,
        logger: Optional[AgentLogger] = None,
    ):
        """
        Initialize LLM agent.

        Args:
            shared_state: The shared state object
            llm: Optional pre-configured LLM
            logger: Optional custom logger
        """
        super().__init__(shared_state, logger)
        self._llm = llm
        self._tokens_used = 0

    @property
    def llm(self) -> Any:
        """Get or create the LLM instance."""
        if self._llm is None:
            from src.utils.bedrock_config import create_bedrock_llm
            self._llm = create_bedrock_llm()
        return self._llm

    async def invoke_llm(self, prompt: str, **kwargs: Any) -> str:
        """
        Invoke the LLM with retry logic.

        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments for the LLM

        Returns:
            The LLM response content
        """
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=1,
                min=self.retry_min_wait,
                max=self.retry_max_wait,
            ),
            reraise=True,
        )
        async def _invoke() -> str:
            response = await self.llm.ainvoke(prompt, **kwargs)
            return response.content

        return await _invoke()


# ============== Decorator for Retry Logic ==============

def with_retry(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 60,
):
    """
    Decorator to add exponential backoff retry logic to async functions.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
    """
    def decorator(func):
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            reraise=True,
        )
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator
