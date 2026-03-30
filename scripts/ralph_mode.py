#!/usr/bin/env python3
"""
InkForge Ralph Mode Implementation (Advanced)

Ralph is an autonomous looping pattern created by Geoff Huntley for the DeepAgents
framework. Each loop starts with fresh context. The filesystem and git serve as memory.

Advanced Features:
- Git commits after each iteration (full audit trail)
- Webhook notifications when stages complete
- Resume from any previous state
- Quality gates for each stage transition

Usage:
    python ralph_mode.py --topic "Universal Commerce Protocol" --key-concepts "Agentic AI,Commerce"

    # With iteration limit
    python ralph_mode.py --iterations 10 --topic "AI in Travel" --key-concepts "LLMs,Automation"

    # Resume from previous state
    python ralph_mode.py --resume --workspace ./workspace/previous_run --topic "Continue"

    # With webhook notifications
    python ralph_mode.py --webhook https://example.com/webhook --topic "AI Trends"

Reference:
    https://github.com/langchain-ai/deepagents/blob/master/examples/ralph_mode/ralph_mode.py
"""

import os
import sys
import json
import asyncio
import argparse
import tempfile
import subprocess
import httpx
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import hashlib

# AWS Bedrock configuration
AWS_PROFILE = os.environ.get("AWS_PROFILE", "mll-dev")
AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
BEDROCK_MODEL_ID = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
FALLBACK_MODEL = "openai:gpt-4o"  # Fallback when Bedrock fails

# Add src to path for InkForge imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check for deepagents-cli
try:
    from deepagents_cli.agent import create_cli_agent, create_deep_agent
    from deepagents_cli.config import SessionState
    from langchain_core.tools import tool
    from langgraph.checkpoint.memory import MemorySaver
    DEEPAGENTS_AVAILABLE = True
    IMPORT_ERROR = None
except ImportError as e:
    print(f"Warning: deepagents-cli not available: {e}")
    DEEPAGENTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


async def execute_agent_task(
    user_input: str,
    agent,
    thread_id: str = "ralph",
    config_dict: dict = None
) -> None:
    """
    Execute an agent task using direct LangGraph API.
    Replacement for the removed execute_task from deepagents_cli.execution.
    """
    message_content = user_input
    stream_input = {"messages": [{"role": "user", "content": message_content}]}

    run_config = {
        "configurable": {"thread_id": thread_id},
        **(config_dict or {})
    }

    # Use astream for streaming execution
    try:
        async for chunk in agent.astream(
            stream_input,
            config=run_config,
            stream_mode=["messages", "updates"],
        ):
            # Process the stream but we don't need UI output
            # The agent writes to filesystem, which is what we care about
            pass
    except Exception as e:
        print(f"[Ralph] Agent execution error: {e}")
        raise


# ============================================================================
# Stage Enum for InkForge Newsletter Workflow
# ============================================================================

class Stage(str, Enum):
    """InkForge Ralph mode workflow stages."""
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


# ============================================================================
# Configuration Data Classes
# ============================================================================

@dataclass
class WebhookConfig:
    """Configuration for webhook notifications."""
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    events: List[str] = field(default_factory=lambda: ["stage_change", "iteration_complete", "error"])
    timeout: float = 10.0


@dataclass
class GitConfig:
    """Configuration for git commits."""
    enabled: bool = True
    auto_commit: bool = True
    commit_on_stage_change: bool = True
    commit_on_iteration: bool = True
    author_name: str = "Ralph Agent"
    author_email: str = "ralph@inkforge.local"


@dataclass
class ParallelConfig:
    """Configuration for parallel processing."""
    enabled: bool = False
    max_workers: int = 3
    batch_size: int = 5


@dataclass
class BedrockConfig:
    """Configuration for AWS Bedrock."""
    profile: str = "mll-dev"
    region: str = "eu-central-1"
    model_id: str = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0


@dataclass
class InkForgeConfig:
    """Main configuration for InkForge Ralph mode."""
    workspace_dir: Optional[str] = None
    max_iterations: int = 0  # 0 = unlimited
    model: str = f"bedrock:{BEDROCK_MODEL_ID}"  # Primary: Bedrock
    fallback_model: str = FALLBACK_MODEL  # Fallback: OpenAI GPT-4o
    resume: bool = False
    webhook: Optional[WebhookConfig] = None
    git: GitConfig = field(default_factory=GitConfig)
    parallel: ParallelConfig = field(default_factory=ParallelConfig)
    bedrock: BedrockConfig = field(default_factory=BedrockConfig)
    # InkForge specific
    target_audience: str = "TUI Leadership and Strategy Teams"
    word_count_target: tuple = (2000, 2500)


# ============================================================================
# Exponential Backoff Helper
# ============================================================================

