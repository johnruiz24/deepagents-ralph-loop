# Agent Newsletter System

**A Multi-Agent System for HBR-Quality Leadership Strategy Newsletters**

Built for TUI Group's leadership team, this system generates professional, Harvard Business Review-style newsletters using a coordinated 9-agent architecture powered by Claude and AWS Bedrock.

---

## Overview

The Agent Newsletter System automates the entire newsletter production pipeline—from research and analysis to professional PDF/HTML generation with embedded visuals and audio narration.

### Key Features

- **9 Specialized AI Agents** working in orchestrated sequence
- **HBR-Quality Output** with professional charts, diagrams, and typography
- **Vertical Integration Analysis** leveraging TUI's unique market position
- **Multi-Modal Deliverables**: PDF, HTML, MP3 audio narration
- **Quality Gates** ensuring editorial standards at each phase

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                              │
│         Central coordinator managing workflow phases             │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   RESEARCH    │    │   CONTENT     │    │  PRODUCTION   │
│    PHASE      │    │    PHASE      │    │    PHASE      │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ 1. Query      │    │ 4. Synthesis  │    │ 6. Visual     │
│    Formulation│    │    & Narrative│    │    Assets     │
│ 2. Parallelized│   │ 5. HBR Style  │    │ 7. Multimedia │
│    Research   │    │    Editor     │    │ 8. Assembly   │
│ 3. TUI Strategy│   │               │    │               │
│    Analysis   │    │               │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
                                │
                                ▼
                    ┌───────────────────┐
                    │ SHARED STATE      │
                    │ (File-based)      │
                    │ • Research data   │
                    │ • Content drafts  │
                    │ • Visual assets   │
                    │ • Final outputs   │
                    └───────────────────┘
```

### Agent Descriptions

| # | Agent | Responsibility |
|---|-------|----------------|
| 1 | **Query Formulation** | Analyzes topic, generates targeted search queries |
| 2 | **Parallelized Research** | Executes web searches, aggregates sources |
| 3 | **TUI Strategy Analysis** | Contextualizes research for TUI's vertical integration |
| 4 | **Synthesis & Narrative** | Crafts compelling narrative from research |
| 5 | **HBR Style Editor** | Applies Harvard Business Review editorial standards |
| 6 | **Visual Asset Generator** | Creates professional charts and diagrams |
| 7 | **Multimedia Producer** | Generates audio narration (Amazon Polly/OpenAI TTS) |
| 8 | **Final Assembly** | Compiles PDF, HTML, and ZIP deliverables |

---

## Quick Start

### Prerequisites

- Python 3.12+
- AWS credentials configured (for Bedrock, Polly)
- Tavily API key (for web search)

### Installation

```bash
# Clone the repository
git clone git@ssh.source.tui:ml-lab/incubator/agent-newsletter.git
cd agent-newsletter

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Running the System

```bash
# Run end-to-end newsletter generation
python run_e2e_test.py

# Or use the CLI
python run_cli.py --topic "Your Newsletter Topic"
```

---

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# AWS Configuration (for Bedrock and Polly)
AWS_REGION=eu-west-1
AWS_PROFILE=default

# Web Search
TAVILY_API_KEY=your-tavily-api-key

# Optional: OpenAI for TTS fallback
OPENAI_API_KEY=your-openai-key

# Optional: LangSmith observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
```

---

## Output Structure

Each newsletter run creates a timestamped output directory:

```
output/
└── 20260203_143022_Topic_Name/
    ├── input/
    │   ├── user_prompt.json
    │   └── topics_and_subtopics.json
    ├── research/
    │   ├── research_plan.json
    │   ├── raw_data/
    │   └── tui_strategy_summary.md
    ├── content/
    │   ├── draft_article.md
    │   └── final_article.md
    ├── visuals/
    │   ├── chart_*.png
    │   └── diagram_*.png
    ├── multimedia/
    │   └── narration_*.mp3
    └── final_deliverables/
        ├── newsletter_*.pdf
        ├── newsletter_*.html
        └── newsletter_*.zip
```

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Lint with ruff
ruff check src/

# Type checking
mypy src/
```

### Project Structure

```
agent-newsletter/
├── src/
│   ├── agents/           # 8 specialized agents
│   ├── orchestrator/     # Central workflow coordinator
│   ├── state/            # Shared state management
│   ├── quality_gates/    # Validation at each phase
│   ├── tools/            # Web search tools
│   ├── config/           # Source configuration
│   └── utils/            # Logging, Bedrock config
├── tests/                # Test suite
├── docs/                 # Documentation
└── output/               # Generated newsletters (gitignored)
```

---

## Quality Standards

The system enforces HBR-quality standards through quality gates:

- **Research**: Minimum 5 credible sources, source diversity
- **Content**: 1,500-2,500 words, readability scoring
- **Production**: Professional visuals (300 DPI), embedded images

---

## Tech Stack

- **LLM**: Claude via AWS Bedrock
- **Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **Visuals**: matplotlib, seaborn, [diagrams](https://diagrams.mingrammer.com/)
- **Audio**: Amazon Polly / OpenAI TTS
- **PDF**: WeasyPrint

---

## License

Internal TUI Group - ML Lab Incubator

## Contact

- **Author**: John Ruiz
- **Email**: john.ruiz@tui.com
- **Team**: ML Lab Incubator
