# DeepAgents Migration Plan

> **Status**: PLANNING - Awaiting validation before implementation
> **Priority**: HIGH - Core architectural upgrade
> **Estimated Effort**: 1-2 weeks

---

## Current State

InkForge currently uses **LangGraph** directly for agent orchestration:

```python
# Current: src/orchestrator/orchestrator.py
from langgraph.graph import StateGraph, END

workflow = StateGraph(NewsletterState)
workflow.add_node("query_formulation", ...)
workflow.add_edge("query_formulation", "research")
# ... manual graph construction
```

### Limitations of Current Approach

| Issue | Impact |
|-------|--------|
| Manual state management | Verbose, error-prone |
| No built-in planning tools | Agents can't decompose tasks |
| No subagent delegation | All 9 agents run sequentially |
| No long-term memory | Each run starts fresh |
| No CLI tooling | Poor developer experience |

---

## Target State

Migrate to **DeepAgents** (built on LangGraph) with **deepagents_cli** for development.

```
┌─────────────────────────────────────────────────────────────────┐
│                         DeepAgents                               │
│  • Planning tools (task decomposition)                          │
│  • Subagent spawning (parallel execution)                       │
│  • File system tools (context management)                       │
│  • Long-term memory (cross-session persistence)                 │
├─────────────────────────────────────────────────────────────────┤
│                         LangGraph                                │
│  • State graphs • Node execution • Edge transitions             │
├─────────────────────────────────────────────────────────────────┤
│                         LangChain                                │
│  • LLM integrations • Tools & Models                            │
└─────────────────────────────────────────────────────────────────┘
```

### Benefits

| Feature | Benefit for InkForge |
|---------|---------------------|
| **Planning tools** | Orchestrator can dynamically plan research phases |
| **Subagent spawning** | Research agents run in parallel (faster) |
| **File system tools** | Better context management for long articles |
| **deepagents_cli** | Ralph mode for iterative development |
| **Memory** | Remember user preferences across sessions |

---

## Migration Phases

### Phase 1: Setup & Dependencies (Day 1)

```bash
# Add DeepAgents to dependencies
pip install deepagents deepagents-cli

# Update pyproject.toml
[project]
dependencies = [
    "deepagents>=0.1.0",
    "deepagents-cli>=0.1.0",
    # ... existing deps
]
```

### Phase 2: Orchestrator Refactor (Days 2-3)

Replace manual LangGraph construction with DeepAgents patterns.

**Before (LangGraph direct)**:
```python
from langgraph.graph import StateGraph, END

class Orchestrator:
    def __init__(self):
        self.workflow = StateGraph(NewsletterState)
        # Manual node/edge setup...
```

**After (DeepAgents)**:
```python
from deepagents import Agent, PlanningTool, SubagentTool

class NewsletterOrchestrator(Agent):
    tools = [
        PlanningTool(),  # Task decomposition
        SubagentTool(),  # Spawn specialized agents
        FileSystemTool(), # Context management
    ]

    async def run(self, topic: str):
        # Plan the research strategy
        plan = await self.plan(f"Research and write article about {topic}")

        # Execute with subagents
        for task in plan.tasks:
            if task.can_parallelize:
                await self.spawn_parallel(task.subtasks)
            else:
                await self.execute(task)
```

### Phase 3: Agent Migration (Days 4-6)

Convert each agent to DeepAgents pattern:

| Current Agent | DeepAgents Pattern |
|--------------|-------------------|
| QueryFormulationAgent | PlanningAgent (task decomposition) |
| ResearchAgent | ParallelSubagent (concurrent searches) |
| TUIStrategyAgent | ContextAgent (file system tools) |
| SynthesisAgent | WriterAgent (long-form generation) |
| HBREditorAgent | EditorAgent (multi-pass refinement) |
| VisualAssetAgent | ToolAgent (skill invocation) |
| MultimediaAgent | ToolAgent (skill invocation) |
| AssemblyAgent | OutputAgent (packaging) |

### Phase 4: Skills Integration (Days 7-8)

Register skills as DeepAgents tools:

```python
from deepagents import Tool
from skills.visual_generation import generate_chart

class ChartTool(Tool):
    name = "generate_chart"
    description = "Generate a professional chart from data"

    async def run(self, chart_type: str, data: dict, title: str):
        return generate_chart(chart_type, data, title)
```

### Phase 5: CLI Integration (Days 9-10)

Configure deepagents_cli for development:

```yaml
# deepagents.yaml
name: inkforge
version: 0.1.0

agents:
  - name: orchestrator
    entrypoint: src.orchestrator:NewsletterOrchestrator

  - name: researcher
    entrypoint: src.agents.research:ResearchAgent
    parallel: true

  - name: writer
    entrypoint: src.agents.synthesis:SynthesisAgent

ralph_mode:
  enabled: true
  checkpoint_dir: .ralph/
  max_iterations: 10
```

**Usage with Ralph Mode**:
```bash
# Start newsletter generation with Ralph mode
deepagents run orchestrator --topic "AI in Travel" --ralph

# Ralph will:
# 1. Execute phase
# 2. Show results
# 3. Ask for feedback
# 4. Iterate or proceed
```

---

## Reference: VideoRAG Pattern

Based on our VideoRAG implementation, key patterns to follow:

### 1. Agent Definition Pattern
```python
from deepagents import Agent, Memory

class VideoRAGAgent(Agent):
    memory = Memory(persist=True)

    async def process(self, input_data):
        # Check memory for similar queries
        cached = await self.memory.search(input_data.query)
        if cached:
            return cached

        # Process and store
        result = await self._process(input_data)
        await self.memory.store(input_data.query, result)
        return result
```

### 2. Subagent Spawning Pattern
```python
# Parallel research execution
research_tasks = [
    self.spawn("researcher", query=q)
    for q in queries
]
results = await asyncio.gather(*research_tasks)
```

### 3. Ralph Loop Pattern
```python
@ralph_checkpoint
async def research_phase(self):
    """This creates a checkpoint after execution."""
    results = await self.execute_research()
    return results

# Ralph will pause here, show results, and ask:
# "Continue to next phase? (y/n/modify)"
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `pyproject.toml` | Add deepagents dependencies |
| `src/orchestrator/orchestrator.py` | Complete rewrite |
| `src/agents/*.py` | Convert to DeepAgents Agent class |
| `skills/**/*.py` | Wrap as DeepAgents Tool |
| `deepagents.yaml` | NEW - CLI configuration |
| `.ralph/` | NEW - Ralph mode checkpoints |

---

## Success Criteria

- [ ] All 9 agents running under DeepAgents
- [ ] Research phase parallelized (3x faster)
- [ ] Ralph mode working for iterative development
- [ ] Skills registered as tools
- [ ] Memory persisting across sessions
- [ ] CLI commands working (`deepagents run`, `deepagents status`)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| API compatibility | Keep LangGraph fallback |
| Performance regression | Benchmark before/after |
| Breaking existing workflows | Feature branch development |

---

## Timeline

| Week | Focus |
|------|-------|
| Week 1 | Phases 1-3 (Setup + Orchestrator + Agents) |
| Week 2 | Phases 4-5 (Skills + CLI) + Testing |

---

## Next Steps (Post-Validation)

1. **John to validate** this plan
2. Create `feature/deepagents-migration` branch
3. Start with Phase 1 (dependencies)
4. Incremental commits with working checkpoints

---

*Plan created: 2026-02-03*
*Author: Claude Code + John Ruiz*
