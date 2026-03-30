#!/usr/bin/env python3
"""
Publish Ralph article to Medium using agent-browser automation
"""

import subprocess
import time
import re
import os
from pathlib import Path

def run_browser_command(cmd):
    """Run agent-browser command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

def escape_for_shell(text):
    """Escape text for safe shell passage via heredoc"""
    # Use single quotes and avoid special characters
    return text.replace("'", "'\\''")

def paste_content_section(content, delay=0.5):
    """Paste content section via clipboard"""
    # Replace newlines for safer shell handling
    content_escaped = content.replace('"', '\\"').replace('\n', '\\n')

    # Use printf to handle escaping properly
    cmd = f'''agent-browser clipboard write "{content_escaped}" && sleep {delay} && agent-browser clipboard paste && sleep 1'''
    print(f"Pasting section ({len(content)} chars)...")
    run_browser_command(cmd)

def main():
    # Read article
    article_path = Path("/Users/john.ruiz/Documents/projects/inkforge/ralph/MEDIUM_ARTICLE_PRODUCTION_READY_V2.md")
    article_content = article_path.read_text()

    # Remove markdown heading (already used for title)
    lines = article_content.split('\n')
    # Skip the title line and blank lines
    content_lines = []
    skip_next_line = False
    for i, line in enumerate(lines):
        if i == 0:  # Skip first heading
            skip_next_line = True
            continue
        if skip_next_line and line.strip() == '':
            continue
        skip_next_line = False
        content_lines.append(line)

    article_body = '\n'.join(content_lines)

    # Split into manageable chunks (Medium editor can handle ~5000 chars per paste)
    # Break at section boundaries (##) when possible
    sections = re.split(r'(^##\s+.*$)', article_body, flags=re.MULTILINE)

    print(f"Article split into {len(sections)} sections")
    print("Starting content paste...")

    # Paste each section
    chunk_size = 2000
    current_chunk = ""

    for section in sections:
        if not section.strip():
            continue

        # If section is small enough, add to current chunk
        if len(current_chunk) + len(section) < chunk_size:
            current_chunk += section + "\n"
        else:
            # Paste current chunk if it has content
            if current_chunk.strip():
                paste_content_section(current_chunk)
            # Start new chunk
            current_chunk = section + "\n"

    # Paste final chunk
    if current_chunk.strip():
        paste_content_section(current_chunk)

    print("\n✅ Content pasted successfully!")

    # Wait for Medium to process
    print("Waiting for Medium to process content...")
    time.sleep(3)

    # Get current URL
    result = run_browser_command("agent-browser get url")
    print(f"\n📄 Draft URL: {result.strip()}")

    # Take screenshot
    screenshot_path = run_browser_command("agent-browser screenshot --screenshot-dir /tmp")
    print(f"📸 Screenshot saved")

    print("\n✅ Article published as DRAFT to Medium!")
    print("Next steps: Review the draft, add images, and publish when ready.")

if __name__ == "__main__":
    main()
