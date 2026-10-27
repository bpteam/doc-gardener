---
description: Find the docs and sections worth reading for a task (read-only)
argument-hint: "<task or question>"
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py:*)", "Read", "Grep", "Glob"]
---

Use the **doc-gardener** skill in **DISCOVER** mode. Task: $ARGUMENTS

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py route --root . "$ARGUMENTS"`. If results are weak, retry with 1–2 rephrasings (synonyms, component names).
2. Read only the listed sections (use the line ranges), then follow `code_refs`/neighbors only if needed.
3. Answer with: the canonical pages for this task (path + one line why), the key facts relevant to the task, implementation locations, and any gap (nothing documented) worth reporting. Do not edit files.