async def with_exponential_backoff(
    func: Callable,
    *args,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    **kwargs
) -> Any:
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay cap in seconds

    Returns:
        Result from the function

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt == max_retries:
                break

            # Calculate delay with jitter
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            print(f"[BACKOFF] Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
            await asyncio.sleep(delay)

    raise last_exception


# ============================================================================
# InkForge Custom Tools
# ============================================================================

if DEEPAGENTS_AVAILABLE:
    @tool
    async def inkforge_generate_research_plan(
        topic: str,
        key_concepts_json: str,
        target_audience: str,
        output_dir: str
    ) -> dict:
        """
        Generate a research plan for the newsletter topic.

        Args:
            topic: The newsletter topic
            key_concepts_json: JSON string of key concepts list
            target_audience: Target audience description
            output_dir: Directory to save the research plan

        Returns:
            Dict with success status and research plan details
        """
        try:
            from src.agents.query_formulation_agent import create_query_formulation_agent
            from src.state.shared_state import create_shared_state

            key_concepts = json.loads(key_concepts_json)
            shared_state = create_shared_state(
                topic=topic,
                target_audience=target_audience,
                key_concepts=key_concepts,
                output_base_dir=output_dir,
            )

            agent = create_query_formulation_agent(shared_state)
            result = await agent.execute()

            return {
                "success": result.success,
                "research_plan_path": str(shared_state.research_dir / "research_plan.json"),
                "message": result.message,
                "quality_score": result.quality_score,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def inkforge_execute_research(
        workspace_path: str,
    ) -> dict:
        """
        Execute parallelized research based on the research plan.

        Args:
            workspace_path: Path to the workspace directory

        Returns:
            Dict with success status and research results
        """
        try:
            from src.agents.research_agent import create_research_agent
            from src.state.shared_state import SharedState
            from src.state.newsletter_state import create_initial_newsletter_state

            workspace = Path(workspace_path)
            state_file = workspace / "state.json"
            if state_file.exists():
                state_data = json.loads(state_file.read_text())
            else:
                return {"success": False, "error": "No state.json found"}

            shared_state = SharedState(
                output_dir=workspace,
                state=state_data
            )

            agent = create_research_agent(shared_state)
            result = await agent.execute()

            return {
                "success": result.success,
                "message": result.message,
                "quality_score": result.quality_score,
                "sources_collected": len(shared_state.read_all_research_data()),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def inkforge_tui_analysis(
        workspace_path: str,
    ) -> dict:
        """
        Perform TUI strategic analysis on the research data.

        Args:
            workspace_path: Path to the workspace directory

        Returns:
            Dict with success status and TUI analysis results
        """
        try:
            from src.agents.tui_strategy_agent import create_tui_strategy_agent
            from src.state.shared_state import SharedState

            workspace = Path(workspace_path)
            state_file = workspace / "state.json"
            if state_file.exists():
                state_data = json.loads(state_file.read_text())
            else:
                return {"success": False, "error": "No state.json found"}

            shared_state = SharedState(output_dir=workspace, state=state_data)
            agent = create_tui_strategy_agent(shared_state)
            result = await agent.execute()

            return {
                "success": result.success,
                "message": result.message,
                "quality_score": result.quality_score,
                "tui_summary_path": str(shared_state.research_dir / "tui_strategy_summary.md"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def inkforge_synthesize_article(
        workspace_path: str,
    ) -> dict:
        """
        Synthesize research into a draft article.

        Args:
            workspace_path: Path to the workspace directory

        Returns:
            Dict with success status and draft article info
        """
        try:
            from src.agents.synthesis_agent import create_synthesis_agent
            from src.state.shared_state import SharedState

            workspace = Path(workspace_path)
            state_file = workspace / "state.json"
            if state_file.exists():
                state_data = json.loads(state_file.read_text())
            else:
                return {"success": False, "error": "No state.json found"}

            shared_state = SharedState(output_dir=workspace, state=state_data)
            agent = create_synthesis_agent(shared_state)
            result = await agent.execute()

            draft_path = shared_state.content_dir / "draft_article.md"
            word_count = 0
            if draft_path.exists():
                word_count = len(draft_path.read_text().split())

            return {
                "success": result.success,
                "message": result.message,
                "quality_score": result.quality_score,
                "draft_path": str(draft_path),
                "word_count": word_count,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def inkforge_hbr_edit(
        workspace_path: str,
    ) -> dict:
        """
        Apply HBR-quality editing to the draft article.

        Args:
            workspace_path: Path to the workspace directory

        Returns:
            Dict with success status and final article info
        """
        try:
            from src.agents.hbr_editor_agent import create_hbr_editor_agent
            from src.state.shared_state import SharedState

            workspace = Path(workspace_path)
            state_file = workspace / "state.json"
            if state_file.exists():
                state_data = json.loads(state_file.read_text())
            else:
                return {"success": False, "error": "No state.json found"}

            shared_state = SharedState(output_dir=workspace, state=state_data)
            agent = create_hbr_editor_agent(shared_state)
            result = await agent.execute()

            final_path = shared_state.content_dir / "final_article.md"
            word_count = 0
            if final_path.exists():
                word_count = len(final_path.read_text().split())

            return {
                "success": result.success,
                "message": result.message,
                "quality_score": result.quality_score,
                "final_article_path": str(final_path),
                "word_count": word_count,
                "in_target_range": 2000 <= word_count <= 2500,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def inkforge_generate_visuals(
        workspace_path: str,
    ) -> dict:
        """
        Generate professional visual assets for the newsletter.

        Args:
            workspace_path: Path to the workspace directory

        Returns:
            Dict with success status and visual assets info
        """
        try:
            from src.agents.visual_asset_agent import create_visual_asset_agent
            from src.state.shared_state import SharedState

            workspace = Path(workspace_path)
            state_file = workspace / "state.json"
            if state_file.exists():
                state_data = json.loads(state_file.read_text())
            else:
                return {"success": False, "error": "No state.json found"}

            shared_state = SharedState(output_dir=workspace, state=state_data)
            agent = create_visual_asset_agent(shared_state)
            result = await agent.execute()

            visuals = list(shared_state.visuals_dir.glob("*.png"))

            return {
                "success": result.success,
                "message": result.message,
                "quality_score": result.quality_score,
                "visuals_count": len(visuals),
                "visuals_dir": str(shared_state.visuals_dir),
                "visual_files": [v.name for v in visuals],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def inkforge_produce_multimedia(
        workspace_path: str,
    ) -> dict:
        """
        Produce multimedia assets (audio, video) for the newsletter.

        Args:
            workspace_path: Path to the workspace directory

        Returns:
            Dict with success status and multimedia info
        """
        try:
            from src.agents.multimedia_agent import create_multimedia_agent
            from src.state.shared_state import SharedState

            workspace = Path(workspace_path)
            state_file = workspace / "state.json"
            if state_file.exists():
                state_data = json.loads(state_file.read_text())
            else:
                return {"success": False, "error": "No state.json found"}

            shared_state = SharedState(output_dir=workspace, state=state_data)
            agent = create_multimedia_agent(shared_state)
            result = await agent.execute()

            audio_files = list(shared_state.multimedia_dir.glob("*.mp3"))
            video_files = list(shared_state.multimedia_dir.glob("*.mp4"))

            return {
                "success": result.success,
                "message": result.message,
                "quality_score": result.quality_score,
                "audio_files": [a.name for a in audio_files],
                "video_files": [v.name for v in video_files],
                "multimedia_dir": str(shared_state.multimedia_dir),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def inkforge_assemble_deliverables(
        workspace_path: str,
    ) -> dict:
        """
        Assemble final deliverables (PDF, HTML, ZIP package).

        Args:
            workspace_path: Path to the workspace directory

        Returns:
            Dict with success status and deliverables info
        """
        try:
            from src.agents.assembly_agent import create_assembly_agent
            from src.state.shared_state import SharedState

            workspace = Path(workspace_path)
            state_file = workspace / "state.json"
            if state_file.exists():
                state_data = json.loads(state_file.read_text())
            else:
                return {"success": False, "error": "No state.json found"}

            shared_state = SharedState(output_dir=workspace, state=state_data)
            agent = create_assembly_agent(shared_state)
            result = await agent.execute()

            deliverables = {
                "pdf": None,
                "html": None,
                "zip": None,
            }

            for f in shared_state.final_deliverables_dir.iterdir():
                if f.suffix == ".pdf":
                    deliverables["pdf"] = str(f)
                elif f.suffix == ".html":
                    deliverables["html"] = str(f)

            zip_file = workspace / "newsletter_package.zip"
            if zip_file.exists():
                deliverables["zip"] = str(zip_file)

            return {
                "success": result.success,
                "message": result.message,
                "quality_score": result.quality_score,
                "deliverables": deliverables,
                "final_dir": str(shared_state.final_deliverables_dir),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================================
# Ralph Mode System Prompt
# ============================================================================

RALPH_SYSTEM_PROMPT = """
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
    state.json              # Current state and progress
    iteration_log.md        # Log of each iteration's actions
    input/                  # User prompt and topics
    research/               # Research plan and raw data
        raw_data/           # Per-subtopic research
        tui_strategy_summary.md
    content/                # Article drafts
        draft_article.md
        final_article.md
    visuals/                # Charts, diagrams (PNG)
    multimedia/             # Audio (MP3), Video (MP4)
    deliverables/           # PDF, HTML, ZIP package
```

## State Machine Stages
1. INITIALIZED - Starting state
2. QUERY_FORMULATION - Generate research plan and queries
3. RESEARCHING - Execute parallelized research
4. TUI_ANALYSIS - Analyze with TUI strategic context
5. SYNTHESIZING - Create draft article
6. HBR_EDITING - Apply HBR-quality editing (2000-2500 words)
7. VISUAL_GENERATION - Generate professional charts/diagrams
8. MULTIMEDIA_PRODUCTION - Create audio and video versions
9. ASSEMBLY - Produce final PDF, HTML, ZIP package
10. COMPLETED - All done

## Quality Gates
- QUERY_FORMULATION -> RESEARCHING: Research plan JSON exists, has 3+ subtopics
- RESEARCHING -> TUI_ANALYSIS: Raw data exists for each subtopic
- TUI_ANALYSIS -> SYNTHESIZING: TUI strategy summary written
- SYNTHESIZING -> HBR_EDITING: Draft article exists with 1500+ words
- HBR_EDITING -> VISUAL_GENERATION: Final article 2000-2500 words
- VISUAL_GENERATION -> MULTIMEDIA_PRODUCTION: 3+ professional PNG files
- MULTIMEDIA_PRODUCTION -> ASSEMBLY: Audio MP3 exists
- ASSEMBLY -> COMPLETED: PDF and HTML files exist

## Available Tools
- File operations: read_file, write_file, edit_file, ls, glob
- Shell execution: execute (for ffmpeg, etc.)
- **inkforge_generate_research_plan**: Create research plan from topic
- **inkforge_execute_research**: Run parallelized web research
- **inkforge_tui_analysis**: Analyze with TUI strategic context
- **inkforge_synthesize_article**: Create draft article from research
- **inkforge_hbr_edit**: Apply HBR-quality editing pass
- **inkforge_generate_visuals**: Create professional charts/diagrams
- **inkforge_produce_multimedia**: Generate audio and video
- **inkforge_assemble_deliverables**: Create PDF, HTML, ZIP package

## IMPORTANT: Tool Usage

When in each stage, use the corresponding tool:
- QUERY_FORMULATION: Use `inkforge_generate_research_plan`
- RESEARCHING: Use `inkforge_execute_research`
- TUI_ANALYSIS: Use `inkforge_tui_analysis`
- SYNTHESIZING: Use `inkforge_synthesize_article`
- HBR_EDITING: Use `inkforge_hbr_edit`
- VISUAL_GENERATION: Use `inkforge_generate_visuals`
- MULTIMEDIA_PRODUCTION: Use `inkforge_produce_multimedia`
- ASSEMBLY: Use `inkforge_assemble_deliverables`

## Each Iteration
1. Read state.json to know current stage
2. Verify quality gate for current stage is met
3. If met, advance to next stage and execute that stage's tool
4. If not met, fix issues in current stage
5. Update state.json with progress
6. Log actions to iteration_log.md
7. If you complete all work, set stage to COMPLETED

Remember: You have fresh context each iteration. Always read state first.
"""


# ============================================================================
# Webhook Notifications
# ============================================================================

async def send_webhook(
    config: WebhookConfig,
    event: str,
    data: Dict[str, Any]
) -> bool:
    """Send webhook notification."""
    if not config or event not in config.events:
        return False

    payload = {
        "event": event,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.url,
                json=payload,
                headers=config.headers,
                timeout=config.timeout
            )
            success = response.status_code < 400
            if success:
                print(f"[WEBHOOK] {event} sent to {config.url}")
            else:
                print(f"[WEBHOOK] Failed: {response.status_code}")
            return success
    except Exception as e:
        print(f"[WEBHOOK] Error: {e}")
        return False


# ============================================================================
# Git Operations
# ============================================================================

def git_init(workspace: Path) -> bool:
    """Initialize git repository in workspace if not exists."""
    git_dir = workspace / ".git"
    if git_dir.exists():
        return True

    try:
        subprocess.run(
            ["git", "init"],
            cwd=workspace,
            capture_output=True,
            check=True
        )
        # Create .gitignore
        gitignore = workspace / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/\n.DS_Store\n*.mp3\n*.mp4\n")
        print(f"[GIT] Initialized repository in {workspace}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[GIT] Init failed: {e}")
        return False


def git_commit(
    workspace: Path,
    message: str,
    config: GitConfig
) -> Optional[str]:
    """Create a git commit with all changes."""
    if not config.enabled or not config.auto_commit:
        return None

    try:
        # Set git config for this repo
        subprocess.run(
            ["git", "config", "user.name", config.author_name],
            cwd=workspace,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", config.author_email],
            cwd=workspace,
            capture_output=True
        )

        # Add all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=workspace,
            capture_output=True,
            check=True
        )

        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace,
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():
            return None  # No changes to commit

        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=True
        )

        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=True
        )

        commit_hash = result.stdout.strip()[:8]
        print(f"[GIT] Committed: {commit_hash} - {message[:50]}...")
        return commit_hash

    except subprocess.CalledProcessError as e:
        print(f"[GIT] Commit failed: {e}")
        return None


def git_log(workspace: Path, limit: int = 10) -> List[Dict[str, str]]:
    """Get recent git commits."""
    try:
        result = subprocess.run(
            ["git", "log", f"-{limit}", "--pretty=format:%H|%s|%ai"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=True
        )

        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|", 2)
                if len(parts) == 3:
                    commits.append({
                        "hash": parts[0][:8],
                        "message": parts[1],
                        "date": parts[2]
                    })
        return commits
    except subprocess.CalledProcessError:
        return []


def git_checkout(workspace: Path, commit_or_branch: str) -> bool:
    """Checkout a specific commit or branch."""
    try:
        subprocess.run(
            ["git", "checkout", commit_or_branch],
            cwd=workspace,
            capture_output=True,
            check=True
        )
        print(f"[GIT] Checked out: {commit_or_branch}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[GIT] Checkout failed: {e}")
        return False


# ============================================================================
# State Management
# ============================================================================

def create_initial_state(
    topic: str,
    key_concepts: List[str],
    target_audience: str
) -> dict:
    """Create initial state for a new InkForge Ralph mode session."""
    return {
        "topic": topic,
        "key_concepts": key_concepts,
        "target_audience": target_audience,
        "stage": Stage.INITIALIZED.value,
        "iteration": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "research_plan": None,
        "research_completed": False,
        "tui_analysis_completed": False,
        "draft_article_path": None,
        "final_article_path": None,
        "word_count": 0,
        "visual_assets": [],
        "multimedia": {
            "audio": None,
            "video": None,
        },
        "final_deliverables": {
            "pdf": None,
            "html": None,
            "package": None,
        },
        "errors": [],
        "history": [],  # Track stage transitions
        "git_commits": [],  # Track commits for audit trail
        "quality_scores": {},  # Track quality scores per stage
    }


def load_state(workspace: Path) -> Optional[dict]:
    """Load state from workspace. Returns None if file doesn't exist or has errors."""
    state_file = workspace / "state.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except json.JSONDecodeError as e:
            # Return error info so agent can fix it
            return {"_json_error": str(e), "_raw_content": state_file.read_text()[:500]}
    return None


def save_state(workspace: Path, state: dict):
    """Save state to workspace."""
    state["updated_at"] = datetime.now().isoformat()
    state_file = workspace / "state.json"
    state_file.write_text(json.dumps(state, indent=2, default=str))


def get_state_hash(state: dict) -> str:
    """Get hash of current state for change detection."""
    # Exclude volatile fields
    state_copy = {k: v for k, v in state.items() if k not in ["updated_at", "history", "git_commits"]}
    return hashlib.md5(json.dumps(state_copy, sort_keys=True, default=str).encode()).hexdigest()[:8]


# ============================================================================
# Resume Functionality
# ============================================================================

def list_available_checkpoints(workspace: Path) -> List[Dict[str, Any]]:
    """List available checkpoints to resume from."""
    checkpoints = []

    # Get git commits as checkpoints
    commits = git_log(workspace, limit=20)
    for commit in commits:
        checkpoints.append({
            "type": "git_commit",
            "id": commit["hash"],
            "message": commit["message"],
            "date": commit["date"]
        })

    # Get state history as checkpoints
    state = load_state(workspace)
    if state and "history" in state:
        for entry in state.get("history", []):
            checkpoints.append({
                "type": "state_history",
                "id": entry.get("state_hash"),
                "stage": entry.get("stage"),
                "iteration": entry.get("iteration"),
                "date": entry.get("timestamp")
            })

    return checkpoints


def resume_from_checkpoint(workspace: Path, checkpoint_id: str) -> bool:
    """Resume from a specific checkpoint."""
    # Try git checkout first
    if git_checkout(workspace, checkpoint_id):
        state = load_state(workspace)
        if state:
            print(f"[RESUME] Restored state from commit {checkpoint_id}")
            print(f"         Stage: {state.get('stage')}, Iteration: {state.get('iteration')}")
            return True

    print(f"[RESUME] Could not restore checkpoint: {checkpoint_id}")
    return False


# ============================================================================
# Agent Creation
# ============================================================================

def create_inkforge_agent(config: InkForgeConfig, custom_tools: List = None):
    """
    Create agent with Bedrock as primary and OpenAI as fallback.

    Sets up AWS credentials and creates the agent with proper error handling.
    """
    # Set AWS environment for Bedrock
    os.environ["AWS_PROFILE"] = config.bedrock.profile
    os.environ["AWS_DEFAULT_REGION"] = config.bedrock.region

    try:
        # Try Bedrock first
        print(f"[AGENT] Creating agent with Bedrock: {config.model}")
        print(f"[AGENT] AWS Profile: {config.bedrock.profile}, Region: {config.bedrock.region}")

        agent, backend = create_cli_agent(
            model=config.model,
            assistant_id="ralph-inkforge",
            system_prompt=RALPH_SYSTEM_PROMPT,
            auto_approve=True,
            tools=custom_tools or []
        )
        print("[AGENT] Bedrock agent created successfully")
        return agent, backend, config.model

    except Exception as e:
        print(f"[AGENT] Bedrock failed: {e}")
        print(f"[AGENT] Falling back to: {config.fallback_model}")

        # Fallback to OpenAI
        agent, backend = create_cli_agent(
            model=config.fallback_model,
            assistant_id="ralph-inkforge",
            system_prompt=RALPH_SYSTEM_PROMPT,
            auto_approve=True,
            tools=custom_tools or []
        )
        print("[AGENT] Fallback agent created successfully")
        return agent, backend, config.fallback_model


# ============================================================================
# Ralph Mode Loop
# ============================================================================

async def ralph_iteration(
    agent,
    backend,
    workspace: Path,
    iteration: int,
    task: str,
    config: InkForgeConfig
) -> bool:
    """
    Run a single Ralph mode iteration using deepagents_cli.

    Returns True if work should continue, False if complete.
    """
    # Check for JSON errors from previous iteration
    state = load_state(workspace)
    previous_stage = state.get("stage") if state and "_json_error" not in state else None
    previous_hash = get_state_hash(state) if state and "_json_error" not in state else None

    error_notice = ""
    if state and "_json_error" in state:
        error_notice = f"""
**CRITICAL: state.json has invalid JSON that YOU wrote in a previous iteration!**
Error: {state['_json_error']}
You MUST fix this by reading state.json, identifying the JSON syntax error, and rewriting it correctly.
This is YOUR mistake - fix it before doing anything else.
"""
        print(f"[SELF-CORRECTION] Agent must fix JSON error: {state['_json_error']}")

    # Build the iteration prompt
    prompt = f"""
Iteration #{iteration}
{error_notice}
Your task: {task}

Your previous work is in the filesystem at: {workspace}
Check state.json to see current progress and continue building.

If this is the first iteration, initialize the state and start with the first stage.
Otherwise, continue from where the last iteration left off.

Remember to:
1. Read state.json first
2. Do ONE meaningful unit of work (one stage transition)
3. Update state.json with progress (ENSURE VALID JSON!)
4. Append to iteration_log.md what you did
5. If you complete all work, set stage to COMPLETED

IMPORTANT: When writing JSON, always validate it is correct. No duplicate keys, proper commas.
"""

    # Run the agent using direct LangGraph API
    await execute_agent_task(
        user_input=prompt,
        agent=agent,
        thread_id=f"ralph-inkforge-{iteration}"
    )

    # Load updated state
    state = load_state(workspace)

    if state and "_json_error" not in state:
        current_stage = state.get("stage")
        current_hash = get_state_hash(state)

        # Track history
        if "history" not in state:
            state["history"] = []

        state["history"].append({
            "iteration": iteration,
            "stage": current_stage,
            "state_hash": current_hash,
            "timestamp": datetime.now().isoformat()
        })

        # Git commit after iteration
        if config.git.commit_on_iteration:
            commit_msg = f"Iteration {iteration}: {current_stage}"
            commit_hash = git_commit(workspace, commit_msg, config.git)
            if commit_hash:
                if "git_commits" not in state:
                    state["git_commits"] = []
                state["git_commits"].append({
                    "hash": commit_hash,
                    "iteration": iteration,
                    "stage": current_stage,
                    "timestamp": datetime.now().isoformat()
                })

        # Webhook on stage change
        if previous_stage and current_stage != previous_stage:
            if config.git.commit_on_stage_change:
                commit_msg = f"Stage change: {previous_stage} -> {current_stage}"
                git_commit(workspace, commit_msg, config.git)

            if config.webhook:
                await send_webhook(config.webhook, "stage_change", {
                    "previous_stage": previous_stage,
                    "current_stage": current_stage,
                    "iteration": iteration,
                    "workspace": str(workspace)
                })

        # Webhook on iteration complete
        if config.webhook:
            await send_webhook(config.webhook, "iteration_complete", {
                "iteration": iteration,
                "stage": current_stage,
                "state_hash": current_hash,
                "workspace": str(workspace)
            })

        save_state(workspace, state)

        # Check if completed
        if current_stage == Stage.COMPLETED.value:
            return False

    return True


async def emit_event(
    callback: Optional[Callable[[str, Dict], Awaitable[None]]],
    event_type: str,
    data: Dict[str, Any]
):
    """Emit an event through the callback if provided."""
    if callback:
        await callback(event_type, {
            "timestamp": datetime.now().isoformat(),
            **data
        })


async def ralph_mode_single(
    topic: str,
    key_concepts: List[str] = None,
    target_audience: str = "TUI Leadership and Strategy Teams",
    config: InkForgeConfig = None,
    event_callback: Optional[Callable[[str, Dict], Awaitable[None]]] = None
) -> Dict[str, Any]:
    """
    Run Ralph mode for InkForge newsletter generation (single instance).

    Ralph mode runs the agent in autonomous loops where:
    - Each loop starts with fresh context
    - The filesystem serves as persistent memory
    - The agent checks existing work and continues building

    Args:
        topic: Newsletter topic
        key_concepts: List of key concepts to cover
        target_audience: Target audience description
        config: InkForge configuration
        event_callback: Optional async callback for streaming events to frontend.
                       Signature: async def callback(event_type: str, data: dict)
                       Event types: iteration_start, stage_change, tool_call,
                                   thinking, progress, error, completed

    Returns:
        Dict with results including deliverable paths and final state
    """
    if not DEEPAGENTS_AVAILABLE:
        raise ImportError(
            "deepagents-cli is required. Install with: pip install deepagents-cli"
        )

    config = config or InkForgeConfig()
    key_concepts = key_concepts or []

    # Create workspace
    if config.workspace_dir:
        workspace = Path(config.workspace_dir)
    else:
        workspace = Path(tempfile.mkdtemp(prefix="inkforge_ralph_"))

    workspace.mkdir(parents=True, exist_ok=True)

    # Create InkForge directory structure
    directories = [
        workspace / "input",
        workspace / "research" / "raw_data",
        workspace / "content",
        workspace / "visuals",
        workspace / "multimedia",
        workspace / "deliverables",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    # Initialize git if enabled
    if config.git.enabled:
        git_init(workspace)

    # Handle resume
    if config.resume:
        state = load_state(workspace)
        if state and "_json_error" not in state:
            print(f"[RESUME] Found existing state at stage: {state.get('stage')}")
            print(f"         Iteration: {state.get('iteration')}")
            if state.get("git_commits"):
                print(f"         Git commits: {len(state['git_commits'])}")
        else:
            print("[RESUME] No valid state found, starting fresh")
            config = InkForgeConfig(
                workspace_dir=str(workspace),
                max_iterations=config.max_iterations,
                model=config.model,
                resume=False,
                webhook=config.webhook,
                git=config.git,
                parallel=config.parallel,
                target_audience=config.target_audience,
            )

    # Initialize state if not exists
    if not (workspace / "state.json").exists():
        initial_state = create_initial_state(
            topic=topic,
            key_concepts=key_concepts,
            target_audience=target_audience,
        )
        save_state(workspace, initial_state)

        if config.git.enabled:
            git_commit(workspace, "Initial state", config.git)

    # Initialize iteration log
    log_file = workspace / "iteration_log.md"
    if not log_file.exists():
        log_file.write_text(f"# InkForge Ralph Mode Log\n\nStarted: {datetime.now().isoformat()}\n\n")

    # Build task description
    task = f"""
Generate a strategic newsletter about: {topic}
Target Audience: {target_audience}
Key Concepts: {', '.join(key_concepts) if key_concepts else 'None specified'}

Requirements:
- 2000-2500 words (HBR quality)
- Include TUI strategic context (MANDATORY)
- Generate visual assets (charts, diagrams)
- Create PDF, HTML, and ZIP package
"""

    # Create agent with Ralph system prompt using deepagents_cli
    print(f"\n{'='*60}")
    print("InkForge Ralph Mode (Advanced)")
    print(f"{'='*60}")
    print(f"Topic: {topic}")
    print(f"Workspace: {workspace}")
    print(f"Model: {config.model}")
    print(f"Max Iterations: {config.max_iterations if config.max_iterations > 0 else 'unlimited'}")
    print(f"Git Enabled: {config.git.enabled}")
    print(f"Webhook: {config.webhook.url if config.webhook else 'disabled'}")
    print(f"Resume Mode: {config.resume}")
    print(f"{'='*60}\n")

    # Build custom tools list
    custom_tools = [
        inkforge_generate_research_plan,
        inkforge_execute_research,
        inkforge_tui_analysis,
        inkforge_synthesize_article,
        inkforge_hbr_edit,
        inkforge_generate_visuals,
        inkforge_produce_multimedia,
        inkforge_assemble_deliverables,
    ]

    print(f"[TOOLS] Registered {len(custom_tools)} InkForge tools")

    agent, backend, active_model = create_inkforge_agent(config, custom_tools)
    print(f"[AGENT] Active model: {active_model}")

    # Get starting iteration from state
    state = load_state(workspace)
    start_iteration = (state.get("iteration", 0) + 1) if state and "_json_error" not in state else 1

    # Run the loop
    iteration = start_iteration
    start_time = datetime.now()
    previous_stage = None

    try:
        while True:
            print(f"\n--- Iteration {iteration} ---")

            # Emit iteration_start event
            await emit_event(event_callback, "iteration_start", {
                "iteration": iteration,
                "max_iterations": config.max_iterations if config.max_iterations > 0 else 100
            })

            # Log iteration start
            with open(log_file, "a") as f:
                f.write(f"\n## Iteration {iteration}\n")
                f.write(f"Started: {datetime.now().isoformat()}\n\n")

            # Run iteration
            should_continue = await ralph_iteration(
                agent=agent,
                backend=backend,
                workspace=workspace,
                iteration=iteration,
                task=task,
                config=config
            )

            # Check for stage change and emit event
            current_state = load_state(workspace)
            if current_state and "_json_error" not in current_state:
                current_stage = current_state.get("stage")
                if current_stage != previous_stage:
                    await emit_event(event_callback, "stage_change", {
                        "previous_stage": previous_stage,
                        "current_stage": current_stage
                    })
                    previous_stage = current_stage

            # Check if done
            if not should_continue:
                print("\n[COMPLETED] Agent signaled completion.")

                # Final commit
                if config.git.enabled:
                    git_commit(workspace, "Newsletter generation completed", config.git)

                # Calculate duration
                duration = (datetime.now() - start_time).total_seconds()

                # Load final state for deliverables info
                final_state = load_state(workspace)
                deliverables = final_state.get("final_deliverables", {}) if final_state else {}

                # Emit completed event
                await emit_event(event_callback, "completed", {
                    "deliverables": deliverables,
                    "summary": "Newsletter generation completed successfully",
                    "total_iterations": iteration,
                    "duration_seconds": duration
                })

                # Webhook notification
                if config.webhook:
                    await send_webhook(config.webhook, "completed", {
                        "iterations": iteration,
                        "workspace": str(workspace),
                        "deliverables": deliverables
                    })
                break

            # Check iteration limit
            if config.max_iterations > 0 and iteration >= config.max_iterations:
                print(f"\n[LIMIT] Reached maximum iterations ({config.max_iterations})")
                break

            iteration += 1

    except KeyboardInterrupt:
        print(f"\n\n[INTERRUPTED] Stopped after {iteration} iterations")
        with open(log_file, "a") as f:
            f.write(f"\n## Interrupted\n")
            f.write(f"Stopped at iteration {iteration} by user\n")

        if config.git.enabled:
            git_commit(workspace, f"Interrupted at iteration {iteration}", config.git)

    # Load final state
    final_state = load_state(workspace)

    # List created files
    print(f"\n{'='*60}")
    print("Created files:")
    for f in workspace.rglob("*"):
        if f.is_file() and ".git" not in str(f):
            print(f"  - {f.relative_to(workspace)}")

    # Show git history
    if config.git.enabled:
        commits = git_log(workspace, limit=5)
        if commits:
            print(f"\nGit commits (last 5):")
            for c in commits:
                print(f"  - {c['hash']}: {c['message']}")

    print(f"{'='*60}")

    return {
        "success": final_state.get("stage") == Stage.COMPLETED.value if final_state else False,
        "iterations": iteration,
        "workspace": str(workspace),
        "state": final_state,
        "deliverables": final_state.get("final_deliverables", {}) if final_state else {},
        "git_commits": final_state.get("git_commits", []) if final_state else []
    }


async def ralph_mode(
    topic: str,
    key_concepts: List[str] = None,
    target_audience: str = "TUI Leadership and Strategy Teams",
    max_iterations: int = 0,
    model: str = f"bedrock:{BEDROCK_MODEL_ID}",
    workspace_dir: Optional[str] = None,
    resume: bool = False,
    webhook_url: Optional[str] = None,
    git_enabled: bool = True,
    parallel_workers: int = 0
) -> Dict[str, Any]:
    """
    Run Ralph mode for InkForge newsletter generation.

    This is the main entry point that supports all advanced features.

    Args:
        topic: Newsletter topic
        key_concepts: List of key concepts to cover
        target_audience: Target audience description
        max_iterations: Maximum iterations (0 = unlimited)
        model: LLM model to use (default: Bedrock Claude, fallback: OpenAI GPT-4o)
        workspace_dir: Directory for workspace
        resume: Whether to resume from existing state
        webhook_url: URL for webhook notifications
        git_enabled: Enable git commits for audit trail
        parallel_workers: Number of parallel workers (0 = disabled)

    Returns:
        Dict with results including deliverables and final state
    """
    config = InkForgeConfig(
        workspace_dir=workspace_dir,
        max_iterations=max_iterations,
        model=model,
        resume=resume,
        webhook=WebhookConfig(url=webhook_url) if webhook_url else None,
        git=GitConfig(enabled=git_enabled),
        parallel=ParallelConfig(enabled=parallel_workers > 0, max_workers=parallel_workers),
        target_audience=target_audience,
    )

    return await ralph_mode_single(
        topic=topic,
        key_concepts=key_concepts,
        target_audience=target_audience,
        config=config
    )


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Command-line interface for InkForge Ralph mode."""
    parser = argparse.ArgumentParser(
        description="InkForge Ralph Mode (Advanced) - Autonomous iterative newsletter generation"
    )
    parser.add_argument(
        "--topic", "-t",
        required=True,
        help="Newsletter topic"
    )
    parser.add_argument(
        "--key-concepts", "-k",
        help="Comma-separated key concepts (e.g., 'Agentic AI,Commerce,Travel')"
    )
    parser.add_argument(
        "--target-audience", "-a",
        default="TUI Leadership and Strategy Teams",
        help="Target audience description"
    )
    parser.add_argument(
        "--iterations", "-i",
        type=int,
        default=0,
        help="Maximum iterations (0 = unlimited)"
    )
    parser.add_argument(
        "--model", "-m",
        default=f"bedrock:{BEDROCK_MODEL_ID}",
        help="LLM model to use (default: Bedrock Claude, fallback: OpenAI GPT-4o)"
    )
    parser.add_argument(
        "--workspace", "-w",
        help="Workspace directory (auto-generated if not provided)"
    )
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        help="Resume from existing workspace state"
    )
    parser.add_argument(
        "--webhook",
        help="Webhook URL for notifications"
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Disable git commits"
    )
    parser.add_argument(
        "--parallel", "-p",
        type=int,
        default=0,
        help="Number of parallel workers (0 = disabled)"
    )
    parser.add_argument(
        "--list-checkpoints",
        action="store_true",
        help="List available checkpoints to resume from"
    )
    parser.add_argument(
        "--checkout",
        help="Checkout a specific commit/checkpoint before running"
    )

    args = parser.parse_args()

    if not DEEPAGENTS_AVAILABLE:
        print("Error: deepagents-cli is required")
        print("Install with: pip install deepagents-cli")
        sys.exit(1)

    # Handle list checkpoints
    if args.list_checkpoints:
        if not args.workspace:
            print("Error: --workspace required for --list-checkpoints")
            sys.exit(1)
        workspace = Path(args.workspace)
        if not workspace.exists():
            print(f"Error: Workspace not found: {workspace}")
            sys.exit(1)

        checkpoints = list_available_checkpoints(workspace)
        print(f"\nAvailable checkpoints in {workspace}:")
        for cp in checkpoints:
            print(f"  [{cp['type']}] {cp['id']}: {cp.get('message') or cp.get('stage', '')}")
        sys.exit(0)

    # Handle checkout
    if args.checkout:
        if not args.workspace:
            print("Error: --workspace required for --checkout")
            sys.exit(1)
        workspace = Path(args.workspace)
        if not resume_from_checkpoint(workspace, args.checkout):
            sys.exit(1)

    # Parse key concepts
    key_concepts = []
    if args.key_concepts:
        key_concepts = [c.strip() for c in args.key_concepts.split(",")]

    # Run Ralph mode
    result = asyncio.run(ralph_mode(
        topic=args.topic,
        key_concepts=key_concepts,
        target_audience=args.target_audience,
        max_iterations=args.iterations,
        model=args.model,
        workspace_dir=args.workspace,
        resume=args.resume,
        webhook_url=args.webhook,
        git_enabled=not args.no_git,
        parallel_workers=args.parallel
    ))

    # Print results
    print(f"\n{'='*60}")
    print("Results")
    print(f"{'='*60}")
    print(f"Success: {result['success']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Workspace: {result['workspace']}")

    if result.get('git_commits'):
        print(f"Git Commits: {len(result['git_commits'])}")

    if result['deliverables']:
        print("\nGenerated deliverables:")
        for fmt, path in result['deliverables'].items():
            if path:
                print(f"  - {fmt}: {path}")

    if not result['success']:
        state = result.get('state', {})
        print(f"\nFinal stage: {state.get('stage', 'unknown')}")
        if state.get('errors'):
            print("Errors:")
            for err in state['errors']:
                print(f"  - {err}")


if __name__ == "__main__":
    main()
