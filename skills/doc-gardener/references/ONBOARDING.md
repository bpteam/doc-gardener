# BOOTSTRAP: setting up or restructuring a knowledge base

Use when the user asks to "set up / organize / restructure the knowledge base (docs, wiki) here". The flow is a conversation with **gates**: nothing structural is written before the user approves the specific plan, and every write step is a separate, reviewable commit.

```text
1 Scan ──► 2 Interview ──► 3 Proposal ──► [approve?] ──► 4 Config ──► 5 Moves ──► 6 Content batches ──► 7 Activation ──► 8 Report
               ▲                │  no / change                          (commit)     (commit per batch)
               └────────────────┘
```

## 0. Preconditions

- Work on a branch or worktree; the working tree should be clean (`git status`). If it is not, ask before continuing — moves must be revertible as one diff.
- Read the project's agent instructions (`AGENTS.md`, `CLAUDE.md`, …) and README first. They outrank this procedure.

## 1. Scan (deterministic, no edits)

```bash
python3 <skill-root>/scripts/docgraph.py scan --root .        # human summary
python3 <skill-root>/scripts/docgraph.py scan --root . --json # full detail
```

`scan` reports: agent instruction files, docs renderers (MkDocs, Docusaurus, VitePress, mdBook, Sphinx, Jekyll, Hugo, Obsidian, SUMMARY.md, …), packages/components (by manifest files), documentation areas and folders, link style, frontmatter usage, filename style, script/language, generated-looking pages, very large pages, current health (broken links, orphans, duplicates, stale code references), a **draft `.doc-gardener.json`**, and **open questions with defaults**.

Then look yourself — the scan is not understanding:

- Open the top-level README, the main index of each doc area, and the renderer nav config if present.
- Skim headings of the 10–20 most linked pages (`graph --root .` / `scan --json` → `doc_dirs`).
- Note what each area is for, who it is written for, and where code and docs already correspond.

## 2. Interview (ask only what the repository cannot answer)

Take the scan's `questions`, drop the ones the repo already answers, and ask the rest **in one message**, each with the scan's default, so the user can reply "defaults are fine" or correct a few. Typical questions:

| Id | Question | Why it matters |
| --- | --- | --- |
| scope | Navigation only, moves/renames, or content restructuring too? | Bounds every later step. |
| audience | Agents, humans or both? | Index wording, page granularity. |
| canonical_root / placement | Central docs folder or docs near each component? | Prevents a second parallel KB. |
| renderer | Keep the renderer and its nav as the source of navigation? | Moves must update nav; link rules follow the renderer. |
| agent_tooling | Exclude agent skills/rules folders from the KB? | They configure agents, not the project. |
| generated | Exclude generated pages from checks and edits? | Tools rewrite them. |
| frontmatter / links | Adopt metadata or a link style, or keep current? | Mass injection is noisy; adopt only on purpose. |
| language | Language for new/updated text? | Consistency. |
| large_pages / duplicates | Split / consolidate flagged pages? | Context cost, drift. |
| activation | Add the Doc Gardener rule to agent instructions? | Otherwise DISCOVER/SYNC are not invoked reliably. |

Do not ask about things you can decide by convention (e.g. index filename when the repo already uses `README.md` per folder).

## 3. Proposal (written, concrete, reviewable)

Write the proposal to a file the user can open (e.g. `docs-proposal.md` in a scratch location or the PR description) and summarize it in chat. It must contain:

1. **Findings** — what exists, what works and will be kept, what hurts (unreachable areas, duplicates, giant pages, stale refs, missing entrypoints).
2. **Target layout** — a tree of the resulting structure. Show only folders that will have content. If the current layout is good, say so: the plan may be "keep layout, add indexes and links".
3. **Page map** — a table `current path → target path → action` with actions: `keep`, `move`, `rename`, `merge into <canonical>`, `split into <pages>`, `new index`, `exclude`. Every existing page appears exactly once (group large unchanged areas as one row, e.g. `docs/api/** → keep`).
4. **Navigation** — which entrypoints/indexes exist afterwards and what each routes (question/job → page).
5. **Config** — the `.doc-gardener.json` to be written (from `init`, edited).
6. **Batches** — order of execution (see 5–6), with what the user will review after each.
7. **Not changing** — explicitly: renderer, frontmatter, link style, historical ADRs, generated docs, … as agreed.
8. **Risks / follow-ups** — external links into moved pages, renderer nav, code comments, bookmarks; how they are handled.

