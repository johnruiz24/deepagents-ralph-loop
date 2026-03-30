#!/usr/bin/env python3
"""
Simplified E2E Test with Visual Progress.

Ralph Loop-style step-by-step execution with clear feedback.
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ANSI colors
class C:
    H = '\033[95m'  # Header
    B = '\033[94m'  # Blue
    C = '\033[96m'  # Cyan
    G = '\033[92m'  # Green
    Y = '\033[93m'  # Yellow
    R = '\033[91m'  # Red
    E = '\033[0m'   # End
    BOLD = '\033[1m'
    DIM = '\033[2m'


def header(text: str):
    print(f"\n{C.BOLD}{C.C}{'='*70}{C.E}")
    print(f"{C.BOLD}{C.C}  {text}{C.E}")
    print(f"{C.BOLD}{C.C}{'='*70}{C.E}\n")


def phase_start(num: int, total: int, name: str):
    print(f"\n{C.BOLD}Phase {num}/{total}: {name.upper()}{C.E}")
    print(f"  {C.DIM}├─{C.E} Iteration: 1/3")
    print(f"  {C.DIM}├─{C.E} Status: {C.Y}Running...{C.E}", end="", flush=True)


def phase_update(msg: str):
    print(f"\r  {C.DIM}├─{C.E} Status: {C.Y}{msg}{C.E}".ljust(60), end="", flush=True)


def phase_done(passed: bool, quality: float = None, time_s: float = None, detail: str = None):
    if passed:
        status = f"{C.G}✅ PASSED{C.E}"
    else:
        status = f"{C.R}❌ FAILED{C.E}"

    quality_str = f" (quality: {quality:.0f}/100)" if quality else ""
    time_str = f" [{time_s:.1f}s]" if time_s else ""

    print(f"\r  {C.DIM}├─{C.E} Status: {status}{quality_str}{time_str}".ljust(70))
    if detail:
        print(f"  {C.DIM}└─{C.E} {C.DIM}{detail[:60]}{C.E}")


async def run_agent_phase(agent_class, shared_state, phase_num: int, total: int, name: str):
    """Run a single agent phase with progress display."""
    phase_start(phase_num, total, name)

    start = time.time()
    try:
        agent = agent_class(shared_state)
        result = await agent.execute()
        elapsed = time.time() - start

        if result.success:
            phase_done(True, result.quality_score, elapsed)
            return True
        else:
            phase_done(False, None, elapsed, result.error or result.message)
            return False

    except Exception as e:
        elapsed = time.time() - start
        phase_done(False, None, elapsed, str(e)[:100])
        return False


async def main():
    """Run simplified E2E test."""
    from src.state.shared_state import create_shared_state

    # Import agents
    from src.agents.query_formulation_agent import create_query_formulation_agent
    from src.agents.research_agent import create_research_agent
    from src.agents.tui_strategy_agent import create_tui_strategy_agent
    from src.agents.synthesis_agent import create_synthesis_agent
    from src.agents.hbr_editor_agent import create_hbr_editor_agent
    from src.agents.visual_asset_agent import create_visual_asset_agent
    from src.agents.multimedia_agent import create_multimedia_agent
    from src.agents.assembly_agent import create_assembly_agent

    header("NEWSLETTER GENERATION - Universal Commerce Protocol")

    print(f"{C.DIM}Topic:{C.E} Universal Commerce Protocol (UCP)")
    print(f"{C.DIM}Target:{C.E} TUI Leadership and Strategy Teams")
    print(f"{C.DIM}Key Concepts:{C.E} Agentic AI, Commerce Protocols, Travel Technology")

    # Initialize shared state
    shared_state = create_shared_state(
        topic="Universal Commerce Protocol (UCP)",
        target_audience="TUI Leadership and Strategy Teams",
        key_concepts=["Agentic AI", "Commerce Protocols", "Travel Technology"],
        output_base_dir="output",
    )

    # Write subtopics
    shared_state.write_topics_and_subtopics([
        {"name": "Technical architecture of UCP"},
        {"name": "Business implications for online travel agencies"},
        {"name": "Competitive landscape and adoption trends"},
    ])

    print(f"\n{C.DIM}Output:{C.E} {shared_state.output_dir}")

    # Define phases
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

    total = len(phases)
    results = {}
    start_time = time.time()

    for i, (name, factory) in enumerate(phases, 1):
        shared_state.set_phase(name.lower().replace(" ", "_"))

        success = await run_agent_phase(factory, shared_state, i, total, name)
        results[name] = success

        # Stop on critical failures
        if not success and name in ["TUI Strategy Analysis", "Parallelized Research"]:
            print(f"\n{C.R}Critical phase failed. Stopping.{C.E}")
            break

    # Summary
    total_time = time.time() - start_time
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    header(f"COMPLETE! {'🎉' if failed == 0 else '⚠️'}")

    print(f"Output: {C.C}{shared_state.output_dir}{C.E}")
    print(f"Duration: {total_time:.1f}s")
    print(f"Phases: {C.G}{passed} passed{C.E}, {C.R if failed else C.DIM}{failed} failed{C.E}")

    # List files
    for subdir in ["content", "visuals", "multimedia", "final_deliverables"]:
        dir_path = shared_state.output_dir / subdir
        if dir_path.exists():
            files = list(dir_path.iterdir())
            if files:
                print(f"\n  {C.BOLD}{subdir}/{C.E}")
                for f in sorted(files)[:5]:
                    if f.is_file():
                        size = f.stat().st_size
                        if size > 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        else:
                            size_str = f"{size} bytes"
                        print(f"    {C.DIM}├─{C.E} {f.name} ({size_str})")

    # Article stats
    final = shared_state.output_dir / "content" / "final_article.md"
    draft = shared_state.output_dir / "content" / "draft_article.md"

    article = final if final.exists() else draft if draft.exists() else None

    if article and article.exists():
        content = article.read_text()
        words = len(content.split())
        print(f"\n{C.BOLD}Article:{C.E}")
        print(f"  {C.DIM}├─{C.E} Word count: {words}")
        print(f"  {C.DIM}├─{C.E} Target: 2000-2500 words")
        status = f"{C.G}✅ PASS{C.E}" if 2000 <= words <= 2500 else f"{C.R}❌ FAIL{C.E}"
        print(f"  {C.DIM}└─{C.E} Status: {status}")

    return failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{C.Y}Interrupted{C.E}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{C.R}Error: {e}{C.E}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
