#!/usr/bin/env python3
"""
Test InkForge RALPH LOOP - demonstrates the iterative newsletter generation pattern.
The agent progresses through stages, each iteration doing one unit of work.
"""
import asyncio
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Set AWS credentials for Bedrock
os.environ["AWS_PROFILE"] = os.environ.get("AWS_PROFILE", "mll-dev")
os.environ["AWS_DEFAULT_REGION"] = os.environ.get("AWS_DEFAULT_REGION", "eu-central-1")

# Load API key if exists
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()

print("="*60)
print("INKFORGE RALPH LOOP - NEWSLETTER GENERATION DEMO")
print("="*60)
print("Watch the agent progress through stages:")
print("  QUERY_FORMULATION -> RESEARCHING -> SYNTHESIZING -> COMPLETED")
print("="*60)

# Setup workspace
workspace = Path(__file__).parent / "workspace" / "ralph-newsletter-test"

# Clean previous run
if workspace.exists():
    import shutil
    shutil.rmtree(workspace)

workspace.mkdir(parents=True, exist_ok=True)
for d in ["content", "visuals", "multimedia", "deliverables", "research"]:
    (workspace / d).mkdir(exist_ok=True)

# Newsletter topic
topic = "Universal Commerce Protocol (UCP)"
key_concepts = ["Agentic AI", "Commerce Protocols", "Travel Technology"]
target_audience = "TUI Leadership and Strategy Teams"

# Complex task for the agent
newsletter_task = f"""
Generate an HBR-quality strategic newsletter about: {topic}

Key Concepts: {', '.join(key_concepts)}
Target Audience: {target_audience}

The newsletter should:
1. Analyze how UCP affects TUI's strategic positioning
2. Identify counterintuitive insights about agentic commerce
3. Include a provocative headline that challenges conventional wisdom
4. Follow HBR Five Core Qualities (clarity, evidence, tone, flow, insight)
"""

# Initial state - starting from research
state = {
    "task": newsletter_task,
    "topic": topic,
    "key_concepts": key_concepts,
    "target_audience": target_audience,
    "stage": "QUERY_FORMULATION",  # Start at first working stage
    "iteration": 0,
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat(),
    # Research data placeholder - agent will populate
    "research_queries": [],
    "research_results": [],
    "tui_analysis": None,
    "draft_article": None,
    "final_article": None,
    "visual_assets": [],
    "deliverables": {},
    "errors": [],
    "history": []
}

(workspace / "state.json").write_text(json.dumps(state, indent=2))

# Create initial iteration log
iteration_log = f"""# InkForge Ralph Mode Log

Started: {datetime.now().isoformat()}

## Task
{newsletter_task}

## Stages
1. QUERY_FORMULATION - Generate search queries
2. RESEARCHING - Execute web research
3. SYNTHESIZING - Create draft article
4. HBR_EDITING - Apply HBR quality pass
5. COMPLETED - Newsletter ready

---
"""
(workspace / "iteration_log.md").write_text(iteration_log)

print(f"\n[INIT] Workspace: {workspace}")
print(f"       Topic: {topic}")
print(f"       Starting stage: {state['stage']}")
print(f"\n[TASK] {newsletter_task[:150]}...")

# Check if deepagents-cli is available
try:
    from deepagents_cli.agent import create_cli_agent
    from langchain_core.tools import tool
    DEEPAGENTS_AVAILABLE = True
except ImportError as e:
    print(f"\n[ERROR] deepagents-cli not available: {e}")
    print("Install with: pip install deepagents-cli")
    sys.exit(1)

# ============================================================================
# Simple Tools for Newsletter Generation
# ============================================================================

@tool
async def analyze_topic_for_newsletter(
    topic: str,
    context: str,
    output_file: str
) -> dict:
    """
    Analyze a topic and generate newsletter content structure.

    Args:
        topic: The newsletter topic to analyze
        context: Additional context and research data
        output_file: Path to save the analysis

    Returns:
        Dict with analysis results
    """
    # This is a simple pass-through - the LLM does the real work
    analysis = {
        "topic": topic,
        "analyzed_at": datetime.now().isoformat(),
        "context_length": len(context),
        "output_file": output_file
    }

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_text(json.dumps(analysis, indent=2))

    return {"success": True, "output_file": output_file}


@tool
async def save_newsletter_draft(
    title: str,
    content: str,
    output_dir: str
) -> dict:
    """
    Save a newsletter draft to the workspace.

    Args:
        title: The article title
        content: The article content in markdown
        output_dir: Directory to save the draft

    Returns:
        Dict with file path and status
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save markdown
    md_file = output_path / "draft_article.md"
    md_file.write_text(f"# {title}\n\n{content}")

    return {
        "success": True,
        "file_path": str(md_file),
        "word_count": len(content.split())
    }


# ============================================================================
# Ralph Mode System Prompt for InkForge
# ============================================================================

INKFORGE_SYSTEM_PROMPT = """
# InkForge Ralph Mode Agent

You are an autonomous newsletter generation agent operating in Ralph mode.
Your work persists in the filesystem between iterations.

## Core Principle
Each iteration, you receive fresh context but your previous work remains
in the filesystem. Check what exists and continue building.

## Workflow
1. **Check State**: Read workspace/state.json to understand current progress
2. **Continue Work**: Pick up where the last iteration left off
3. **Save Progress**: Always update state.json before completing
4. **Quality Gates**: Don't proceed to next stage until current stage passes

