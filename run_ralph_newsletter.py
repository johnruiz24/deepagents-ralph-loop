#!/usr/bin/env python3
"""
InkForge Ralph Mode - Simplified Newsletter Generation
Uses Claude Code's built-in capabilities for iterative execution.
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
Para executar o Ralph Loop, use Claude Code com este prompt:

```
Você é um agente Ralph Mode para geração de newsletters.
Seu workspace é: /tmp/inkforge_ralph_newsletter

CADA ITERAÇÃO:
1. Leia state.json para saber o stage atual
2. Execute UMA unidade de trabalho
3. Atualize state.json com progresso
4. Adicione log em iteration_log.md
5. Se completar, defina stage = "COMPLETED"

STAGES:
- INITIALIZED → QUERY_FORMULATION (gerar queries de pesquisa)
- QUERY_FORMULATION → RESEARCHING (simular pesquisa)
- RESEARCHING → SYNTHESIZING (criar draft do artigo)
- SYNTHESIZING → COMPLETED (finalizar)

Comece lendo o state.json e execute a primeira iteração.
```

O padrão Ralph garante que:
- Cada iteração tem contexto fresco
- Filesystem serve como memória
- Se houver erro, auto-corrige na próxima iteração
""")

print("\n[READY] Workspace inicializado. Execute o prompt acima no Claude Code.")
