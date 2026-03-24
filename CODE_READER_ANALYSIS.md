# InkForge Ralph Project - Comprehensive Code Analysis

**Project**: InkForge Ralph Mode - Advanced Newsletter Generation System
**Created**: 2025-03-24
**Scope**: Complete Python codebase analysis for article documentation

---

## Executive Summary

InkForge Ralph is an autonomous, iterative newsletter generation system built on the **Ralph Loop** pattern (pioneered by Geoff Huntley/DeepAgents). The system implements a 9-agent pipeline that transforms topics into publication-ready newsletters with HBR-quality content, professional visuals, and multimedia assets.

**Key Architecture**:
- Stateful iteration model with fresh context per loop
- Filesystem as persistent memory (git-backed audit trail)
- MapReduce parallelization for research
- Quality gates between workflow stages
- Bedrock Claude + OpenAI GPT-4o (fallback)

---

## Table of Contents

1. [Ralph Loop Implementation](#ralph-loop-implementation)
2. [Agent Architecture](#agent-architecture)
3. [State Persistence](#state-persistence)
4. [Workflow Pipeline](#workflow-pipeline)
5. [Key Components](#key-components)
6. [File Organization](#file-organization)
7. [Integration Points](#integration-points)

---

## Ralph Loop Implementation

### Main Entry Point
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/ralph_mode.py` (1,612 lines)

#### Core Concept (Lines 3-27)
Ralph Mode creates an **autonomous looping pattern** where:
- Each iteration receives **fresh context** (agent re-initializes)
- **Filesystem and git serve as persistent memory** between iterations
- Agent checks state.json to understand current progress
- Agent performs ONE meaningful unit of work (one stage transition)
- Git commits create audit trail
- Agent is stateless between iterations

#### Stage Machine (Lines 107-119)
```python
class Stage(str, Enum):
    INITIALIZED = "INITIALIZED"
    QUERY_FORMULATION = "QUERY_FORMULATION"
    RESEARCHING = "RESEARCHING"
    TUI_ANALYSIS = "TUI_ANALYSIS"
    SYNTHESIZING = "SYNTHESIZING"
    HBR_EDITING = "HBR_EDITING"
    VISUAL_GENERATION = "VISUAL_GENERATION"
    MULTIMEDIA_PRODUCTION = "MULTIMEDIA_PRODUCTION"
    ASSEMBLY = "ASSEMBLY"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
```

**Total**: 11 distinct stages forming the newsletter generation pipeline.

#### Ralph Iteration Function (Lines 1016-1134)
```python
async def ralph_iteration(
    agent,
    backend,
    workspace: Path,
    iteration: int,
    task: str,
    config: InkForgeConfig
) -> bool
```

**Flow**:
1. Load current state from `state.json`
2. Build iteration prompt with error notices (self-correction)
3. Execute agent via LangGraph API (not deprecated execute_task)
4. Load updated state
5. Track history and git commits
6. Send webhook notifications on stage changes
7. Return whether to continue

**Key Detail (Lines 1029-1042)**: Self-correcting JSON error detection
- If state has `_json_error`, agent MUST fix it before proceeding
- This is a built-in self-correction mechanism

#### Main Ralph Loop (Lines 1300-1374)
```python
while True:
    # Run iteration
    should_continue = await ralph_iteration(...)

    # Check for completion
    if not should_continue:
        # Final commit and deliverables reporting
        break

    # Check iteration limit
    if config.max_iterations > 0 and iteration >= config.max_iterations:
        break

    iteration += 1
```

**Terminal Condition**: Stage reaches `COMPLETED` or iteration limit exceeded.

### System Prompt (Lines 586-675)
The agent receives a detailed system prompt that explains:
- Ralph mode principles (fresh context, filesystem memory)
- Directory structure and file locations
- State machine stages with quality gates
- Available tools (InkForge-specific functions)
- Iteration workflow (read state → do work → update state → log)

**Critical Instructions (Line 1063)**:
```
When writing JSON, always validate it is correct. No duplicate keys, proper commas.
```

### State Management (Lines 857-911)
```python
def create_initial_state(
    topic: str,
    key_concepts: List[str],
    target_audience: str
) -> dict
```

**Initial State Structure**:
- `topic`, `key_concepts`, `target_audience`
- `stage`: Starts at `INITIALIZED`
- `iteration`: Tracks current iteration number
- `research_plan`, `research_completed`, `tui_analysis_completed`
- `draft_article_path`, `final_article_path`, `word_count`
- `visual_assets`, `multimedia`, `final_deliverables`
- `errors`, `history` (stage transitions), `git_commits` (audit trail)
- `quality_scores` (per-stage tracking)

**Persistence (Lines 906-911)**:
```python
def save_state(workspace: Path, state: dict):
    """Save state to workspace."""
    state["updated_at"] = datetime.now().isoformat()
    state_file = workspace / "state.json"
    state_file.write_text(json.dumps(state, indent=2, default=str))
```

### Git Integration (Lines 720-851)
**Repository Initialization (Lines 720-740)**:
- Creates `.git` in workspace
- Generates `.gitignore` (filters media files)
- Returns success/failure status

**Commit System (Lines 743-808)**:
```python
def git_commit(
    workspace: Path,
    message: str,
    config: GitConfig
) -> Optional[str]
```
- Sets git config (author name/email from config)
- Stages all changes (`git add -A`)
- Creates commit with message
- Returns 8-char commit hash
- **Triggered on**: stage changes, iterations, completion

**Git History (Lines 811-834)**:
- Retrieves recent commits for audit trail
- Formats as: `{hash}|{message}|{datetime}`

**Resume Functionality (Lines 923-964)**:
- `list_available_checkpoints()`: Lists git commits + state history
- `resume_from_checkpoint()`: Restores state from specific commit
- Enables recovery from any previous state

### Webhook Notifications (Lines 682-713)
```python
async def send_webhook(
    config: WebhookConfig,
    event: str,
    data: Dict[str, Any]
) -> bool
```

**Events**: `stage_change`, `iteration_complete`, `error`

**Payload Structure**:
```json
{
  "event": "stage_change",
  "timestamp": "2025-03-24T...",
  "data": {
    "previous_stage": "QUERY_FORMULATION",
    "current_stage": "RESEARCHING",
    "iteration": 2,
    "workspace": "..."
  }
}
```

### Custom Tools for Ralph Agent (Lines 234-579)
Eight @tool decorated async functions serve as Ralph's interface to InkForge agents:

1. **`inkforge_generate_research_plan`** (Lines 235-276)
   - Input: topic, key_concepts_json, target_audience, output_dir
   - Invokes QueryFormulationAgent
   - Returns: research_plan_path, quality_score

2. **`inkforge_execute_research`** (Lines 278-318)
   - Runs ParallelizedResearchAgent
   - Returns: sources_collected count, quality_score

3. **`inkforge_tui_analysis`** (Lines 320-355)
   - Runs TUIStrategyAgent
   - Returns: tui_summary_path, quality_score

4. **`inkforge_synthesize_article`** (Lines 357-398)
   - Runs SynthesisAgent
   - Returns: draft_path, word_count, quality_score

5. **`inkforge_hbr_edit`** (Lines 400-442)
   - Runs HBREditorAgent
   - Returns: final_article_path, word_count, in_target_range

6. **`inkforge_generate_visuals`** (Lines 444-483)
   - Runs VisualAssetAgent
   - Returns: visuals_count, visual_files list

7. **`inkforge_produce_multimedia`** (Lines 485-525)
   - Runs MultimediaAgent
   - Returns: audio_files, video_files lists

8. **`inkforge_assemble_deliverables`** (Lines 527-579)
   - Runs AssemblyAgent
   - Returns: deliverables dict (pdf, html, zip paths)

### Exponential Backoff Retry (Lines 186-227)
```python
async def with_exponential_backoff(
    func: Callable,
    *args,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    **kwargs
) -> Any
```

**Strategy**:
- Retry up to N times on failure
- Delay = `base_delay * (2 ^ attempt) + random(0,1)` capped at max_delay
- Used for resilience against API rate limits

### Agent Creation (Lines 971-1009)
```python
def create_inkforge_agent(config: InkForgeConfig, custom_tools: List = None)
```

**LLM Selection Logic**:
1. Try Bedrock first with retries
2. Fall back to OpenAI GPT-4o if Bedrock fails
3. Returns: (agent, backend, active_model)

---

## Agent Architecture

### Base Agent Class
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/agents/base_agent.py` (417 lines)

#### Core Design Pattern (Lines 60-326)
All agents inherit from `BaseAgent[TInput, TOutput]` - generic base class defining execution flow:

```python
class BaseAgent(ABC, Generic[TInput, TOutput]):
    agent_name: str = "BaseAgent"
    phase: str = "unknown"
    max_retries: int = 3
    retry_min_wait: int = 1  # seconds
    retry_max_wait: int = 60  # seconds
```

#### Execution Pipeline (Lines 147-220)
```python
async def execute(self) -> AgentResult:
    """
    Flow:
    1. Read inputs from state
    2. Process with retry logic
    3. Validate output
    4. Write to state
    5. Signal completion
    """
```

**Standard Result** (Lines 39-57):
```python
@dataclass
class AgentResult:
    success: bool
    output: Optional[Any] = None
    quality_score: float = 0.0
    message: str = ""
    duration_ms: float = 0.0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
```

#### Abstract Methods All Agents Must Implement
1. **`read_from_state()`** (Lines 96-107): Extract inputs from SharedState
2. **`process()`** (Lines 109-120): Perform the agent's core task
3. **`write_to_state()`** (Lines 122-130): Write outputs back to SharedState
4. **`validate_output()`** (Lines 132-143): Check quality gates
5. **`calculate_quality_score()`** (Lines 279-291): Score the output (0-100)

#### Retry Mechanism (Lines 222-248)
Uses **tenacity** library for exponential backoff:
```python
@retry(
    stop=stop_after_attempt(self.max_retries),
    wait=wait_exponential(min=1, max=60),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, ...)),
    reraise=True,
)
```

#### LLM Agent Subclass (Lines 328-388)
```python
class LLMAgent(BaseAgent[TInput, TOutput]):
    def __init__(self, shared_state, llm=None, logger=None):
        self._llm = llm
        self._tokens_used = 0

    @property
    def llm(self):
        """Lazy-load Bedrock LLM"""
        if self._llm is None:
            from src.utils.bedrock_config import create_bedrock_llm
            self._llm = create_bedrock_llm()
        return self._llm

    async def invoke_llm(self, prompt: str, **kwargs) -> str:
        """Invoke LLM with tenacity retry"""
```

### Agent 1: Query Formulation Agent
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/agents/query_formulation_agent.py` (381 lines)

**Purpose**: Transform topic into structured research plan with optimized queries

**Input** (Lines 33-38):
```python
@dataclass
class QueryFormulationInput:
    topic: str
    key_concepts: list[str]
    sub_topics: list[dict]
    target_audience: str
```

**Process** (Lines 141-195):
1. Get relevant sources from MASTER_SOURCE_LIST using keyword matching
2. Always include TUI source (mandatory)
3. Call LLM with QUERY_FORMULATION_PROMPT (Lines 61-103)
4. Parse JSON response into SubTopicPlan objects
5. If parsing fails, use fallback plan generation

**Output** (Lines 51-58):
```python
@dataclass
class ResearchPlan:
    main_topic: str
    target_audience: str
    sub_topic_plans: list[SubTopicPlan]  # Each has queries, sources, focus_areas
    tui_source: str
    total_sources: int
    generated_at: str
```

**Quality Validation** (Lines 226-248):
- Must have sub-topic plans
- Each sub-topic needs 2+ queries and 2+ sources
- TUI source MUST be included
- Quality scoring: 40% plans + 20% queries + 20% sources + 10% TUI + 10% focus_areas

**Output Writing** (Lines 197-224):
Saves research_plan.json and updates shared_state

### Agent 2: Parallelized Research Agent
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/agents/research_agent.py` (670 lines)

**Purpose**: Execute parallelized research across sub-topics using MapReduce pattern

**Architecture** (Lines 86-163):
- **ResearchSubAgent**: Sub-agent for single sub-topic
- **ParallelizedResearchAgent**: Orchestrator spawning 5-10 concurrent sub-agents

#### MapReduce Execution (Lines 478-557)

**MAP Phase** (Lines 488-510):
```python
semaphore = asyncio.Semaphore(self.config.max_concurrent_agents)

async def run_with_semaphore(agent):
    async with semaphore:
        return await agent.execute()

results = await asyncio.gather(
    *[run_with_semaphore(agent) for agent in sub_agents],
    return_exceptions=True,
)
```

Spawns up to 5 concurrent agents (configurable).

**ResearchSubAgent Tasks** (Lines 113-163):
1. Execute searches (Tavily API or mock data)
2. Extract full text from URLs (via trafilatura or BeautifulSoup)
3. Save articles as markdown to raw_data/{subtopic}/{filename}.md
4. Return SubTopicResearchResult

**REDUCE Phase** (Lines 518-557):
- Combine all results
- Calculate quality score (40% articles + 30% coverage + 20% sources + 10% baseline)
- Generate research summary markdown

**Article Structure** (Lines 54-62):
```python
@dataclass
class Article:
    title: str
    url: str
    content: str          # Full text, not snippet!
    source: str
    extracted_at: str
    word_count: int
    subtopic: str
```

**Config** (Lines 43-50):
```python
max_concurrent_agents: int = 5
request_timeout: float = 30.0
rate_limit_delay: float = 1.0
max_articles_per_subtopic: int = 10
min_article_length: int = 500
```

### Agent 3: TUI Strategy Agent
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/agents/tui_strategy_agent.py`

**Purpose**: Analyze research through TUI's strategic lens (MANDATORY for TUI newsletters)

**Ensures**: Content is specifically relevant to TUI's business context, not generic analysis

### Agent 4: Synthesis Agent
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/agents/synthesis_agent.py` (150+ lines)

**Purpose**: Create draft article from research using HBR model

**Input** (Lines 28-34):
```python
@dataclass
class SynthesisInput:
    topic: str
    target_audience: str
    research_data: dict[str, list[dict]]  # subtopic -> articles
    tui_strategy: str
    combined_research_summary: str
```

**Multi-Stage Process** (Lines 51-150+):

1. **Insight Extraction Phase**:
   - Extract 5-7 KEY INSIGHTS (backed by evidence)
   - Extract 2-3 COUNTERINTUITIVE INSIGHTS (challenge conventional wisdom)
   - Extract 3-5 TUI-SPECIFIC IMPLICATIONS
   - LLM parses structured JSON response

2. **Article Structuring Phase** (Lines 96-150+):
   - Title + Subtitle
   - Hook section (250-300 words): Problem/opportunity
   - Context setting (300-350 words): Current state
   - **Core Analysis (1400-1700 words)**: Multi-dimensional exploration of 10-12 distinct dimensions
   - Implications for TUI
   - Conclusion

**Output** (Lines 38-48):
```python
@dataclass
class DraftArticle:
    title: str
    subtitle: str
    content: str
    word_count: int
    sections: list[dict]
    key_insights: list[str]
    counterintuitive_insights: list[str]  # CRITICAL!
    citations: list[dict]
    reading_time_minutes: float
```

**Key Principle (Line 13)**: "THE MOST CRITICAL AGENT for content quality. Harvard Business Review level - NON-NEGOTIABLE!"

### Agent 5: HBR Editor Agent
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/agents/hbr_editor_agent.py`

**Purpose**: Polish draft article to HBR standards, ensure 2000-2500 word count

**Quality Gate**:
- Word count MUST be 2000-2500 (hard constraint)
- Readability score ≥ 60
- HBR quality score ≥ 85

### Agent 6: Visual Asset Agent
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/agents/visual_asset_agent.py` (150+ lines)

**Purpose**: Generate professional visual assets using skills as tools

**Tools Available** (Lines 110-118):
```python
self.tools = {
    "generate_chart": generate_chart,
    "generate_investment_chart": generate_investment_chart,
    "generate_efficiency_chart": generate_efficiency_chart,
    "generate_architecture": generate_architecture,
    "generate_tui_vs_ota_diagram": generate_tui_vs_ota_diagram,
    "generate_timeline": generate_timeline,
    "generate_market_trajectory": generate_market_trajectory,
}
```

**Quality Standards** (Lines 100-103):
```python
MIN_ASSETS = 3
MAX_ASSETS = 5
MIN_DPI = 300              # Professional quality
MIN_FILE_SIZE = 50000      # 50KB minimum (substantive images)
```

**Process** (Lines 137-150+):
1. Extract structured data from article using LLM
2. Generate framework/dimensional charts
3. Generate architecture diagrams
4. Generate timeline/trajectory visualizations
5. Validate each asset meets quality standards

### Agent 7: Multimedia Agent
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/agents/multimedia_agent.py`

**Purpose**: Generate audio (MP3) and video (MP4) versions

**Constraints**:
- Video: exactly 60 ± 2 seconds
- Audio: full article narration
- Quality: professional production standards

### Agent 8: Assembly Agent
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/agents/assembly_agent.py`

**Purpose**: Produce final deliverables (PDF, HTML, ZIP package)

**Outputs**:
- PDF: Professional formatted document
- HTML: Interactive web version
- ZIP: Complete package with all assets

### Agent 9: Orchestrator
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/orchestrator/orchestrator.py` (482 lines)

**Purpose**: Coordinate all agents in sequence, handle retries and errors

#### Orchestrator Class (Lines 65-329)

**Configuration** (Lines 55-62):
```python
@dataclass
class OrchestratorConfig:
    max_retries_per_agent: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0
    max_total_duration: float = 1800.0  # 30 minutes
```

**Main Run Method** (Lines 108-209):
```python
async def run(
    self,
    topic: str,
    target_audience: str = "TUI Leadership and Strategy Teams",
    key_concepts: Optional[list[str]] = None,
    sub_topics: Optional[list[dict]] = None,
) -> SharedState
```

**Workflow Phases** (Lines 158-167):
```python
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
```

**Execution with Retry** (Lines 169-186):
```python
for phase in phases:
    if self._is_timed_out():
        raise TimeoutError(...)

    success = await self._execute_phase_with_retry(phase)

    if not success:
        if phase in [WorkflowPhase.RESEARCH, WorkflowPhase.TUI_ANALYSIS]:
            raise RuntimeError(f"Critical phase {phase.value} failed")
```

**Phase Retry Logic** (Lines 211-284):
```python
async def _execute_phase_with_retry(self, phase: WorkflowPhase) -> bool:
    for attempt in range(self.config.max_retries_per_agent):
        try:
            self.shared_state.set_phase(phase.value)
            await self._execute_agent(phase)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                await asyncio.sleep(delay)
    return False
```

---

## State Persistence

### SharedState Class
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/state/shared_state.py` (458 lines)

#### Design (Lines 41-76)
```python
@dataclass
class SharedState:
    """Hierarchical shared state manager"""
    output_dir: Path
    state: NewsletterState  # In-memory tracking
    created_at: datetime
    updated_at: datetime
```

**Principle**: Combines **in-memory state** (for workflow) with **file-based artifacts** (for persistence)

#### Directory Structure (Lines 63-75)
```python
def _ensure_directories(self):
    directories = [
        self.input_dir,
        self.research_dir,
        self.research_dir / "raw_data",    # Per-subtopic: raw_data/{subtopic}/*.md
        self.content_dir,
        self.visuals_dir,
        self.multimedia_dir,
        self.final_deliverables_dir,
    ]
```

**Full Hierarchy**:
```
output/
├── input/
│   ├── user_prompt.json
│   └── topics_and_subtopics.json
├── research/
│   ├── research_plan.json
│   ├── raw_data/
│   │   ├── subtopic_1/
│   │   │   ├── article_1.md
│   │   │   └── article_2.md
│   │   └── subtopic_2/
│   ├── tui_strategy_summary.md
├── content/
│   ├── draft_article.md
│   └── final_article.md
├── visuals/
│   ├── chart_1.png
│   ├── diagram_1.png
│   └── timeline_1.png
├── multimedia/
│   ├── audio_version.mp3
│   └── promo_video.mp4
├── final_deliverables/
│   ├── Leadership_Strategy_Newsletter.pdf
│   ├── Leadership_Strategy_Newsletter.html
│   └── newsletter_package.zip
└── state_snapshot.json
```

#### State Operations

**Read/Write** (Lines 116-130):
```python
def update_state(self, **kwargs):
    for key, value in kwargs.items():
        self.state[key] = value
    self.updated_at = datetime.now()

def get_state_field(self, field: str):
    return self.state.get(field)
```

**Input Operations** (Lines 134-171):
- `write_user_prompt()`: Saves topic, audience, concepts
- `write_topics_and_subtopics()`: Saves subtopic list
- `read_user_prompt()`: Loads input metadata

**Research Operations** (Lines 175-246):
- `write_research_plan()`: Saves research_plan.json
- `read_research_plan()`: Loads plan
- `write_research_data()`: Saves articles by subtopic
- `read_all_research_data()`: Loads all articles organized by subtopic
- `write_tui_strategy_summary()`: Saves strategy analysis
- `read_tui_strategy_summary()`: Loads strategy

**Content Operations** (Lines 250-282):
- `write_draft_article()`: Saves draft_article.md
- `write_final_article()`: Saves final_article.md
- `read_draft_article()`: Loads draft
- `read_final_article()`: Loads final

**Visual Operations** (Lines 286-306):
- `write_visual()`: Saves image bytes to visuals/
- `copy_visual()`: Copies from external location
- `list_visuals()`: Returns all PNG files

**Multimedia Operations** (Lines 310-326):
- `write_audio()`: Saves MP3 to multimedia/
- `write_video()`: Saves MP4 to multimedia/

**Deliverables Operations** (Lines 330-355):
- `write_pdf()`: Saves to final_deliverables/
- `write_html()`: Saves to final_deliverables/
- `create_archive()`: Creates ZIP of deliverables

**Quality Gate Recording** (Lines 359-378):
```python
def record_gate_passed(self, gate_name: str):
    passed = list(self.state.get("quality_gates_passed", []))
    passed.append(gate_name)
    self.update_state(quality_gates_passed=passed)

def record_gate_failed(self, gate_name: str, reason: str = ""):
    failed = list(self.state.get("quality_gates_failed", []))
    failed.append(f"{gate_name}: {reason}")
    self.update_state(quality_gates_failed=failed)
```

**Serialization** (Lines 399-419):
```python
def save_state_snapshot(self) -> Path:
    """Save snapshot of in-memory state"""
    snapshot = {
        "state": dict(self.state),
        "created_at": self.created_at.isoformat(),
        "updated_at": self.updated_at.isoformat(),
    }
    path = self.output_dir / "state_snapshot.json"
    path.write_text(json.dumps(snapshot, indent=2, default=str))

def load_state_snapshot(self) -> bool:
    """Restore state from snapshot"""
    path = self.output_dir / "state_snapshot.json"
    if path.exists():
        snapshot = json.loads(path.read_text())
        for key, value in snapshot["state"].items():
            self.state[key] = value
        return True
    return False
```

### Newsletter State Definition
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/state/newsletter_state.py` (209 lines)

#### TypedDict Schema (Lines 6-100)
```python
class NewsletterState(TypedDict):
    # INPUT
    topic: str
    target_audience: Optional[str]
    key_concepts: list[str]
    sub_topics: list[dict]

    # PHASE 1: QUERY_FORMULATION
    research_plan: Optional[dict]
    query_formulation_iteration: int

    # PHASE 2: PARALLELIZED RESEARCH
    research_results: list[dict]
    combined_research: Optional[dict]
    research_quality_score: float
    research_iteration: int

    # PHASE 3: TUI STRATEGY ANALYSIS
    tui_analysis: Optional[dict]
    tui_strategic_priorities: list[str]
    tui_relevance_score: float
    tui_iteration: int

    # PHASE 4: SYNTHESIS & NARRATIVE
    synthesized_content: Optional[dict]
    narrative_outline: list[dict]
    synthesis_iteration: int

    # PHASE 5: HBR STYLE EDITOR
    article_content: str
    article_sections: list[dict]
    word_count: int          # MUST be 2000-2500
    readability_score: float
    hbr_quality_score: float
    editing_iteration: int

    # PHASE 6: VISUAL ASSETS
    generated_images: list[dict]
    hero_images: list[dict]
    diagrams: list[dict]
    charts: list[dict]
    visual_quality_score: float
    visual_iteration: int

    # PHASE 7: MULTIMEDIA
    audio_script: str
    audio_path: Optional[str]
    audio_duration_seconds: float
    audio_quality_score: float
    video_script: str
    video_path: Optional[str]
    video_duration_seconds: float  # MUST be 60 ± 2 seconds
    video_quality_score: float
    multimedia_iteration: int

    # PHASE 8: FINAL ASSEMBLY
    article_package_path: str
    pdf_path: Optional[str]
    html_path: Optional[str]
    archive_path: Optional[str]
    publishing_package: Optional[dict]
    assembly_iteration: int

    # QUALITY GATES & CONTROL
    quality_gates_passed: list[str]
    quality_gates_failed: list[str]
    iteration_count: int
    current_phase: Literal[...phases...]
    error_messages: list[str]
    is_complete: bool
```

#### Quality Thresholds (Lines 198-208)
```python
QUALITY_THRESHOLDS = {
    "research_quality_min": 85,
    "source_count_min": 5,
    "article_word_count_min": 2000,
    "article_word_count_max": 2500,
    "readability_min": 60,
    "hbr_quality_min": 85,
    "video_duration_target": 60,
    "video_duration_tolerance": 2,
    "max_iterations_per_phase": 3,
}
```

---

## Workflow Pipeline

### Sequential Execution
**Files**: `run_ralph_style.py`, `run_cli.py`

#### Ralph-Style Runner
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/run_ralph_style.py` (387 lines)

**Purpose**: Show iteration-by-iteration progress with visual feedback

**Flow** (Lines 253-372):
```python
async def main():
    # Initialize shared_state
    shared_state = create_shared_state(
        topic="Universal Commerce Protocol (UCP)",
        target_audience="TUI Leadership and Strategy Teams",
        key_concepts=[...],
        output_base_dir="output",
    )

    # Save initial state.json
    state_file = workspace / "state.json"
    state_file.write_text(json.dumps({
        "stage": "QUERY_FORMULATION",
        "iteration": 0,
        ...
    }, indent=2))

    phases = [
        ("Query Formulation", create_query_formulation_agent),
        ("Parallelized Research", create_research_agent),
        ("TUI Strategy Analysis", create_tui_strategy_agent),
        ("Synthesis", create_synthesis_agent),
        ("HBR Editing", create_hbr_editor_agent),
        ("Visual Assets", create_visual_asset_agent),
        ("Multimedia", create_multimedia_agent),
        ("Final Assembly", create_assembly_agent),
    ]

    for i, (name, factory) in enumerate(phases, 1):
        # Update state.json with current phase
        state["stage"] = name.upper().replace(" ", "_")
        state["iteration"] = i
        state_file.write_text(json.dumps(state, indent=2))

        # Execute phase
        success, result = await run_phase(factory, shared_state, name, i, log_file)
        results[name] = success
```

**Visual Output** (Lines 48-62):
- Iteration headers with phase numbers
- Timestamps for each action
- State diffs (before/after values)
- Result status (✅ PASSED / ❌ FAILED)
- Quality scores and execution time

**Iteration Logging** (Lines 65-75):
```python
def write_iteration_log(log_file: Path, iteration: int, phase: str, actions: list, result: dict):
    with open(log_file, "a") as f:
        f.write(f"\n## Iteration {iteration}\n")
        f.write(f"Phase: {phase}\n")
        for action in actions:
            f.write(f"- {action}\n")
        f.write(f"Result: {'PASSED' if result.get('success') else 'FAILED'}\n")
        f.write(f"Quality: {result['quality_score']:.0f}/100\n")
```

#### Standard CLI Runner
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/run_cli.py` (211 lines)

**Purpose**: Simple phased execution with summary output

**Flow** (Lines 121-195):
```python
async def main():
    # Initialize
    orchestrator = Orchestrator(shared_state)

    # Define phases
    phases = [
        ("Query Formulation", orchestrator.run_query_formulation),
        ("Parallelized Research", orchestrator.run_research),
        ("TUI Strategy Analysis", orchestrator.run_tui_strategy),
        ("Synthesis", orchestrator.run_synthesis),
        ("HBR Editing", orchestrator.run_editing),
        ("Visual Assets", orchestrator.run_visuals),
        ("Multimedia", orchestrator.run_multimedia),
        ("Final Assembly", orchestrator.run_assembly),
    ]

    # Execute each phase
    for i, (name, func) in enumerate(phases, 1):
        result = await run_phase(name, func, i, total_phases)
        results[name] = result

    # Show summary
    print_output_summary(output_dir)
```

---

## Key Components

### Configuration & Setup

#### Bedrock Configuration
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/utils/bedrock_config.py`

Configures AWS Bedrock LLM:
- Profile: `mll-dev`
- Region: `eu-central-1`
- Model: `claude-sonnet-4-5-20250929`

#### Source Management
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/config/sources.py`

**MASTER_SOURCE_LIST**: Curated sources by category
- Technology publications (MIT Tech Review, TechCrunch)
- Travel industry sources (Skift, Phocuswire, UNWTO)
- Strategy sources (McKinsey, BCG, Harvard Business Review)
- News sources (Reuters, Bloomberg)

Functions:
- `get_sources_by_relevance()`: Filter by keywords
- `get_tui_source()`: Always-include TUI context source

#### Quality Validators
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/quality_gates/`

Multiple validators:
- `research_validator.py`: Validates research completeness
- `writing_validator.py`: Validates article quality
- `publishing_validator.py`: Validates deliverables
- `validators.py`: Generic validation framework

#### Logging Framework
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/src/utils/logging.py`

Provides structured logging:
```python
logger = get_agent_logger("QueryFormulationAgent", "query_formulation")
logger.info("Starting query formulation", topic=topic, num_subtopics=len(input_data.sub_topics))
logger.warning("Failed to parse LLM response", error=str(e))
logger.error("Research failed", error=error_msg)
```

### Skill Integration

#### Visual Generation Skills
**Directory**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/skills/visual_generation/generators/`

**Generators**:
- `charts.py`: Bar, line, area charts (matplotlib, seaborn)
- `architecture.py`: System diagrams (diagrams library)
- `timelines.py`: Timeline visualizations (plotly)

**Key Interface**:
```python
def generate_chart(config: ChartConfig) -> bytes:
    """Generate PNG chart at 300 DPI"""

def generate_architecture(title: str, ...) -> bytes:
    """Generate architecture diagram"""

def generate_timeline(title: str, ...) -> bytes:
    """Generate timeline visualization"""
```

### Testing Infrastructure

#### End-to-End Tests
**File**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/run_e2e_test.py`

Tests complete pipeline with sample topic

#### Unit Tests
**Directory**: `/Users/john.ruiz/Documents/projects/inkforge/ralph/tests/`

- `test_agents/`: Agent functionality tests
- `test_orchestrator/`: Orchestration tests
- `test_state/`: State management tests

---

## File Organization

### Directory Structure Summary

```
/Users/john.ruiz/Documents/projects/inkforge/ralph/
├── ralph_mode.py                    # Main Ralph loop (1,612 lines)
├── run_cli.py                       # Standard CLI runner
├── run_ralph_style.py               # Ralph-style visual runner
├── run_e2e_test.py                  # E2E tests
├── run_simple_e2e.py                # Simple tests
├── generate_images.py               # Image generation script
│
├── src/
│   ├── agents/                      # 9 agent implementations
│   │   ├── base_agent.py            # Abstract base class (417 lines)
│   │   ├── query_formulation_agent.py
│   │   ├── research_agent.py        # Parallelized research (670 lines)
│   │   ├── tui_strategy_agent.py
│   │   ├── synthesis_agent.py
│   │   ├── hbr_editor_agent.py
│   │   ├── visual_asset_agent.py
│   │   ├── multimedia_agent.py
│   │   ├── assembly_agent.py
│   │   └── __init__.py
│   │
│   ├── state/                       # State management
│   │   ├── shared_state.py          # Hierarchical state (458 lines)
│   │   ├── newsletter_state.py      # TypedDict schema (209 lines)
│   │   ├── article_state.py
│   │   └── __init__.py
│   │
│   ├── orchestrator/                # Workflow orchestration
│   │   ├── orchestrator.py          # Main orchestrator (482 lines)
│   │   └── __init__.py
│   │
│   ├── config/                      # Configuration
│   │   ├── sources.py               # Source list & filtering
│   │   └── __init__.py
│   │
│   ├── quality_gates/               # Quality validation
│   │   ├── research_validator.py
│   │   ├── writing_validator.py
│   │   ├── publishing_validator.py
│   │   ├── validators.py
│   │   └── __init__.py
│   │
│   ├── tools/                       # Utility tools
│   │   ├── web_search.py            # Web search wrapper
│   │   └── __init__.py
│   │
│   ├── utils/                       # Utilities
│   │   ├── bedrock_config.py        # AWS Bedrock setup
│   │   ├── logging.py               # Structured logging
│   │   ├── hbr_content_processor.py # HBR formatting
│   │   └── __init__.py
│   │
│   ├── image_generation/            # Image generation
│   │   ├── bedrock_image_gen.py
│   │   ├── diagram_generator.py
│   │   ├── hero_image_generator.py
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── skills/                          # Reusable skills
│   ├── visual_generation/           # Visual generation
│   │   ├── generators/
│   │   │   ├── charts.py            # Chart generation
│   │   │   ├── architecture.py      # Diagrams
│   │   │   ├── timelines.py         # Timelines
│   │   │   └── __init__.py
│   │   └── __init__.py
│   └── __init__.py
│
└── tests/                           # Test suite
    ├── test_agents/
    ├── test_orchestrator/
    ├── test_state/
    └── __init__.py
```

---

## Integration Points

### Configuration Dataclasses
**File**: `ralph_mode.py` (Lines 126-180)

```python
@dataclass
class WebhookConfig:
    url: str
    headers: Dict[str, str]
    events: List[str]
    timeout: float = 10.0

@dataclass
class GitConfig:
    enabled: bool = True
    auto_commit: bool = True
    commit_on_stage_change: bool = True
    commit_on_iteration: bool = True
    author_name: str = "Ralph Agent"
    author_email: str = "ralph@inkforge.local"

@dataclass
class ParallelConfig:
    enabled: bool = False
    max_workers: int = 3
    batch_size: int = 5

@dataclass
class BedrockConfig:
    profile: str = "mll-dev"
    region: str = "eu-central-1"
    model_id: str = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0

@dataclass
class InkForgeConfig:
    workspace_dir: Optional[str] = None
    max_iterations: int = 0  # 0 = unlimited
    model: str = f"bedrock:{BEDROCK_MODEL_ID}"
    fallback_model: str = FALLBACK_MODEL
    resume: bool = False
    webhook: Optional[WebhookConfig] = None
    git: GitConfig = field(default_factory=GitConfig)
    parallel: ParallelConfig = field(default_factory=ParallelConfig)
    bedrock: BedrockConfig = field(default_factory=BedrockConfig)
    target_audience: str = "TUI Leadership and Strategy Teams"
    word_count_target: tuple = (2000, 2500)
```

### CLI Arguments
**File**: `ralph_mode.py` (Lines 1469-1532)

Main entry point accepts:
- `--topic` (required): Newsletter topic
- `--key-concepts`: Comma-separated concepts
- `--target-audience`: Audience description
- `--iterations`: Max iterations (0 = unlimited)
- `--model`: LLM to use
- `--workspace`: Working directory
- `--resume`: Resume from existing state
- `--webhook`: Webhook URL for notifications
- `--no-git`: Disable git commits
- `--parallel`: Number of parallel workers
- `--list-checkpoints`: Show available restart points
- `--checkout`: Restore specific checkpoint

### Primary Use Cases

#### 1. Start New Newsletter Generation
```bash
python ralph_mode.py \
  --topic "Universal Commerce Protocol" \
  --key-concepts "Agentic AI,Commerce Protocols" \
  --target-audience "TUI Leadership"
```

**Result**:
- Creates workspace with timestamp + topic name
- Initializes state.json with INITIALIZED stage
- Begins ralph_iteration loop
- Produces state.json snapshots after each iteration
- Git commits track all changes

#### 2. Resume from Checkpoint
```bash
python ralph_mode.py \
  --resume \
  --workspace ./workspace/20250324_universal_commerce_protocol \
  --topic "Universal Commerce Protocol"
```

**Result**:
- Loads existing state.json
- Continues from current stage
- Preserves all prior artifacts

#### 3. Resume from Specific Commit
```bash
python ralph_mode.py \
  --list-checkpoints \
  --workspace ./workspace/20250324_universal_commerce_protocol

python ralph_mode.py \
  --workspace ./workspace/20250324_universal_commerce_protocol \
  --checkout a1b2c3d4 \
  --topic "Universal Commerce Protocol"
```

**Result**:
- Restores state from specific commit
- Resumes workflow from that point

#### 4. With Webhook Notifications
```bash
python ralph_mode.py \
  --topic "Universal Commerce Protocol" \
  --webhook "https://example.com/webhook"
```

**Result**:
- Sends events on stage changes and iterations
- Enables real-time monitoring

---

## Advanced Features

### Self-Correction Mechanism
**Lines** (ralph_mode.py 1035-1041)

If an agent writes invalid JSON to state.json:
1. System detects `_json_error` field in state
2. Next iteration receives error notice in prompt
3. Agent MUST fix the JSON before proceeding
4. Built-in error recovery

### Exponential Backoff Retry
**Lines** (ralph_mode.py 186-227)

For all LLM calls and API requests:
- Attempt 1: immediate
- Attempt 2: wait 1s + jitter
- Attempt 3: wait 2s + jitter
- Attempt 4: wait 4s + jitter
- ...
- Attempt N: wait min(60s, 2^N) + jitter

### Quality Gate System
**Lines** (shared_state.py 359-378)

Each agent validates output before writing to state:
```python
def record_gate_passed(self, gate_name: str):
    # Track successful quality gates

def record_gate_failed(self, gate_name: str, reason: str):
    # Track failed gates with reasons
```

### Multi-Dimensional Framework
**Lines** (synthesis_agent.py 132-149+)

Article explores 10-12 distinct dimensions of topic:
- Dimensions specific to topic (UCP example):
  - Data Quality as UCP Foundation
  - Unified Customer Profile
  - Cross-System Data Reconciliation
  - Real-Time Data Validation Architecture
  - AI/ML Training Data Quality
  - Master Data Management
  - Data Governance Framework
  - Data Quality Metrics & KPIs
  - Legacy System Integration Challenges
  - Partner/Supplier Data Quality
  - Data Quality ROI & Business Case
  - Competitive Moat through Data Excellence

---

## Conclusion

InkForge Ralph represents a sophisticated implementation of **autonomous, stateful iteration** for newsletter generation. Key architectural principles:

1. **Ralph Loop Pattern**: Fresh context each iteration, filesystem as persistent memory
2. **9-Agent Pipeline**: Specialized agents for each stage of content creation
3. **Quality Gates**: Hard constraints on output before advancing stages
4. **MapReduce Research**: Parallelized data gathering across subtopics
5. **State-Based Continuation**: JSON state enables full resume/restart capability
6. **Git Audit Trail**: Every iteration creates commit for full auditability
7. **Fallback Resilience**: Bedrock primary, OpenAI GPT-4o fallback
8. **Self-Correction**: JSON validation errors trigger agent self-fix in next iteration

This architecture enables **truly autonomous newsletter generation** with human oversight through checkpoints, quality gates, and detailed iteration logs.
