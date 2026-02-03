"""Agents module for the newsletter agent system."""

from src.agents.base_agent import (
    BaseAgent,
    LLMAgent,
    AgentResult,
    with_retry,
)
from src.agents.query_formulation_agent import (
    QueryFormulationAgent,
    create_query_formulation_agent,
)
from src.agents.research_agent import (
    ParallelizedResearchAgent,
    ResearchSubAgent,
    ResearchConfig,
    create_research_agent,
)
from src.agents.tui_strategy_agent import (
    TUIStrategyAgent,
    create_tui_strategy_agent,
)
from src.agents.synthesis_agent import (
    SynthesisAgent,
    create_synthesis_agent,
)
from src.agents.hbr_editor_agent import (
    HBREditorAgent,
    create_hbr_editor_agent,
)
from src.agents.visual_asset_agent import (
    VisualAssetAgent,
    create_visual_asset_agent,
)
from src.agents.multimedia_agent import (
    MultimediaAgent,
    create_multimedia_agent,
)
from src.agents.assembly_agent import (
    AssemblyAgent,
    create_assembly_agent,
)

__all__ = [
    # Base
    "BaseAgent",
    "LLMAgent",
    "AgentResult",
    "with_retry",
    # Phase 2: Research Pipeline
    "QueryFormulationAgent",
    "create_query_formulation_agent",
    "ParallelizedResearchAgent",
    "ResearchSubAgent",
    "ResearchConfig",
    "create_research_agent",
    "TUIStrategyAgent",
    "create_tui_strategy_agent",
    # Phase 3: Content Creation
    "SynthesisAgent",
    "create_synthesis_agent",
    "HBREditorAgent",
    "create_hbr_editor_agent",
    # Phase 4: Multimedia & Assembly
    "VisualAssetAgent",
    "create_visual_asset_agent",
    "MultimediaAgent",
    "create_multimedia_agent",
    "AssemblyAgent",
    "create_assembly_agent",
]
