#!/usr/bin/env python3
"""
InkForge Ralph Mode - Newsletter Generation Workspace Initializer
Sets up the workspace for iterative Ralph loop execution.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Setup
os.environ["AWS_PROFILE"] = os.environ.get("AWS_PROFILE", "mll-dev")
os.environ["AWS_DEFAULT_REGION"] = "eu-central-1"

print("="*60)
print("INKFORGE RALPH MODE - NEWSLETTER GENERATION")
print("="*60)

# Workspace setup
workspace = Path("/tmp/inkforge_ralph_newsletter")
if workspace.exists():
    import shutil
    shutil.rmtree(workspace)

workspace.mkdir(parents=True, exist_ok=True)
for d in ["content", "visuals", "research", "deliverables"]:
    (workspace / d).mkdir(exist_ok=True)

# Configuration
topic = "Universal Commerce Protocol (UCP)"
key_concepts = ["Agentic AI", "Commerce Protocols", "Travel Technology"]

# Initial state
state = {
    "topic": topic,
    "key_concepts": key_concepts,
    "target_audience": "TUI Leadership",
    "stage": "INITIALIZED",
    "iteration": 0,
    "created_at": datetime.now().isoformat(),
    "research_queries": [],
    "draft_article": None,
    "errors": [],
    "history": []
}

(workspace / "state.json").write_text(json.dumps(state, indent=2))

# Iteration log
log = f"""# InkForge Ralph Mode Log
Started: {datetime.now().isoformat()}
Topic: {topic}
Key Concepts: {', '.join(key_concepts)}

## Workflow Stages
1. QUERY_FORMULATION - Generate search queries
2. RESEARCHING - Execute research
3. SYNTHESIZING - Create draft
4. COMPLETED - Done

---
"""
(workspace / "iteration_log.md").write_text(log)

print(f"\n[INIT] Workspace: {workspace}")
print(f"       Topic: {topic}")
print(f"       Stage: INITIALIZED")
print(f"\n[INFO] State saved to: {workspace / 'state.json'}")
print(f"[INFO] Log at: {workspace / 'iteration_log.md'}")

print("\n" + "="*60)
print("RALPH MODE INSTRUCTIONS")
print("="*60)
print("""
To execute the Ralph Loop, use Claude Code with this prompt:

```
You are a Ralph Mode agent for newsletter generation.
Your workspace is: /tmp/inkforge_ralph_newsletter

EACH ITERATION:
1. Read state.json to know the current stage
2. Execute ONE unit of work
3. Update state.json with progress
4. Add log entry to iteration_log.md
5. If complete, set stage = "COMPLETED"

STAGES:
- INITIALIZED → QUERY_FORMULATION (generate research queries)
- QUERY_FORMULATION → RESEARCHING (simulate research)
- RESEARCHING → SYNTHESIZING (create article draft)
- SYNTHESIZING → COMPLETED (finalize)

Start by reading state.json and execute the first iteration.
```

The Ralph pattern ensures:
- Fresh context each iteration
- Filesystem serves as memory
- If there's an error, auto-correct in next iteration
""")

print("\n[READY] Workspace initialized. Execute the prompt above in Claude Code.")
