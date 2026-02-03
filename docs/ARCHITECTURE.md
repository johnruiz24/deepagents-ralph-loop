# Architecture Documentation

## System Overview

The Agent Newsletter System is a multi-agent architecture designed to produce HBR-quality newsletters for TUI Group leadership. The system follows a sequential pipeline with quality gates at each phase.

## Core Components

### 1. Orchestrator (`src/orchestrator/orchestrator.py`)

The central coordinator that:
- Initializes shared state for each run
- Invokes agents in sequence
- Handles errors with exponential backoff retry
- Tracks execution progress and timing
- Enforces quality gates between phases

```python
class WorkflowPhase(Enum):
    QUERY_FORMULATION = "query_formulation"
    RESEARCH = "research"
    TUI_ANALYSIS = "tui_analysis"
    SYNTHESIS = "synthesis"
    EDITING = "editing"
    VISUALS = "visuals"
    MULTIMEDIA = "multimedia"
    ASSEMBLY = "assembly"
    COMPLETE = "complete"
```

### 2. Shared State (`src/state/shared_state.py`)

File-based state management that persists artifacts across agents:

```
shared_state/
├── input/           # User prompt, topics
├── research/        # Research plan, raw data, TUI analysis
├── content/         # Draft and final articles
├── visuals/         # Generated charts and diagrams
├── multimedia/      # Audio narration
└── final_deliverables/  # PDF, HTML, ZIP
```

### 3. Agents (`src/agents/`)

Each agent is a specialized processor:

| Agent | Input | Output | LLM Calls |
|-------|-------|--------|-----------|
| QueryFormulation | Topic | Search queries | 1 |
| Research | Queries | Raw research data | 5-10 (parallel) |
| TUIStrategy | Research | TUI-contextualized analysis | 1 |
| Synthesis | Analysis | Draft narrative | 1 |
| HBREditor | Draft | Polished article | 1-2 |
| VisualAsset | Article | PNG charts/diagrams | 0 (matplotlib) |
| Multimedia | Article | MP3 narration | 0 (Polly API) |
| Assembly | All artifacts | PDF, HTML, ZIP | 0 |

### 4. Quality Gates (`src/quality_gates/`)

Validation at each phase transition:

- **Research Validator**: Source count, diversity, recency
- **Writing Validator**: Word count, readability, structure
- **Publishing Validator**: Asset completeness, PDF validity

## Data Flow

```
User Topic
    │
    ▼
┌─────────────────────┐
│ Query Formulation   │ → search_queries.json
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Parallelized        │ → raw_data/*.md
│ Research            │   (5-10 sources)
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ TUI Strategy        │ → tui_strategy_summary.md
│ Analysis            │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Synthesis &         │ → draft_article.md
│ Narrative           │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ HBR Style           │ → final_article.md
│ Editor              │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Visual Assets       │ → chart_*.png
│ (matplotlib/diagrams)│   diagram_*.png
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Multimedia          │ → narration_*.mp3
│ (Amazon Polly)      │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Final Assembly      │ → newsletter_*.pdf
│ (WeasyPrint)        │   newsletter_*.html
│                     │   newsletter_*.zip
└─────────────────────┘
```

## Technology Stack

### LLM Integration
- **Provider**: AWS Bedrock
- **Model**: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022-v2:0)
- **Framework**: LangChain + LangGraph

### Visual Generation
- **Charts**: matplotlib + seaborn (300 DPI)
- **Diagrams**: `diagrams` library (architecture diagrams)
- **Style**: Professional, publication-ready

### Audio Generation
- **Primary**: Amazon Polly (Neural voices)
- **Fallback**: OpenAI TTS
- **Format**: MP3

### Document Generation
- **PDF**: WeasyPrint (HTML → PDF with embedded images)
- **HTML**: Jinja2 templates with inline CSS

## Error Handling

The orchestrator implements exponential backoff retry:

```python
@dataclass
class OrchestratorConfig:
    max_retries_per_agent: int = 3
    retry_base_delay: float = 1.0  # seconds
    retry_max_delay: float = 60.0  # seconds
    max_total_duration: float = 1800.0  # 30 minutes
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AWS_REGION` | Yes | AWS region for Bedrock/Polly |
| `TAVILY_API_KEY` | Yes | Web search API |
| `OPENAI_API_KEY` | No | TTS fallback |
| `LANGCHAIN_API_KEY` | No | LangSmith tracing |

## Future Enhancements

1. **Skills Architecture**: Refactor agents to use skills as tools
2. **Parallel Execution**: Run independent agents concurrently
3. **Custom Templates**: User-configurable newsletter templates
4. **Multi-Language**: Support for multiple output languages
