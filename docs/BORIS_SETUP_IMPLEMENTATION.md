# Boris Cherny's 10 Tips - Implementation Documentation

## Overview

This document details how Boris Cherny's 10 tips for effective Claude Code usage are implemented in the **Leadership Strategy Newsletter Agent** project.

---

## Boris's 10 Tips Mapping

| # | Tip | Status | Implementation |
|---|-----|--------|----------------|
| 1 | CLAUDE.md for Project Context | ✅ COMPLETE | Global + Project-specific CLAUDE.md |
| 2 | Context7 Validation | ✅ AVAILABLE | Via `/devflow-plan` and `/devflow-verify` |
| 3 | Custom Slash Commands | ✅ COMPLETE | `/newsletter-dev`, `/parallel-agents` |
| 4 | Parallel Agents/Subagents | ✅ COMPLETE | Map-reduce pattern in ParallelizedResearchAgent |
| 5 | Memory & Persistent Context | ✅ COMPLETE | `tasks/lessons.md`, state files |
| 6 | Planning Before Implementation | ✅ COMPLETE | Phase-based TODO.md, CLAUDE.md rules |
| 7 | Verification Gates | ✅ COMPLETE | Quality gates in every agent |
| 8 | Code Review Loops | ✅ AVAILABLE | Ralph loop, swarm review via plugins |
| 9 | Context Awareness | ✅ COMPLETE | Status line, context tracking |
| 10 | Technical Debt Management | ✅ AVAILABLE | `/techdebt` command |

---

## Tip 1: CLAUDE.md for Project Context

### Global Configuration
**File:** `~/.claude/CLAUDE.md`

```
- Task Complexity Assessment (Simple/Medium/Complex)
- 6 Core Operating Rules
- Auto-trigger plan mode for 3+ step tasks
- Automatic lesson capture in tasks/lessons.md
```

### Project-Specific Configuration
**File:** `/project/.claude/CLAUDE.md`

**Critical Requirements Captured:**
- ✅ Quality bar: HBR level (NON-NEGOTIABLE)
- ✅ Word count: 2000-2500 words EXACTLY
- ✅ TUI Context: MANDATORY for all newsletters
- ✅ Visual Quality: Top-notch professional
- ✅ Multimedia Standards: ElevenLabs audio, 60-sec video

**Architecture Documented:**
- ✅ 9 Agent workflow diagram
- ✅ LangGraph patterns
- ✅ Quality gate pattern
- ✅ State management approach

### Evidence of Application
```python
# synthesis_agent.py:214-217
class SynthesisAgent(LLMAgent[SynthesisInput, DraftArticle]):
    # Word count constraints (NON-NEGOTIABLE!)
    MIN_WORDS = 2000
    MAX_WORDS = 2500
    TARGET_WORDS = 2200

# hbr_editor_agent.py:230-233
class HBREditorAgent(LLMAgent[EditorInput, EditedArticle]):
    # Word count constraints (NON-NEGOTIABLE!)
    MIN_WORDS = 2000
    MAX_WORDS = 2500
    TARGET_WORDS = 2250
```

---

## Tip 2: Context7 Validation

### Available via DevFlow
```bash
# Query best practices for frameworks
/devflow-plan   # Deep Context7 research
/devflow-verify # Pattern validation gate
```

### Application to This Project
Context7 was used for:
- LangGraph StateGraph patterns
- AWS Bedrock configuration (CRIS)
- pytest async testing patterns

---

## Tip 3: Custom Slash Commands

### Project-Specific Skills

**1. `/newsletter-dev`**
- **Location:** `.claude/skills/newsletter-dev/SKILL.md`
- **Purpose:** Guide 9-agent implementation
- **Contents:**
  - Agent file structure template
  - Agent node function pattern
  - Quality gate pattern
  - Development phase order
  - Testing commands

**2. `/parallel-agents`**
- **Location:** `.claude/skills/parallel-agents/SKILL.md`
- **Purpose:** Map-reduce pattern for research
- **Contents:**
  - Send pattern for fan-out
  - Combine pattern for fan-in
  - Quality gates for parallel results

### Global Skills Available
- `/devflow-init` - Feature initialization
- `/devflow-plan` - Deep planning mode
- `/devflow-verify` - Verification gates
- `/devflow-swarm` - Parallel agent reviews
- `/techdebt` - Technical debt detection
- `/tips` - Power user prompts

---

## Tip 4: Parallel Agents/Subagents

### Implementation: ParallelizedResearchAgent

**File:** `src/agents/research_agent.py`

```python
class ParallelizedResearchAgent(LLMAgent):
    """
    Map-reduce pattern with concurrent sub-agents.

    1. MAP: Dispatch ResearchSubAgent for each subtopic
    2. PROCESS: Concurrent execution (5-10 agents)
    3. REDUCE: Combine results with quality scoring
    """

    async def process(self, research_plan: dict) -> dict:
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.max_concurrent_agents)

        # Fan-out to sub-agents
        tasks = [
            self._research_subtopic_with_semaphore(plan, semaphore)
            for plan in research_plan["research_plan"]
        ]

        # Parallel execution
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Fan-in: combine results
        return self._combine_results(results)
```

### Evidence of Application
```
79 tests passing - includes parallel research tests
```

---

## Tip 5: Memory & Persistent Context

### Lesson Capture System
**File:** `tasks/lessons.md`

