#!/usr/bin/env python3
"""
CLI Runner for Newsletter Agent System.

Provides Ralph Loop-style visual progress tracking.
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ANSI colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def print_header(title: str):
    """Print a styled header."""
    print()
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
    print()


def print_phase(phase_num: int, total: int, name: str, status: str = "Running"):
    """Print phase progress."""
    status_color = Colors.YELLOW if status == "Running" else Colors.GREEN if status == "PASSED" else Colors.RED
    print(f"\n{Colors.BOLD}Phase {phase_num}/{total}: {name.upper()}{Colors.ENDC}")
    print(f"  {Colors.DIM}├─{Colors.ENDC} Status: {status_color}{status}{Colors.ENDC}")


def print_phase_detail(key: str, value: str):
    """Print phase detail."""
    print(f"  {Colors.DIM}├─{Colors.ENDC} {key}: {value}")


def print_phase_result(passed: bool, quality: float = None, details: str = None):
    """Print phase result."""
    if passed:
        symbol = f"{Colors.GREEN}✅{Colors.ENDC}"
        status = f"{Colors.GREEN}PASSED{Colors.ENDC}"
    else:
        symbol = f"{Colors.RED}❌{Colors.ENDC}"
        status = f"{Colors.RED}FAILED{Colors.ENDC}"

    quality_str = f" (quality: {quality:.0f}/100)" if quality else ""
    print(f"  {Colors.DIM}└─{Colors.ENDC} {symbol} {status}{quality_str}")
    if details:
        print(f"     {Colors.DIM}{details}{Colors.ENDC}")


def print_output_summary(output_dir: Path):
    """Print summary of generated outputs."""
    print_header("OUTPUT SUMMARY")

    print(f"Output: {Colors.CYAN}{output_dir}{Colors.ENDC}")

    subdirs = ["content", "visuals", "multimedia", "final_deliverables"]
    for subdir in subdirs:
        dir_path = output_dir / subdir
        if dir_path.exists():
            files = list(dir_path.iterdir())
            if files:
                print(f"\n  {Colors.BOLD}{subdir}/{Colors.ENDC}")
                for f in sorted(files):
                    if f.is_file():
                        size = f.stat().st_size
                        if size > 1024 * 1024:
                            size_str = f"{size / (1024*1024):.1f} MB"
                        elif size > 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        else:
                            size_str = f"{size} bytes"
                        print(f"    {Colors.DIM}├─{Colors.ENDC} {f.name} ({size_str})")


async def run_phase(phase_name: str, phase_func, phase_num: int, total_phases: int):
    """Run a single phase with progress display."""
    print_phase(phase_num, total_phases, phase_name, "Running...")

    start_time = time.time()
    try:
        result = await phase_func()
        elapsed = time.time() - start_time

        print_phase_detail("Time", f"{elapsed:.1f}s")

        if isinstance(result, dict):
            quality = result.get("quality_score", None)
            details = result.get("details", None)
            passed = result.get("passed", True)
        else:
            quality = None
            details = None
            passed = result is not None

        print_phase_result(passed, quality, details)
        return result

    except Exception as e:
        elapsed = time.time() - start_time
        print_phase_detail("Time", f"{elapsed:.1f}s")
        print_phase_result(False, details=str(e)[:100])
        raise


async def main():
    """Run the newsletter generation with visual progress."""
    from src.orchestrator.orchestrator import Orchestrator
    from src.state.shared_state import SharedState

    print_header("NEWSLETTER GENERATION - Universal Commerce Protocol")

    print(f"{Colors.DIM}Topic:{Colors.ENDC} Universal Commerce Protocol (UCP)")
    print(f"{Colors.DIM}Target:{Colors.ENDC} TUI Leadership and Strategy Teams")
    print(f"{Colors.DIM}Key Concepts:{Colors.ENDC} Agentic AI, Commerce Protocols, Travel Technology")
    print()

    # Initialize
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / f"newsletter_ucp_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    shared_state = SharedState(output_dir)
    shared_state.update_state(
        topic="Universal Commerce Protocol (UCP)",
        target_audience="TUI Leadership and Strategy Teams",
        key_concepts=["Agentic AI", "Commerce Protocols", "Travel Technology"],
        sub_topics=[
            {"name": "Technical architecture of UCP"},
            {"name": "Business implications for online travel agencies"},
            {"name": "Competitive landscape and adoption trends"},
        ],
    )

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

    total_phases = len(phases)
    results = {}

    for i, (name, func) in enumerate(phases, 1):
        try:
            result = await run_phase(name, func, i, total_phases)
            results[name] = result
        except Exception as e:
            print(f"\n{Colors.RED}Phase {name} failed: {e}{Colors.ENDC}")
            # Continue with remaining phases if possible
            results[name] = None

    # Final summary
    print_header("GENERATION COMPLETE! 🎉")
    print_output_summary(output_dir)

    # Article stats
    final_article = output_dir / "content" / "final_article.md"
    if final_article.exists():
        content = final_article.read_text()
        word_count = len(content.split())

        print(f"\n{Colors.BOLD}Article Statistics:{Colors.ENDC}")
        print(f"  {Colors.DIM}├─{Colors.ENDC} Word count: {word_count}")
        print(f"  {Colors.DIM}├─{Colors.ENDC} Target: 2000-2500 words")

        if 2000 <= word_count <= 2500:
            print(f"  {Colors.DIM}└─{Colors.ENDC} Status: {Colors.GREEN}✅ PASS{Colors.ENDC}")
        else:
            print(f"  {Colors.DIM}└─{Colors.ENDC} Status: {Colors.RED}❌ FAIL{Colors.ENDC}")

    return output_dir


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        print(f"\n{Colors.GREEN}Done!{Colors.ENDC}")
        sys.exit(0)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
