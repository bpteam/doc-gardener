---
description: Quick snapshot of the repo's knowledge system: conventions, health, draft config (read-only)
argument-hint: ""
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py:*)", "Read", "Grep", "Glob"]
---

Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py scan --root .` and summarize for the user: where docs live, conventions in use, renderer/agent files, health counts, the draft config, and the open questions. Suggest the next command (`/doc-gardener:init`, `/doc-gardener:check` or `/doc-gardener:find`). Do not edit files.
