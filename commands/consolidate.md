---
description: Find duplicated knowledge and merge it into canonical pages without losing facts
argument-hint: "[--docs path] (optional scope)"
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py:*)", "Read", "Grep", "Glob", "Edit", "Write"]
---

Use the **doc-gardener** skill in **CONSOLIDATE** mode and its `references/KNOWLEDGE_ARCHITECTURE.md` §3.

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py check --root . --duplicates $ARGUMENTS --json`; take `exact_duplicate`, `duplicate_section`, `near_duplicate` groups.
2. For each group: read both, decide if it is a real duplicate or a valid audience-specific copy; pick the canonical owner with evidence.
3. Present a merge plan (canonical page, unique facts to carry over, links to repoint, pages to delete or keep as short pointers). **Wait for approval.**
4. Apply group by group; run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py check --root .` after each; report.
