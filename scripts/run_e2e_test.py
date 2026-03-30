#!/usr/bin/env python3
"""
E2E Test Runner for the Newsletter Agent System.

Runs the complete 9-agent pipeline with the UCP topic.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator.orchestrator import generate_newsletter


async def main():
    """Run E2E test with Universal Commerce Protocol topic."""
    print("=" * 70)
    print("E2E TEST: Leadership Strategy Newsletter Agent")
    print("=" * 70)
    print()
    print("Topic: Universal Commerce Protocol (UCP)")
    print("Key Concepts: Agentic AI, Commerce Protocols, Travel Technology")
    print()
    print("Starting pipeline...")
    print("-" * 70)

    try:
        result = await generate_newsletter(
            topic="Universal Commerce Protocol (UCP)",
            target_audience="TUI Leadership and Strategy Teams",
            key_concepts=["Agentic AI", "Commerce Protocols", "Travel Technology"],
            sub_topics=[
                {"name": "Technical architecture of UCP"},
                {"name": "Business implications for online travel agencies"},
                {"name": "Competitive landscape and adoption trends"},
            ],
            output_dir="output",
        )

        print()
        print("=" * 70)
        print("E2E TEST COMPLETE")
        print("=" * 70)
        print()
        print(f"Output directory: {result.output_dir}")
        print()

        # List generated files
        print("Generated files:")
        for subdir in ["content", "visuals", "multimedia", "final_deliverables"]:
            dir_path = result.output_dir / subdir
            if dir_path.exists():
                print(f"\n  {subdir}/")
                for f in sorted(dir_path.iterdir()):
                    if f.is_file():
                        size = f.stat().st_size
                        if size > 1024 * 1024:
                            size_str = f"{size / (1024*1024):.1f} MB"
                        elif size > 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        else:
                            size_str = f"{size} bytes"
                        print(f"    - {f.name} ({size_str})")

        # Show article stats
        final_article = result.content_dir / "final_article.md"
        if final_article.exists():
            content = final_article.read_text()
            word_count = len(content.split())
            print(f"\nArticle Statistics:")
            print(f"  - Word count: {word_count}")
            print(f"  - Target: 2000-2500 words")
            print(f"  - Status: {'✅ PASS' if 2000 <= word_count <= 2500 else '❌ FAIL'}")

        return result

    except Exception as e:
        print()
        print("=" * 70)
        print("E2E TEST FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
