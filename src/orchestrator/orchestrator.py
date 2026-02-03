"""
Orchestrator Agent for the 9-agent newsletter system.

The central coordinator that:
- Initializes the system
- Invokes each specialized agent in sequence
- Manages the shared state
- Handles errors with exponential backoff retry

Based on IMPLEMENTATION_GUIDE.md section 3.1.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Awaitable

from langgraph.graph import StateGraph, END

from src.state.shared_state import SharedState, create_shared_state
from src.state.newsletter_state import NewsletterState, QUALITY_THRESHOLDS
from src.utils.logging import AgentLogger, get_agent_logger, setup_logging


class WorkflowPhase(str, Enum):
    """Enumeration of workflow phases."""
    QUERY_FORMULATION = "query_formulation"
    RESEARCH = "research"
    TUI_ANALYSIS = "tui_analysis"
    SYNTHESIS = "synthesis"
    EDITING = "editing"
    VISUALS = "visuals"
    MULTIMEDIA = "multimedia"
    ASSEMBLY = "assembly"
    COMPLETE = "complete"


@dataclass
class AgentExecution:
    """Record of an agent execution."""
    agent_name: str
    phase: WorkflowPhase
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None
    retry_count: int = 0
    quality_score: float = 0.0


@dataclass
class OrchestratorConfig:
    """Configuration for the Orchestrator."""
    max_retries_per_agent: int = 3
    retry_base_delay: float = 1.0  # seconds
    retry_max_delay: float = 60.0  # seconds
    max_total_duration: float = 1800.0  # 30 minutes
    log_file: Optional[Path] = None
    output_base_dir: str = "output"


class Orchestrator:
    """
    Central coordinator for the 9-agent newsletter workflow.

    Responsibilities:
    - Initialize shared state
    - Invoke agents in sequence
    - Handle errors with exponential backoff
    - Track execution progress
    - Produce final deliverables
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize the Orchestrator.

        Args:
            config: Optional configuration overrides
        """
        self.config = config or OrchestratorConfig()
        self.logger = get_agent_logger("Orchestrator", "orchestration")
        self.shared_state: Optional[SharedState] = None
        self.execution_log: list[AgentExecution] = []
        self._start_time: float = 0.0

        # Agent registry (populated during setup)
        self._agents: dict[WorkflowPhase, Callable] = {}

    def register_agent(
        self,
        phase: WorkflowPhase,
        agent_factory: Callable[[SharedState], Any],
    ) -> None:
        """
        Register an agent for a workflow phase.

        Args:
            phase: The workflow phase this agent handles
            agent_factory: Factory function that creates the agent
        """
        self._agents[phase] = agent_factory
        self.logger.debug(f"Registered agent for phase: {phase.value}")

    async def run(
        self,
        topic: str,
        target_audience: str = "TUI Leadership and Strategy Teams",
        key_concepts: Optional[list[str]] = None,
        sub_topics: Optional[list[dict]] = None,
    ) -> SharedState:
        """
        Run the complete newsletter generation workflow.

        Args:
            topic: The newsletter topic
            target_audience: Target audience description
            key_concepts: Optional list of key concepts
            sub_topics: Optional list of subtopics with details

        Returns:
            The final SharedState with all artifacts
        """
        self._start_time = time.time()

        # Setup logging
        if self.config.log_file:
            setup_logging(log_file=self.config.log_file)

        self.logger.info(
            "Starting newsletter workflow",
            status="initializing",
            topic=topic,
        )

        try:
            # Initialize shared state
            self.shared_state = create_shared_state(
                topic=topic,
                target_audience=target_audience,
                key_concepts=key_concepts,
                output_base_dir=self.config.output_base_dir,
            )

            # Write subtopics if provided
            if sub_topics:
                self.shared_state.write_topics_and_subtopics(sub_topics)

            self.logger.info(
                f"Created output directory: {self.shared_state.output_dir}",
                status="initialized",
            )

            # Execute workflow phases in sequence
            phases = [
                WorkflowPhase.QUERY_FORMULATION,
                WorkflowPhase.RESEARCH,
                WorkflowPhase.TUI_ANALYSIS,
                WorkflowPhase.SYNTHESIS,
                WorkflowPhase.EDITING,
                WorkflowPhase.VISUALS,
                WorkflowPhase.MULTIMEDIA,
                WorkflowPhase.ASSEMBLY,
            ]

            for phase in phases:
                # Check timeout
                if self._is_timed_out():
                    raise TimeoutError(f"Workflow exceeded max duration of {self.config.max_total_duration}s")

                # Execute phase with retry
                success = await self._execute_phase_with_retry(phase)

                if not success:
                    self.logger.error(
                        f"Phase {phase.value} failed after all retries",
                        status="failed",
                        phase=phase.value,
                    )
                    # Continue to next phase or abort based on criticality
                    if phase in [WorkflowPhase.RESEARCH, WorkflowPhase.TUI_ANALYSIS]:
                        raise RuntimeError(f"Critical phase {phase.value} failed")

            # Mark workflow complete
            self.shared_state.mark_complete()
            self.shared_state.save_state_snapshot()

            self.logger.info(
                "Newsletter workflow completed successfully",
                status="completed",
                duration_ms=(time.time() - self._start_time) * 1000,
                output_dir=str(self.shared_state.output_dir),
            )

            return self.shared_state

        except Exception as e:
            self.logger.critical(
                f"Workflow failed: {str(e)}",
                status="failed",
                error_details={"exception": type(e).__name__, "message": str(e)},
            )
            if self.shared_state:
                self.shared_state.add_error(f"Workflow failed: {str(e)}")
                self.shared_state.save_state_snapshot()
            raise

    async def _execute_phase_with_retry(self, phase: WorkflowPhase) -> bool:
        """
        Execute a workflow phase with exponential backoff retry.

        Args:
            phase: The phase to execute

        Returns:
            True if phase succeeded, False otherwise
        """
        execution = AgentExecution(
            agent_name=phase.value,
            phase=phase,
            start_time=datetime.now(),
        )

        for attempt in range(self.config.max_retries_per_agent):
            execution.retry_count = attempt

            try:
                self.logger.info(
                    f"Executing phase: {phase.value}",
                    status="running",
                    phase=phase.value,
                    iteration=attempt + 1,
                )

                # Update shared state phase
                self.shared_state.set_phase(phase.value)
                self.shared_state.increment_iteration(phase.value)

                # Execute the agent
                await self._execute_agent(phase)

                # Success
                execution.end_time = datetime.now()
                execution.success = True
                self.execution_log.append(execution)

                self.logger.info(
                    f"Phase {phase.value} completed",
                    status="completed",
                    phase=phase.value,
                    duration_ms=(execution.end_time - execution.start_time).total_seconds() * 1000,
                )

                return True

            except Exception as e:
                execution.error = str(e)

                self.logger.warning(
                    f"Phase {phase.value} attempt {attempt + 1} failed: {str(e)}",
                    status="retrying",
                    phase=phase.value,
                    iteration=attempt + 1,
                    error_details={"exception": type(e).__name__},
                )

                # Calculate exponential backoff delay
                if attempt < self.config.max_retries_per_agent - 1:
                    delay = min(
                        self.config.retry_base_delay * (2 ** attempt),
                        self.config.retry_max_delay,
                    )
                    self.logger.debug(f"Waiting {delay}s before retry")
                    await asyncio.sleep(delay)

        # All retries exhausted
        execution.end_time = datetime.now()
        execution.success = False
        self.execution_log.append(execution)

        return False

    async def _execute_agent(self, phase: WorkflowPhase) -> None:
        """
        Execute the agent for a specific phase.

        Args:
            phase: The phase to execute

        Raises:
            NotImplementedError: If agent not registered
            Exception: If agent execution fails
        """
        if phase not in self._agents:
            # Placeholder for phases without registered agents
            self.logger.warning(
                f"No agent registered for phase {phase.value}, skipping",
                status="skipped",
                phase=phase.value,
            )
            return

        # Create and execute the agent
        agent_factory = self._agents[phase]
        agent = agent_factory(self.shared_state)
        result = await agent.execute()

        if not result.success:
            raise RuntimeError(f"Agent {phase.value} failed: {result.error or result.message}")

    def _is_timed_out(self) -> bool:
        """Check if workflow has exceeded max duration."""
        elapsed = time.time() - self._start_time
        return elapsed > self.config.max_total_duration

    def get_execution_summary(self) -> dict:
        """Get a summary of the workflow execution."""
        return {
            "total_duration_ms": (time.time() - self._start_time) * 1000,
            "phases_executed": len(self.execution_log),
            "phases_succeeded": sum(1 for e in self.execution_log if e.success),
            "phases_failed": sum(1 for e in self.execution_log if not e.success),
            "total_retries": sum(e.retry_count for e in self.execution_log),
            "output_dir": str(self.shared_state.output_dir) if self.shared_state else None,
            "is_complete": self.shared_state.state.get("is_complete", False) if self.shared_state else False,
        }


# ============== LangGraph Integration ==============

def create_newsletter_graph(orchestrator: Orchestrator) -> StateGraph:
    """
    Create a LangGraph StateGraph for the newsletter workflow.

    This provides an alternative execution model using LangGraph's
    state machine capabilities.

    Args:
        orchestrator: The orchestrator instance

    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(NewsletterState)

    # Add nodes for each phase
    async def query_formulation_node(state: NewsletterState) -> dict:
        """Execute query formulation phase."""
        orchestrator.shared_state.update_state(**state)
        await orchestrator._execute_agent(WorkflowPhase.QUERY_FORMULATION)
        return dict(orchestrator.shared_state.state)

    async def research_node(state: NewsletterState) -> dict:
        """Execute research phase."""
        orchestrator.shared_state.update_state(**state)
        await orchestrator._execute_agent(WorkflowPhase.RESEARCH)
        return dict(orchestrator.shared_state.state)

    async def tui_analysis_node(state: NewsletterState) -> dict:
        """Execute TUI analysis phase."""
        orchestrator.shared_state.update_state(**state)
        await orchestrator._execute_agent(WorkflowPhase.TUI_ANALYSIS)
        return dict(orchestrator.shared_state.state)

    async def synthesis_node(state: NewsletterState) -> dict:
        """Execute synthesis phase."""
        orchestrator.shared_state.update_state(**state)
        await orchestrator._execute_agent(WorkflowPhase.SYNTHESIS)
        return dict(orchestrator.shared_state.state)

    async def editing_node(state: NewsletterState) -> dict:
        """Execute editing phase."""
        orchestrator.shared_state.update_state(**state)
        await orchestrator._execute_agent(WorkflowPhase.EDITING)
        return dict(orchestrator.shared_state.state)

    async def visuals_node(state: NewsletterState) -> dict:
        """Execute visuals phase."""
        orchestrator.shared_state.update_state(**state)
        await orchestrator._execute_agent(WorkflowPhase.VISUALS)
        return dict(orchestrator.shared_state.state)

    async def multimedia_node(state: NewsletterState) -> dict:
        """Execute multimedia phase."""
        orchestrator.shared_state.update_state(**state)
        await orchestrator._execute_agent(WorkflowPhase.MULTIMEDIA)
        return dict(orchestrator.shared_state.state)

    async def assembly_node(state: NewsletterState) -> dict:
        """Execute assembly phase."""
        orchestrator.shared_state.update_state(**state)
        await orchestrator._execute_agent(WorkflowPhase.ASSEMBLY)
        state_dict = dict(orchestrator.shared_state.state)
        state_dict["is_complete"] = True
        state_dict["current_phase"] = "complete"
        return state_dict

    # Add nodes
    workflow.add_node("query_formulation", query_formulation_node)
    workflow.add_node("research", research_node)
    workflow.add_node("tui_analysis", tui_analysis_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("editing", editing_node)
    workflow.add_node("visuals", visuals_node)
    workflow.add_node("multimedia", multimedia_node)
    workflow.add_node("assembly", assembly_node)

    # Set entry point
    workflow.set_entry_point("query_formulation")

    # Add edges (sequential flow)
    workflow.add_edge("query_formulation", "research")
    workflow.add_edge("research", "tui_analysis")
    workflow.add_edge("tui_analysis", "synthesis")
    workflow.add_edge("synthesis", "editing")
    workflow.add_edge("editing", "visuals")
    workflow.add_edge("visuals", "multimedia")
    workflow.add_edge("multimedia", "assembly")
    workflow.add_edge("assembly", END)

    return workflow.compile()


# ============== Convenience Function ==============

async def generate_newsletter(
    topic: str,
    target_audience: str = "TUI Leadership and Strategy Teams",
    key_concepts: Optional[list[str]] = None,
    sub_topics: Optional[list[dict]] = None,
    output_dir: str = "output",
) -> SharedState:
    """
    High-level function to generate a complete newsletter.

    Args:
        topic: The newsletter topic
        target_audience: Target audience description
        key_concepts: Optional list of key concepts
        sub_topics: Optional list of subtopics
        output_dir: Base output directory

    Returns:
        SharedState with all artifacts
    """
    # Import agents here to avoid circular imports
    from src.agents.query_formulation_agent import create_query_formulation_agent
    from src.agents.research_agent import create_research_agent
    from src.agents.tui_strategy_agent import create_tui_strategy_agent
    from src.agents.synthesis_agent import create_synthesis_agent
    from src.agents.hbr_editor_agent import create_hbr_editor_agent
    from src.agents.visual_asset_agent import create_visual_asset_agent
    from src.agents.multimedia_agent import create_multimedia_agent
    from src.agents.assembly_agent import create_assembly_agent

    config = OrchestratorConfig(output_base_dir=output_dir)
    orchestrator = Orchestrator(config)

    # Register Phase 2 agents (Research Pipeline)
    orchestrator.register_agent(WorkflowPhase.QUERY_FORMULATION, create_query_formulation_agent)
    orchestrator.register_agent(WorkflowPhase.RESEARCH, create_research_agent)
    orchestrator.register_agent(WorkflowPhase.TUI_ANALYSIS, create_tui_strategy_agent)

    # Register Phase 3 agents (Content Creation)
    orchestrator.register_agent(WorkflowPhase.SYNTHESIS, create_synthesis_agent)
    orchestrator.register_agent(WorkflowPhase.EDITING, create_hbr_editor_agent)

    # Register Phase 4 agents (Multimedia & Assembly)
    orchestrator.register_agent(WorkflowPhase.VISUALS, create_visual_asset_agent)
    orchestrator.register_agent(WorkflowPhase.MULTIMEDIA, create_multimedia_agent)
    orchestrator.register_agent(WorkflowPhase.ASSEMBLY, create_assembly_agent)

    return await orchestrator.run(
        topic=topic,
        target_audience=target_audience,
        key_concepts=key_concepts,
        sub_topics=sub_topics,
    )
