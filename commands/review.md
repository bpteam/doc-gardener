---
description: Review the current branch for docs drift without editing (report only)
argument-hint: "[base branch or revision, default: merge-base with main/master]"
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py:*)", "Read", "Grep", "Glob", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git merge-base:*)", "Bash(git rev-parse:*)"]
---

Use the **doc-gardener** skill (SYNC checks, read-only). Base: $ARGUMENTS; if empty use `git merge-base HEAD main` (or `master`).

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py impact --root . --base <base> --json` and `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py check --root . --changed <base> --all`.
2. Verify routed docs against the diff in both directions (code → docs, changed docs → code).
3. Report findings ranked by severity: wrong claims, missing docs for changed behavior, broken references, stale code refs, duplicates introduced. Each with file:line and suggested fix. **Do not edit files.**