Also produce the move plan as JSON for step 5:

```json
{"moves": [
  {"from": "wiki/setup.md", "to": "docs/guides/setup.md"},
  {"from": "notes/adr", "to": "docs/decisions"}
]}
```

Validate it **before** showing the proposal: `move --root . --plan moves.json` (dry run) lists every link rewrite and every non-Markdown mention that needs a manual follow-up. Put the follow-up list into the proposal's risks section.

**Gate:** wait for explicit approval. On "no" or changes, revise the proposal (back to 2 if the answers changed). Approval covers only what the proposal lists.

## 4. Config

```bash
python3 <skill-root>/scripts/docgraph.py init --root .          # preview
python3 <skill-root>/scripts/docgraph.py init --root . --write  # writes .doc-gardener.json (never overwrites)
```

Edit the file to match the approved proposal (target paths for `entrypoints`/`mappings` if moves are coming). Commit together with step 5 or separately.

## 5. Moves (mechanical, one commit)

```bash
python3 <skill-root>/scripts/docgraph.py move --root . --plan moves.json --apply
python3 <skill-root>/scripts/docgraph.py check --root .
```

- Uses `git mv` for tracked files (history preserved); rewrites inline links, reference definitions and wiki-links in all Markdown; moves assets inside moved folders; removes emptied folders; re-checks and lists any broken reference.
- Apply the reported manual follow-ups (renderer nav, config, code comments) in the same commit.
- **No content edits in this commit.** Pure renames keep the diff reviewable and git rename detection intact.
- Commit: `docs: restructure knowledge base layout (moves only)`.

## 6. Content batches (one area or concern per commit)

Typical batch kinds, in this order:

1. **Indexes/entrypoints** — routing pages per area (`question/job → canonical link → code location`); never copies of content. `index --dir <dir> --write` can produce a managed listing block inside a human-written index.
2. **Consolidation** — merge confirmed duplicates into the canonical page; preserve unique facts; leave the absorbed page's inbound links pointing to the canonical page (use `move` + edit, or edit links directly); delete the absorbed page only when the proposal said so.
3. **Splits** — break giant pages along separate reader questions; old page becomes an overview linking to the parts (keeps inbound links valid).
4. **Linking** — add meaningful cross-links (`Depends on`, `Used by`, `Implements`, `See also` where it helps) and implementation references (`path/to/code` links) so that `impact` can route future changes.
5. **Gaps** — new pages only for agreed topics with real content.

After every batch: `check --root . --all`, show the user the diff summary, commit. Stop and ask if a batch reveals something the proposal did not anticipate (contradictions between docs and code, unclear ownership).

## 7. Activation (with consent)

- Add [`assets/AGENTS_SNIPPET.md`](../assets/AGENTS_SNIPPET.md) to the project's agent instructions (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules/…`), with the script path that works in this repo.
- Optionally vendor the script for CI/other agents: copy `scripts/docgraph.py` to e.g. `tools/docgraph.py` (pin the version in a comment).
- Optionally add CI ([`CI_EXAMPLE.md`](CI_EXAMPLE.md)) and a Stop hook ([`HOOKS.md`](HOOKS.md)).

## 8. Report

What moved (count, plan file), what was merged/split/created, which indexes are the entrypoints now, config written, checks before vs after (errors, orphans, unreachable, duplicates), follow-ups not done, and open semantic questions.

## Greenfield (no docs yet)

Same flow with a smaller proposal: README as entrypoint, one doc root named by the project's conventions, an index, and only the pages that have real content now (typically architecture overview, setup/development guide, decisions log). No empty folders; categories grow when content appears. See [`KNOWLEDGE_ARCHITECTURE.md`](KNOWLEDGE_ARCHITECTURE.md) §4.
