---
description: After code changes: find docs that need updating and update them
argument-hint: "[base revision, default HEAD]"
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py:*)", "Read", "Grep", "Glob", "Edit", "Bash(git diff:*)", "Bash(git log:*)"]
---

Use the **doc-gardener** skill in **SYNC** mode. Base revision: $ARGUMENTS (use `HEAD` if empty).

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py impact --root . --base <base> --json`.
2. For every entry in `referencing_docs` and `documentation_candidates`: read the code diff and the doc section; decide if the claim is still true.
3. Update the canonical doc minimally where behavior/interfaces/config/architecture changed. If code violates a documented invariant, report the conflict instead of rewriting the rule.
4. For `unrouted_code_changes`, say whether docs are needed (gap) or not (internal change).
5. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-gardener/scripts/docgraph.py check --root . --changed <base> --code-refs` and fix new errors.
6. Report: docs changed and why, docs reviewed but unchanged and why, open conflicts.
