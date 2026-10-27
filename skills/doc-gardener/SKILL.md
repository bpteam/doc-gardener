---
name: doc-gardener
description: Repository-agnostic Markdown knowledge gardening. Set up or restructure a project's knowledge base with the user (scan, interview, proposal, approved migration), route tasks to the few docs and sections worth reading, keep docs in sync with code changes, audit link/graph health, and consolidate duplicates. Use when building or reorganizing docs, exploring documentation before work, changing documented behavior, or auditing knowledge quality.
license: MIT
compatibility: Python 3.10+ for bundled deterministic tools. Git optional (used for discovery and change impact). No LLM/API needed for structural checks.
---

# Doc Gardener

A **project-agnostic** skill inspired by Karpathy's linked-knowledge / LLM Wiki approach and OpenAI Docs Sync. It is a documentation specialist, **not** a coding orchestrator or a project framework. Never assume a business domain, language, directory layout, tech stack, documentation renderer, or mandatory metadata schema.

**Operating principle:** discover the repository's knowledge system first; follow its existing rules; improve navigation and evidence without introducing a competing knowledge base. Scripts establish facts; the agent makes judgments; the user approves structural change.

## References

- [`references/ONBOARDING.md`](references/ONBOARDING.md) — **BOOTSTRAP procedure**: scan → interview → proposal → approval → config → migration batches → activation. Read it before setting up or restructuring a knowledge base.
- [`references/KNOWLEDGE_ARCHITECTURE.md`](references/KNOWLEDGE_ARCHITECTURE.md) — how to choose canonical owners, file new material, link pages and build indexes. Read before BOOTSTRAP, CONSOLIDATE, or creating/moving docs.
- [`references/CONFIG.md`](references/CONFIG.md) (repo config), [`references/CI_EXAMPLE.md`](references/CI_EXAMPLE.md) (CI), [`references/HOOKS.md`](references/HOOKS.md) (agent hooks), [`assets/AGENTS_SNIPPET.md`](assets/AGENTS_SNIPPET.md) (activation rule), [`assets/templates/`](assets/templates/) (examples, **not** mandates).

## Always follow these invariants

1. **Repo conventions outrank this skill's suggestions.** Read applicable instructions, README, and existing docs indexes. If conflicts are unclear, report them; do not silently override the repository.
2. **Search before creating.** Use `route` and existing indexes to find the canonical owner. Prefer adding to an existing page or section rather than multiplying near-duplicates.
3. **Preserve the system's structure.** Documentation may live beside code, in `docs/`, `wiki/`, `handbook/`, multiple packages, or elsewhere. Do not impose a new taxonomy, frontmatter, heading names, naming scheme, or link syntax unless the user chose it during BOOTSTRAP.
4. **Use a connected but sparse graph.** Link from navigation entrypoints to pages, and between pages when the relation helps a reader. Backlinks are computed. Never make up connections to silence warnings.
5. **Keep canonical claims testable.** Code/tests/config/contracts verify current behavior; architecture policies and ADRs express intended constraints. If they disagree, report a discrepancy, not a silent rewrite to match a bug.
6. **Automation first.** Run the deterministic tools before reading broadly. Use judgment only for semantics, contradictions, ambiguous targets and safe consolidation.
7. **Minimal, reviewable diffs.** No mass reformatting, no deleting unique text, no rewriting decision history, no second wiki. Moves go through `move` (links rewritten mechanically) in their own commit, separate from content edits.
8. **Structural change needs approval.** Moving, renaming, merging, splitting or deleting pages, and writing `.doc-gardener.json`, happen only after the user approved the specific plan.

## Pick the smallest mode

| Mode | Trigger | Do |
| --- | --- | --- |
| **DISCOVER** | Need project knowledge for a task | `route "<task>"` → read the top **sections** (line ranges given) → follow neighbors/code refs only if needed. Read-only. |
| **BOOTSTRAP** | "Set up / organize the knowledge base here" | Follow [`references/ONBOARDING.md`](references/ONBOARDING.md): `scan` → ask the open questions → written proposal → approval → `init` → `move` batch → content batches → activation. |
| **SYNC** | Code or docs changed | `impact --base <rev>` → review `referencing_docs` / `documentation_candidates` → verify claims both ways → minimal updates → `check --changed <rev> --code-refs`. |
| **AUDIT** | Periodic / doc-health request | `check --all` → fix confirmed broken references → triage orphan/duplicate/stale-ref warnings → inspect semantic drift only where flagged. |
| **CONSOLIDATE** | Confirmed duplicate information | Compare owners/content (`check --duplicates` groups) → preserve unique information → merge into canonical page → `move`/link repair → check. |

