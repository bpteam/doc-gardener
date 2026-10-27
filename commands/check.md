---
description: Audit knowledge-base health: links, anchors, orphans, duplicates, stale code refs
argument-hint: "[--docs path] (optional scope)"
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py:*)", "Read", "Grep", "Glob", "Edit"]
---

Use the **doc-gardener** skill in **AUDIT** mode.

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py check --root . --all $ARGUMENTS`.
2. Group findings: errors (broken links/anchors/wiki-links) → stale code refs → duplicates → orphans/unreachable.
3. For each error, determine the correct target (search moved/renamed files). Propose fixes as a list; apply only unambiguous link fixes after the user confirms.
4. For warnings: say which are real problems and which are intentional (e.g. standalone pages, examples); suggest config entries (`allow_orphans`, `exclude`, `code_ref_ignore`) for intentional ones instead of fabricated links.
5. Re-run the check and report before/after counts.
