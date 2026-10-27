---
description: Wire Doc Gardener into this project: agent rule, optional vendored script, CI, Stop hook
argument-hint: "[agents|ci|hook|all]"
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py:*)", "Read", "Grep", "Glob", "Edit", "Write", "Bash(mkdir:*)", "Bash(cp:*)"]
---

Use the **doc-gardener** skill. Requested: $ARGUMENTS (default: agents).

Options (ask which ones if unclear, apply only what the user confirms):
- **agents** — add the block from `${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/assets/AGENTS_SNIPPET.md` to the project's `AGENTS.md` / `CLAUDE.md` (whichever exists; ask if neither). Replace `DOCGRAPH` with a path valid in this repo (vendored `tools/docgraph.py` if chosen, else this plugin's script path).
- **vendor** — copy `${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py` to `tools/docgraph.py` (needed for CI and other agents).
- **ci** — add the workflow from `references/CI_EXAMPLE.md` (requires vendor).
- **hook** — add the Claude Code Stop hook from `references/HOOKS.md` to `.claude/settings.json` (requires vendor).

Show each file change before writing it. Report what was added.
