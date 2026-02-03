# 🔥 InkForge

```
╔═══════════════════════════════════════════════════════════════╗
║  ▀█▀ █▄ █ █▄▀ █▀▀ █▀█ █▀█ █▀▀ █▀▀                            ║
║  ░█░ █░▀█ █░█ █▀░ █▄█ █▀▄ █▄█ ██▄                            ║
║                                                               ║
║  9-Agent • Skills-as-Tools • Dynamic Viz • HBR A+ Grade      ║
╚═══════════════════════════════════════════════════════════════╝
```

> **Agentic Newsletter Generation System for TUI Leadership**

Transform strategic insights into HBR-quality newsletters with AI-powered research, dynamic visualization, and professional publishing.

---

## Overview

The Agent Newsletter System automates the entire newsletter production pipeline—from research and analysis to professional PDF/HTML generation with embedded visuals and audio narration.

### Key Features

- **9 Specialized AI Agents** working in orchestrated sequence
- **Skills as Tools** - Modular, reusable skills that agents invoke
- **Dynamic Visualization** - Charts generated based on article content (not hardcoded!)
- **HBR-Quality Output** with professional charts, diagrams, and typography
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
                    │     SKILLS        │
                    │  (Reusable Tools) │
                    │ • visual_generation│
                    │ • audio_generation │
                    │ • pdf_generation   │
                    └───────────────────┘
```

---

## Skills Architecture

Skills are modular, reusable components that agents invoke as tools. This follows the **"Skills as Tools"** pattern.

### Visual Generation Skill

```
skills/
└── visual_generation/
    ├── SKILL.md              # Documentation
    ├── __init__.py           # Public exports
    └── generators/
        ├── charts.py         # matplotlib + seaborn (300 DPI)
        ├── architecture.py   # diagrams library
        └── timelines.py      # plotly
```

#### Available Tools

| Tool | Description | Output |
|------|-------------|--------|
| `generate_chart()` | Bar, line, area charts | PNG (300 DPI) |
| `generate_architecture()` | System/comparison diagrams | PNG (300 DPI) |
| `generate_timeline()` | Market trajectories | PNG + HTML |

#### Dynamic Generation Flow

```
Article Content
      │
      ▼
┌─────────────────────────────────┐
│ LLM: Analyze article            │
│ → Identify visualization needs  │
│ → Extract data from text        │
└─────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────┐
│ Skills: Generate visuals        │
│ → Charts with extracted data    │
│ → Diagrams based on content     │
└─────────────────────────────────┘
```

**No hardcoded data!** Different topics produce different visualizations.

---

## HBR Article Standards Skill

The `hbr-article-standards` skill ensures all output meets Harvard Business Review publication standards.

```
skills/
└── hbr-article-standards/
    ├── SKILL.md                    # Overview
    ├── templates/
    │   ├── hbr_layout_template.html  # Jinja2 HTML template
    │   └── hbr_pdf_template.css      # Professional styling
    ├── guidelines/
    │   ├── structural_elements.md    # 5 mandatory HBR elements
    │   └── writing_style_guide.md    # Persuasive narrative tone
    └── examples/                     # Sample outputs
```

### HBR Structural Elements (Mandatory)

| Element | Description |
|---------|-------------|
| **Author Byline** | Name + credentials below title |
| **Idea in Brief** | Sidebar with Problem/Argument/Solution |
| **Pull Quotes** | 2-3 impactful sentences displayed prominently |
| **Figure Captions** | Numbered captions on all visuals |
| **Provocative Subheadings** | Story-driven section headers |

### Quality Metrics

| Metric | Before | After |
|--------|--------|-------|
| HBR Compliance | 6/10 | **9/10** |
| Structure | 6/10 | **9/10** |
| Writing Tone | 7/10 | **9/10** |
| Overall Grade | B (7.5) | **A+ (9.5)** |

### Example Output

```html
<aside class="idea-in-brief">
    <h3>Idea in Brief</h3>
    <div class="iib-section">
        <h4>THE PROBLEM</h4>
        <p>TUI's vertically integrated model—owning 130+ aircraft,
           16 cruise ships, and 400+ hotels—historically provided
           competitive advantage...</p>
    </div>
    <div class="iib-section">
        <h4>THE ARGUMENT</h4>
        <p>While asset-light OTAs move faster, they optimize
           inventory they don't control...</p>
    </div>
    <div class="iib-section">
        <h4>THE SOLUTION</h4>
        <p>Rather than fighting yesterday's battle, TUI must
           reframe vertical integration as an AI advantage...</p>
    </div>
</aside>
```

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

# Checkout the skills branch
git checkout feature/agentic-skills

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Running the System

```bash
# Run end-to-end newsletter generation
PYTHONPATH=. python run_e2e_test.py

# Or with a custom topic
PYTHONPATH=. python -c "
import asyncio
from src.orchestrator.orchestrator import generate_newsletter

asyncio.run(generate_newsletter(
    topic='Your Topic Here',
    target_audience='TUI Leadership',
    key_concepts=['Concept 1', 'Concept 2'],
))
"
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
    │   ├── chart_1_*.png          # Dynamically named!
    │   ├── chart_2_*.png
    │   └── asset_manifest.json
    ├── multimedia/
    │   └── narration_*.mp3
    └── final_deliverables/
        ├── newsletter_*.pdf
        ├── newsletter_*.html
        ├── *.png (copied visuals)
        ├── *.mp3 (copied audio)
        └── newsletter_*.zip
```

---

## Example Outputs

### Test 1: "Universal Commerce Protocol"
- 3 charts generated
- PDF: 461 KB

### Test 2: "The AI Paradox in Travel"
- 4 charts generated (different content!)
- PDF: 965 KB
- Includes "Automation Paradox: Efficiency vs Customer Satisfaction" chart

---

## Development

### Project Structure

```
agent-newsletter/
├── src/
│   ├── agents/           # 8 specialized agents
│   ├── orchestrator/     # Central workflow coordinator
│   ├── state/            # Shared state management
│   ├── quality_gates/    # Validation at each phase
│   └── utils/            # Logging, Bedrock config
├── skills/               # Reusable skill modules
│   └── visual_generation/
├── tests/                # Test suite
├── docs/                 # Documentation
└── output/               # Generated newsletters (gitignored)
```

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

---

## Tech Stack

- **LLM**: Claude via AWS Bedrock
- **Orchestration**: LangGraph
- **Visuals**: matplotlib, seaborn, diagrams, plotly
- **Audio**: Amazon Polly / OpenAI TTS
- **PDF**: WeasyPrint

---

## Branches

| Branch | Description | Status |
|--------|-------------|--------|
| `main` | Stable release | ✅ |
| `feature/agentic-skills` | Skills architecture + dynamic visualization | ✅ |
| `feature/hbr-quality` | HBR A+ grade structural elements | ✅ NEW |

### Branch Comparison

```
feature/agentic-skills          feature/hbr-quality
        │                               │
        ├── Dynamic charts              ├── All from agentic-skills
        ├── LLM-driven visuals          ├── + Author byline
        ├── Skills as tools             ├── + Idea in Brief sidebar
        └── 5 chart types               ├── + Pull quotes
                                        ├── + Persuasive tone prompts
                                        └── + HBR CSS styling
```

---

## License

Internal TUI Group - ML Lab Incubator

## Contact

- **Author**: John Ruiz
- **Email**: john.ruiz@tui.com
- **Team**: ML Lab Incubator