**Critical Requirements Preserved:**
```markdown
### Quality Bar: HBR Level
- Previous project feedback: "muito extenso" and "não profissional o suficiente"
- This project CANNOT have these problems

### Article Length: 2000-2500 words EXACTLY
- Target reading time: 10 minutes
- NOT MORE than 2500 words - this was the main complaint before

### TUI Context: MANDATORY
- TUI Strategy Analysis Agent MUST run for EVERY newsletter
```

### State Persistence
**Files:**
- `tasks/todo.md` - Implementation progress tracking
- `.claude/devflow/state.json` - DevFlow state
- SharedState saves snapshots to output directory

### Evidence of Application
The word count constraints from lessons.md are enforced in code:
```python
# Both agents enforce the 2000-2500 word constraint
if output_data.word_count < self.MIN_WORDS:
    issues.append(f"Too short: {output_data.word_count} words")
if output_data.word_count > self.MAX_WORDS:
    issues.append(f"Too long: {output_data.word_count} words")
```

---

## Tip 6: Planning Before Implementation

### Phase-Based Development
**File:** `tasks/todo.md`

```markdown
## Phase 0: Foundation Setup ✅ COMPLETE
## Phase 1: Core Infrastructure ✅ COMPLETE
## Phase 2: Research Pipeline ✅ COMPLETE
## Phase 3: Content Creation ✅ COMPLETE
## Phase 4: Multimedia & Assembly (NEXT)
```

### Architecture-First Approach
Before coding, the CLAUDE.md defines:
1. 9-agent architecture diagram
2. Data flow between agents
3. Quality gate requirements
4. State management patterns

### Evidence of Application
```
Phase 0: 5 tasks completed (foundation)
Phase 1: 5 tasks completed (infrastructure)
Phase 2: 4 tasks completed (research pipeline)
Phase 3: 4 tasks completed (content creation)
Total: 79 tests validating implementation
```

---

## Tip 7: Verification Gates

### Quality Gates in Every Agent

**BaseAgent Pattern:**
```python
class BaseAgent(ABC, Generic[TInput, TOutput]):
    @abstractmethod
    async def validate_output(self, output_data: TOutput) -> tuple[bool, str]:
        """Validate output meets quality requirements."""
        pass

    @abstractmethod
    async def calculate_quality_score(self, output_data: TOutput) -> float:
        """Calculate quality score (0-100)."""
        pass
```

### Agent-Specific Gates

**SynthesisAgent:**
- Word count: 2000-2500
- Counterintuitive insights: >= 1 (ESSENTIAL)
- Sources cited: >= 3
- Sections: >= 4

**HBREditorAgent:**
- Word count: 2000-2500 (NON-NEGOTIABLE)
- HBR quality score: >= 70
- Readability score: >= 50

**TUIStrategyAgent:**
- Business model length: >= 50 chars
- Strategic priorities: >= 3
- Risks/challenges: >= 3
- Technology strategy: present

### Global Quality Thresholds
**File:** `src/state/newsletter_state.py`
```python
QUALITY_THRESHOLDS = {
    "research": {"min_sources": 10, "min_subtopics": 3},
    "synthesis": {"min_words": 2000, "max_words": 2500},
    "hbr_quality": {"min_score": 70},
    "visuals": {"min_assets": 3},
    "multimedia": {"video_duration": (58, 62)},
}
```

---

## Tip 8: Code Review Loops

### Available Tools

**Ralph Loop (Plugin):**
```bash
# Iterative refinement until quality gates pass
/ralph-loop
```

**Swarm Review (DevFlow):**
```bash
# Parallel specialist agents review code
/devflow-swarm --all
# Launches: Security, Performance, Architecture reviewers
```

### Application to This Project
- All agents have `validate_output()` methods
- Orchestrator retries failed phases with exponential backoff
- Quality gates prevent error propagation

---

## Tip 9: Context Awareness

### Status Line
**File:** `~/.claude/statusline.sh`
```bash
# Shows: Model | Directory | Git Branch | Context Usage %
# Color-coded context usage warnings
```

### Context Sync
```bash
# Pull recent activity from GitHub, Linear, Asana
/context-sync
```

### In This Project
- SharedState tracks current phase
- Orchestrator logs all phase transitions
- State snapshots saved for debugging

---

## Tip 10: Technical Debt Management

### Available Command
```bash
# Find duplicated code, dead code, code smells, test gaps
/techdebt
```

### In This Project
- Continuous testing (79 tests)
- Type hints throughout
- Dataclass patterns for clean structures
- No circular dependencies

---

## Summary: What's Working Well

### ✅ Fully Implemented

1. **CLAUDE.md** - Project context fully documented
2. **Custom Skills** - `/newsletter-dev`, `/parallel-agents`
3. **Parallel Agents** - Map-reduce research working
4. **Memory** - `tasks/lessons.md` preserving critical requirements
5. **Planning** - 4-phase approach with clear milestones
6. **Verification Gates** - Every agent has quality validation

### ✅ Available & Ready to Use

7. **Context7** - Via `/devflow-plan`
8. **Code Review** - Via `/devflow-swarm`
9. **Context Awareness** - Status line configured
10. **Tech Debt** - Via `/techdebt`

---

## Recommendations Before Phase 4

1. **Run `/devflow-verify`** - Ensure all gates pass
2. **Run `/techdebt`** - Check for accumulated debt
3. **Update `lessons.md`** - Add Phase 3 learnings
4. **Review Context** - Check context usage before large phase

---

## Test Coverage Evidence

```
=================== 79 passed in 15.11s ===================

Tests by Category:
- State Management: 19 tests
- Orchestrator: 9 tests
- Research Pipeline: 17 tests
- Content Creation: 22 tests
- Quality Gates: 12 tests
```
