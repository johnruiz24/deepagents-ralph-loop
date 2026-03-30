#!/usr/bin/env python3
"""
RALPH LOOP Style Newsletter Runner.

Provides iteration-by-iteration progress with visual feedback,
state tracking, and iteration logs.
"""
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ANSI colors
class C:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


def banner(text: str):
    print(f"\n{C.BOLD}{C.CYAN}{'='*70}{C.END}")
    print(f"{C.BOLD}{C.CYAN}  {text}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'='*70}{C.END}\n")


def iteration_header(num: int, phase: str, total_phases: int = 8):
    print(f"\n{C.DIM}--- Iteration {num} ---{C.END}")
    print(f"\n{C.BOLD}Phase {num}/{total_phases}: {phase.upper()}{C.END}")


def log_action(action: str, detail: str = ""):
    timestamp = datetime.now().strftime("%H:%M:%S")
    if detail:
        print(f"  {C.DIM}[{timestamp}]{C.END} {action}: {C.CYAN}{detail}{C.END}")
    else:
        print(f"  {C.DIM}[{timestamp}]{C.END} {action}")


def show_state_diff(key: str, old_val, new_val):
    print(f"\n  {C.DIM}=== State Update ==={C.END}")
    print(f"  {C.RED}- {key}: {str(old_val)[:50]}{C.END}")
    print(f"  {C.GREEN}+ {key}: {str(new_val)[:50]}{C.END}")


def show_result(passed: bool, quality: float = None, time_s: float = None):
    if passed:
        status = f"{C.GREEN}✅ PASSED{C.END}"
    else:
        status = f"{C.RED}❌ FAILED{C.END}"

    quality_str = f" (quality: {quality:.0f}/100)" if quality else ""
    time_str = f" [{time_s:.1f}s]" if time_s else ""
    print(f"\n  {C.BOLD}Result:{C.END} {status}{quality_str}{time_str}")


def write_iteration_log(log_file: Path, iteration: int, phase: str, actions: list, result: dict):
    """Append to iteration log file."""
    with open(log_file, "a") as f:
        f.write(f"\n## Iteration {iteration}\n")
        f.write(f"Started: {datetime.now().isoformat()}\n")
        f.write(f"Phase: {phase}\n")
        for action in actions:
            f.write(f"- {action}\n")
        f.write(f"Result: {'PASSED' if result.get('success') else 'FAILED'}\n")
        if result.get('quality_score'):
            f.write(f"Quality: {result['quality_score']:.0f}/100\n")


async def run_phase(factory, shared_state, phase_name: str, iteration: int, log_file: Path):
    """Run a single phase with Ralph-style logging."""
    iteration_header(iteration, phase_name)

    actions = []
    start = time.time()

    # Log: Reading state
    log_action("Reading state", f"phase={phase_name}")
    actions.append(f"Read state for {phase_name}")

    # Show state before
    old_phase = shared_state.state.get("current_phase", "init")

    try:
        # Create and execute agent
        log_action("Creating agent", factory.__name__)
        agent = factory(shared_state)

        log_action("Executing agent", "Running...")
        result = await agent.execute()

        elapsed = time.time() - start

        # Log actions
        actions.append(f"Executed {factory.__name__}")
        actions.append(f"Duration: {elapsed:.1f}s")

        # Show state diff
        new_phase = shared_state.state.get("current_phase", phase_name)
        if old_phase != new_phase:
            show_state_diff("current_phase", old_phase, new_phase)

        # Show word count if available
        word_count = shared_state.state.get("word_count")
        if word_count:
            log_action("Word count", str(word_count))
            actions.append(f"Word count: {word_count}")

        # Show visual assets count after visuals phase
        if "visual" in phase_name.lower():
            visual_assets = shared_state.state.get("visual_assets", [])
            png_count = len(list(shared_state.visuals_dir.glob("*.png")))
            log_action("Visual assets in state", str(len(visual_assets)))
            log_action("PNG files in directory", str(png_count))
            actions.append(f"Visual assets: {len(visual_assets)} (state), {png_count} (files)")

        # Show multimedia status after multimedia phase
        if "multimedia" in phase_name.lower():
            mm = shared_state.state.get("multimedia", {})
            audio_ok = mm.get("audio", {}).get("filename") is not None
            video_ok = mm.get("video", {}).get("filename") is not None
            log_action("Audio generated", "✓" if audio_ok else "✗")
            log_action("Video generated", "✓" if video_ok else "✗")
            actions.append(f"Audio: {'OK' if audio_ok else 'FAILED'}, Video: {'OK' if video_ok else 'FAILED'}")

        # Show final deliverables after assembly phase
        if "assembly" in phase_name.lower():
            final = shared_state.state.get("final_deliverables", {})
            log_action("PDF generated", "✓" if final.get("pdf") else "✗")
            log_action("HTML generated", "✓" if final.get("html") else "✗")
            log_action("ZIP package", "✓" if final.get("package") else "✗")
            # Check for images in PDF directory
            pdf_path = final.get("pdf")
            if pdf_path:
                import os
                pdf_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
                log_action("PDF size", f"{pdf_size/1024:.1f}KB")

        # Show result
        show_result(result.success, result.quality_score, elapsed)

        # Write to iteration log
        write_iteration_log(
            log_file,
            iteration,
            phase_name,
            actions,
            {"success": result.success, "quality_score": result.quality_score}
        )

        return result.success, result

    except Exception as e:
        elapsed = time.time() - start
        log_action("Error", str(e)[:80])
        show_result(False, None, elapsed)
        write_iteration_log(log_file, iteration, phase_name, actions + [f"Error: {e}"], {"success": False})
        return False, None