## Directory Structure
```
workspace/
├── state.json          # Current state and progress
├── iteration_log.md    # Log of each iteration's actions
├── content/            # Article drafts
├── research/           # Research data
├── visuals/            # Generated charts
└── deliverables/       # Final outputs
```

## Stage Machine
1. QUERY_FORMULATION - Generate optimized search queries
2. RESEARCHING - Execute research (simulate with analysis)
3. SYNTHESIZING - Create HBR-quality draft
4. HBR_EDITING - Apply editing pass
5. COMPLETED - Newsletter ready

## Available Tools
- File operations: read_file, write_file, edit_file, ls, glob
- analyze_topic_for_newsletter: Analyze and structure content
- save_newsletter_draft: Save article drafts

## Each Iteration
1. Read state.json to know current stage
2. Perform ONE meaningful unit of work
3. Update state.json with progress
4. Log actions to iteration_log.md
5. If complete, set stage to COMPLETED

## Newsletter Quality Standards (HBR Five Core Qualities)
1. **Clarity**: Every sentence serves a purpose
2. **Evidence**: Data-driven assertions
3. **Tone**: Authoritative but conversational
4. **Flow**: Logical progression of ideas
5. **Insight**: Counterintuitive, non-obvious conclusions

Remember: You have fresh context each iteration. Always read state first.
"""


# ============================================================================
# Run Ralph Mode
# ============================================================================

async def execute_agent_task(
    user_input: str,
    agent,
    thread_id: str = "ralph",
) -> None:
    """
    Execute an agent task using direct LangGraph API.
    Uses agent.astream() for streaming execution.
    """
    stream_input = {"messages": [{"role": "user", "content": user_input}]}
    run_config = {"configurable": {"thread_id": thread_id}}

    try:
        async for chunk in agent.astream(
            stream_input,
            config=run_config,
            stream_mode=["messages", "updates"],
        ):
            # Process stream - agent writes to filesystem
            if isinstance(chunk, dict):
                for key, value in chunk.items():
                    if key == "messages" and value:
                        for msg in value:
                            if hasattr(msg, 'content') and msg.content:
                                # Print agent thinking (truncated)
                                content = str(msg.content)[:200]
                                if content.strip():
                                    print(f"  [Agent] {content}...")
    except Exception as e:
        print(f"[Ralph] Agent execution error: {e}")
        raise


async def run_ralph_iteration(agent, workspace: Path, iteration: int, task: str) -> bool:
    """Run a single Ralph mode iteration."""

    prompt = f"""
Iteration #{iteration}

Your task: {task}

Your previous work is in the filesystem at: {workspace}
Check state.json to see current progress and continue building.

If this is the first iteration, initialize and start with QUERY_FORMULATION.
Otherwise, continue from where the last iteration left off.

Remember to:
1. Read state.json first
2. Do ONE meaningful unit of work
3. Update state.json with progress (ENSURE VALID JSON!)
4. Append to iteration_log.md what you did
5. If you complete all work, set stage to COMPLETED
"""

    await execute_agent_task(
        user_input=prompt,
        agent=agent,
        thread_id=f"inkforge-{iteration}"
    )

    # Check if completed
    state_file = workspace / "state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text())
        return state.get("stage") != "COMPLETED"

    return True


async def run_ralph_mode():
    """Main Ralph mode execution."""
    print("\n" + "="*60)
    print("Starting InkForge Ralph Loop...")
    print("="*60 + "\n")

    # Create agent with tools
    tools = [analyze_topic_for_newsletter, save_newsletter_draft]

    try:
        agent, backend = create_cli_agent(
            model="bedrock:eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
            assistant_id="inkforge-ralph",
            system_prompt=INKFORGE_SYSTEM_PROMPT,
            auto_approve=True,
            tools=tools
        )
        print("[AGENT] Created with Bedrock Claude Sonnet 4.5")
    except Exception as e:
        print(f"[AGENT] Bedrock failed: {e}")
        print("[AGENT] Falling back to OpenAI...")

        agent, backend = create_cli_agent(
            model="openai:gpt-4o",
            assistant_id="inkforge-ralph",
            system_prompt=INKFORGE_SYSTEM_PROMPT,
            auto_approve=True,
            tools=tools
        )
        print("[AGENT] Created with OpenAI GPT-4o")

    max_iterations = 5
    iteration = 1

    while iteration <= max_iterations:
        print(f"\n--- Iteration {iteration} ---")

        try:
            should_continue = await run_ralph_iteration(
                agent=agent,
                workspace=workspace,
                iteration=iteration,
                task=newsletter_task
            )

            if not should_continue:
                print("\n[COMPLETED] Agent signaled completion.")
                break

        except Exception as e:
            print(f"\n[ERROR] Iteration failed: {e}")

        iteration += 1

    # Final results
    state_file = workspace / "state.json"
    final_state = json.loads(state_file.read_text()) if state_file.exists() else {}

    return {
        "success": final_state.get("stage") == "COMPLETED",
        "iterations": iteration,
        "state": final_state,
        "workspace": str(workspace)
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    result = asyncio.run(run_ralph_mode())

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Total Iterations: {result['iterations']}")
    print(f"Final Stage: {result['state'].get('stage', 'unknown')}")

    # Show iteration log
    log_file = workspace / "iteration_log.md"
    if log_file.exists():
        print(f"\n[ITERATION LOG]")
        print(log_file.read_text())

    # List generated files
    print("\n[FILES CREATED]")
    for f in workspace.rglob("*"):
        if f.is_file():
            size = f.stat().st_size
            print(f"  - {f.relative_to(workspace)} ({size:,} bytes)")
