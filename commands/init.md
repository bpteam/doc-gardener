---
description: Set up or restructure this repo's knowledge base with you (scan, questions, proposal, approved migration)
argument-hint: "[what you want, e.g. 'restructure docs' or 'navigation only']"
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py:*)", "Read", "Grep", "Glob", "Edit", "Write", "Bash(git status:*)", "Bash(git mv:*)"]
---

Use the **doc-gardener** skill in **BOOTSTRAP** mode and follow its `references/ONBOARDING.md` step by step. User's intent: $ARGUMENTS

Tool: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py` (below: DOCGRAPH).

1. Check `git status`. If the tree is dirty, say so and ask before continuing.
2. Run `python3 DOCGRAPH scan --root .`, then read the main entrypoints yourself (root README, each docs area index, renderer nav config).
3. Ask the open questions the repository cannot answer **in one message**, each with the scan's default.
4. Write the proposal (findings, target tree, page map current → target → action, navigation, config, batches, what stays unchanged, risks). Build `moves.json` and validate it with `python3 DOCGRAPH move --root . --plan moves.json` (dry run); list its follow-ups under risks.
5. **Stop and wait for approval.** Revise on feedback.
6. Only after approval: `init --write`, `move --plan moves.json --apply` (moves-only commit), then content batches with `check --root . --all` after each, then offer activation (`/doc-gardener:activate`).
