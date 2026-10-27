---
description: Move/rename docs or folders and rewrite every link (dry run, then apply on approval)
argument-hint: "<src> <dst> [<src> <dst> ...] | --plan moves.json"
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py:*)", "Read", "Grep", "Glob", "Bash(git status:*)"]
---

Use the **doc-gardener** skill. Arguments: $ARGUMENTS

1. Dry run: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py move --root . $ARGUMENTS`. Show the moves, the number of link rewrites, and every manual follow-up (renderer nav, config, code comments).
2. Ask for approval. Mention if `git status` is dirty (moves should be their own commit).
3. On approval: re-run with `--apply`, fix the reported follow-ups, run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py check --root .`, report.