def show_final_results(workspace: Path, results: dict, total_time: float):
    """Show final results summary with detailed stats."""
    banner("FINAL RESULTS")

    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    # Summary box
    print(f"┌{'─'*50}┐")
    print(f"│ {'SUCCESS' if failed == 0 else 'PARTIAL':<48} │")
    print(f"├{'─'*50}┤")
    print(f"│ Total Iterations: {len(results):<30} │")
    print(f"│ Passed: {C.GREEN}{passed}{C.END}{' '*(40-len(str(passed)))} │")
    print(f"│ Failed: {C.RED if failed > 0 else C.DIM}{failed}{C.END}{' '*(40-len(str(failed)))} │")
    print(f"│ Duration: {total_time:.1f}s{' '*(37-len(f'{total_time:.1f}'))} │")
    print(f"└{'─'*50}┘")

    # Iteration details
    print(f"\n{C.BOLD}[ITERATION DETAILS]{C.END}")
    for i, (phase, success) in enumerate(results.items(), 1):
        icon = f"{C.GREEN}✓{C.END}" if success else f"{C.RED}✗{C.END}"
        print(f"  {icon} Iteration {i}: {phase}")

    # Visual assets check
    visuals_dir = workspace / "visuals"
    if visuals_dir.exists():
        png_files = list(visuals_dir.glob("*.png"))
        print(f"\n{C.BOLD}[VISUAL ASSETS]{C.END}")
        print(f"  PNG images generated: {C.CYAN}{len(png_files)}{C.END}")
        for png in sorted(png_files)[:6]:
            size = png.stat().st_size / 1024
            print(f"    {C.DIM}├─{C.END} {png.name} ({size:.1f}KB)")

    # Multimedia check
    mm_dir = workspace / "multimedia"
    if mm_dir.exists():
        audio_files = list(mm_dir.glob("*.mp3"))
        video_files = list(mm_dir.glob("*.mp4"))
        print(f"\n{C.BOLD}[MULTIMEDIA]{C.END}")
        print(f"  Audio files: {len(audio_files)}")
        print(f"  Video files: {len(video_files)}")
        for f in audio_files + video_files:
            size = f.stat().st_size / 1024
            print(f"    {C.DIM}├─{C.END} {f.name} ({size:.1f}KB)")

    # Final deliverables check
    final_dir = workspace / "final_deliverables"
    if final_dir.exists():
        print(f"\n{C.BOLD}[FINAL DELIVERABLES]{C.END}")
        for f in sorted(final_dir.iterdir()):
            if f.is_file():
                size = f.stat().st_size
                if size > 1024 * 1024:
                    size_str = f"{size/(1024*1024):.1f}MB"
                elif size > 1024:
                    size_str = f"{size/1024:.1f}KB"
                else:
                    size_str = f"{size}B"
                icon = "📄" if f.suffix == ".pdf" else "🌐" if f.suffix == ".html" else "📦" if f.suffix == ".zip" else "📋"
                print(f"    {icon} {f.name} ({size_str})")

    # Article stats
    for article_name in ["final_article.md", "draft_article.md"]:
        article = workspace / "content" / article_name
        if article.exists():
            content = article.read_text()
            words = len(content.split())
            in_range = 2000 <= words <= 2500
            status = f"{C.GREEN}✅ PASS{C.END}" if in_range else f"{C.RED}❌ OUT OF RANGE{C.END}"
            print(f"\n{C.BOLD}[ARTICLE QUALITY]{C.END}")
            print(f"  ┌{'─'*40}┐")
            print(f"  │ File: {article_name:<32} │")
            print(f"  │ Words: {words:<33} │")
            print(f"  │ Target: 2000-2500{' '*21} │")
            print(f"  │ Status: {'PASS ✓' if in_range else 'FAIL ✗':<32} │")
            print(f"  └{'─'*40}┘")
            break

    # Show iteration log (compact)
    log_file = workspace / "iteration_log.md"
    if log_file.exists():
        print(f"\n{C.BOLD}[FULL LOG]{C.END} {log_file}")