## DISCOVER protocol

1. `route "<task in the user's words>"` — ranked pages, the best-matching sections with line ranges, approximate token cost, linked code paths, and graph neighbors. Run it with 2–3 phrasings (synonyms, component names) if the first result is weak.
2. Read only the listed sections first (use line offsets). Open a whole page only when the sections are insufficient.
3. Follow `code_refs` to the implementation when the task touches code; follow `neighbors` only when a dependency is unclear.
4. Stop when the task can be answered. If nothing relevant exists, say so — that is a documentation gap to report, not a reason to read everything.

## Documentation ↔ code synchronization (SYNC)

1. `impact --root . --base <rev> --json`:
   - `referencing_docs` — docs that link to or mention (as `path/like.ext`) a changed code path. Primary candidates; needs no config.
   - `documentation_candidates` — docs from configured `mappings`.
   - `docs_linking_to_changed_docs` — pages whose links/claims may need follow-up.
   - `unrouted_code_changes` — changed code no doc mentions. Decide whether that is fine (internal refactor) or a gap.
2. **Code → docs:** did interfaces, behavior, errors, configuration, permissions, deployment steps or architecture change? Update the canonical doc. A purely internal refactor may need no docs edit — say so.
3. **Docs → code:** verify changed claims against implementation and tests. If code violates a documented invariant, surface the conflict instead of deleting the rule.
4. `check --root . --changed <rev> --code-refs` — only findings related to the change (incremental, no full-repo review needed).

## Deterministic commands (no LLM, no dependencies)

Use the script from the **installed skill directory** (or a vendored copy, e.g. `tools/docgraph.py`) against the **target repository**:

```bash
G="python3 <skill-root>/scripts/docgraph.py"
$G scan  --root .                       # inventory, conventions, health, draft config, open questions
$G init  --root . [--write]             # preview / write draft .doc-gardener.json (refuses to overwrite)
$G route --root . "how are refunds retried"   # DISCOVER: pages + sections + code refs
$G check --root .                       # broken links, anchors, wiki-links (errors)
$G check --root . --all                 # + orphans, unreachable, duplicates (exact/section/near), stale code refs
$G check --root . --changed HEAD~1      # only findings related to changes since a revision
$G graph --root . --page docs/x.md      # backlinks, outgoing links, typed relations, code refs
$G impact --root . --base HEAD~1 --json # code/doc changes -> docs to review
$G move  --root . docs/a.md docs/guides/a.md      # dry run: moves + every link rewrite + follow-ups
$G move  --root . --plan moves.json --apply       # apply (git mv when tracked), then re-check
$G index --root . --dir docs [--file README.md] [--write | --check]
```

Notes: discovery scans all Markdown (`.md`, `.markdown`, `.mdx`) git knows about, skipping ignored, vendored and nested-repository files; narrow it with `--docs` or `.doc-gardener.json`. Errors exit 1; warnings are triage signals (`--strict` to fail on them). `move` rewrites inline links, reference definitions and wiki-links (code blocks untouched) and **reports** non-Markdown mentions (renderer nav, config, code comments) for manual follow-up. `init --write`, `index --write` and `move --apply` are the only write operations.

## CI and multi-agent integration

- CI: run `check` (errors) on every PR; keep `--all` warnings advisory. Use a pinned/vendored copy of the script. See [`references/CI_EXAMPLE.md`](references/CI_EXAMPLE.md).
- Activation: installing a skill does not make agents use it. Add [`assets/AGENTS_SNIPPET.md`](assets/AGENTS_SNIPPET.md) to the project's agent instructions (with consent). Optional Claude Code Stop hook: [`references/HOOKS.md`](references/HOOKS.md).
- Agent teams: one owner for edits to shared canonical docs; parallel agents report needed doc changes to that owner; one integrated `check --changed` after merging. This skill does not orchestrate teams.

## Completion report

State which docs were consulted/changed and why they are canonical, which code/tests support changed claims, which links/indexes were updated, which deterministic commands actually ran (with results), and unresolved semantic questions. Do not claim full code↔docs consistency based on a link scan.