async def main():
    """Run newsletter generation with Ralph Loop style output."""
    from src.state.shared_state import create_shared_state
    from src.agents.query_formulation_agent import create_query_formulation_agent
    from src.agents.research_agent import create_research_agent
    from src.agents.tui_strategy_agent import create_tui_strategy_agent
    from src.agents.synthesis_agent import create_synthesis_agent
    from src.agents.hbr_editor_agent import create_hbr_editor_agent
    from src.agents.visual_asset_agent import create_visual_asset_agent
    from src.agents.multimedia_agent import create_multimedia_agent
    from src.agents.assembly_agent import create_assembly_agent

    banner("RALPH LOOP - NEWSLETTER GENERATION")

    print("Watch the agent progress through stages:")
    print(f"  {C.DIM}QUERY_FORMULATION -> RESEARCH -> TUI_ANALYSIS -> SYNTHESIS{C.END}")
    print(f"  {C.DIM}-> EDITING -> VISUALS -> MULTIMEDIA -> ASSEMBLY -> COMPLETE{C.END}")

    # Task description
    task = """
Generate a strategic newsletter about Universal Commerce Protocol (UCP)
for TUI Leadership and Strategy Teams.

Key concepts: Agentic AI, Commerce Protocols, Travel Technology

Sub-topics:
1. Technical architecture of UCP
2. Business implications for online travel agencies
3. Competitive landscape and adoption trends

Requirements:
- 2000-2500 words (HBR quality)
- Include TUI strategic context (MANDATORY)
- Generate visual assets (charts, diagrams)
- Create PDF, HTML, and ZIP package
"""

    print(f"\n{C.BOLD}[TASK]{C.END}")
    print(f"{C.DIM}{task.strip()}{C.END}")

    # Initialize shared state
    shared_state = create_shared_state(
        topic="Universal Commerce Protocol (UCP)",
        target_audience="TUI Leadership and Strategy Teams",
        key_concepts=["Agentic AI", "Commerce Protocols", "Travel Technology"],
        output_base_dir="output",
    )

    shared_state.write_topics_and_subtopics([
        {"name": "Technical architecture of UCP"},
        {"name": "Business implications for online travel agencies"},
        {"name": "Competitive landscape and adoption trends"},
    ])

    workspace = shared_state.output_dir
    print(f"\n{C.BOLD}[WORKSPACE]{C.END} {workspace}")

    # Initialize iteration log
    log_file = workspace / "iteration_log.md"
    log_file.write_text(f"# Newsletter Generation Log\nStarted: {datetime.now().isoformat()}\n")

    # Save initial state
    state_file = workspace / "state.json"
    state_file.write_text(json.dumps({
        "stage": "QUERY_FORMULATION",
        "iteration": 0,
        "created_at": datetime.now().isoformat(),
        "topic": "Universal Commerce Protocol (UCP)",
        "target_audience": "TUI Leadership and Strategy Teams",
    }, indent=2))

    print(f"\n{C.BOLD}[INIT]{C.END} Created workspace and state.json")

    banner("Starting Ralph Loop - Watch the iterations...")

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

    results = {}
    start_time = time.time()

    for i, (name, factory) in enumerate(phases, 1):
        # Update state file
        state = json.loads(state_file.read_text())
        state["stage"] = name.upper().replace(" ", "_")
        state["iteration"] = i
        state["updated_at"] = datetime.now().isoformat()
        state_file.write_text(json.dumps(state, indent=2))

        shared_state.set_phase(name.lower().replace(" ", "_"))

        success, result = await run_phase(factory, shared_state, name, i, log_file)
        results[name] = success

        # Stop on critical failures
        if not success and name in ["TUI Strategy Analysis", "Parallelized Research"]:
            print(f"\n{C.RED}[CRITICAL] Phase {name} failed. Stopping.{C.END}")
            break

    # Mark complete
    state = json.loads(state_file.read_text())
    state["stage"] = "COMPLETED"
    state["completed_at"] = datetime.now().isoformat()
    state_file.write_text(json.dumps(state, indent=2))

    total_time = time.time() - start_time

    # Show final results
    show_final_results(workspace, results, total_time)

    return sum(1 for v in results.values() if not v) == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}[INTERRUPTED]{C.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{C.RED}[ERROR] {e}{C.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
