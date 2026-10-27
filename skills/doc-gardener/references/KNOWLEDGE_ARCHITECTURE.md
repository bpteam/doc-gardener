# Knowledge architecture: project-adaptive rules

**Read before BOOTSTRAP, CONSOLIDATE, creating pages, moving docs, or changing navigation.** This is a *decision procedure*, not a prescribed folder layout. The skill must work with monorepos, small libraries, websites, infrastructure repositories, research projects and non-software knowledge repositories.

## 1. Order of authority (never reverse)

1. Explicit instructions and maintained conventions **of the target repository**.
2. Existing canonical documentation, navigation, docs-site configuration, and repository architecture.
3. The needs of the specific audience/task, including constraints of the documentation renderer.
4. **Only when no usable convention exists:** the optional defaults below.

Do not treat this skill's example names, English headings, frontmatter fields, status labels or folder taxonomy as universal. Never copy examples that do not describe the repository.

## 2. Discover the real knowledge system

Before proposing a structure, inspect:

- Root instructions (`AGENTS.md`, `CLAUDE.md`, `README.md`) and any package-level equivalents.
- Existing documentation roots (e.g. `docs`, `doc`, `wiki`, `handbook`, `knowledge`, package-local READMEs) plus site navigation such as `mkdocs.yml`, `SUMMARY.md`, Docusaurus sidebar or VitePress config if present.
- Whether docs are hand-authored, generated from source, synchronized from another repository, or produced as handoff summaries.
- Current titles, layout, filenames, section conventions, frontmatter, links, glossary, and owners.
- What belongs close to code versus centrally, and how cross-component topics are documented.

Start with `docgraph.py scan --root .`: it reports these facts (instructions, renderers, packages, areas, link/frontmatter/filename conventions, generated and large pages, health) plus a draft config and open questions. Then verify by reading the main entrypoints. Deliver an **inventory** before any substantial BOOTSTRAP: scopes, entrypoints, canonical sources, duplicate candidates, broken references, conventions to retain, gaps, and a *minimal change plan*. Don't create a shadow `wiki/` from summaries of existing docs.

## 3. Canonical ownership and create-vs-update decision

For each claim or topic:

1. Search existing names, aliases, headings, code paths and docs text. Follow entrypoints and backlinks.
2. Identify the **single canonical owner** of the detailed explanation/contract. A guide can summarize a concept, but should link to the owner for details.
3. Prefer editing an existing relevant section; avoid creating one file per class, endpoint or small behavior.
4. New page only if there is a separate lasting reader question, substantial durable content, and an identifiable navigation home. If not, extend an existing page.
5. Before merging/deleting, preserve information unique to each page; repair all incoming links; maintain deprecation/redirect policies of the project; don't rewrite historical decisions silently.
6. If the owner is ambiguous, list candidates and evidence; don't fabricate a source of truth.

**Not every repeated sentence is a duplicate**: short summaries, tutorials, compatibility notes and audience-specific introductions can be valid. The risk is independently maintained copies of authoritative detail.

## 4. Folder and index strategy (adaptive)

Prefer the structure already used by the repository:

- Component-oriented docs near code are reasonable for monorepos. Keep `packages/<package>/README.md` or `<component>/doc/` if used.
- One `docs/` root is reasonable for a single product, library, or site already using it.
- For unusual cases (wiki, book, handbook, research notebooks), keep their existing organization and renderer semantics.

**When a new project has no structure at all**, one possible *optional* starting point is:

```text
README.md                   # entrypoint to the repo and its knowledge
<existing-doc-root>/       # name chosen by project, not by skill
  INDEX.md                  # reader-task routing page
  architecture/             # system-wide design (only if there is such content)
  guides/                   # procedures (only if needed)
  reference/                # exact contracts/config (only if needed)
  decisions/                # historical decisions (only if needed)
```

This is not a required tree. **Do not create empty directories.** `concepts/`, `plans/`, and other categories are optional, not universally valuable. Use nearby package indexes rather than aggregating everything into one big file.

A useful index has a small map from **question/job → canonical link → code/source location (if applicable)**. Maintain relevant names/synonyms so that users and agents can discover terminology. An index is not another copy of the content. Use the repo's standard index filenames (`README.md`, `INDEX.md`, `SUMMARY.md`, nav configuration) rather than imposing one.

The bundled `docgraph.py index` generates an **optional supplemental listing** only in a managed block; it never replaces human routing or edits a non-managed index.

## 5. Page shape: recommended, not mandatory

Follow the repo's Markdown conventions. A good standalone page generally answers:

- **What?** One H1 (or renderer-required title) and a short summary answering the likely question.
- **Why/when?** Context, scope, boundaries and invariants where relevant.
- **How?** Behavior, steps, interfaces or decisions, appropriate to the page's purpose.
- **Evidence?** Real source file, tests, contracts, examples, specs, ADRs; do not invent paths.
- **Neighbors?** Meaningful links to related canonical pages and navigation entrypoints.

**Sample (neutral, not a template requirement):**

```markdown
# Retry policy

How the service retries transient failures, and which failures are never retried.

## Behavior
...

## Constraints
...

## Implementation
- Code: [retry scheduler](../../src/retry_scheduler.py)
- Tests: [retry tests](../../tests/test_retry.py)

## Related
- **Depends on:** [Error categories](error-categories.md)
- **Used by:** [Background jobs](../architecture/jobs.md)
```

**Optional metadata** (only if repository already uses frontmatter or chooses to adopt it):

```yaml
---
id: retry-policy
title: Retry policy
summary: When retryable jobs are scheduled again.
kind: reference
status: current
---
```

Different repos may use `description`, `sidebar_position`, `weight`, `slug`, custom page types, localized metadata or no frontmatter. Do not inject the above fields merely to satisfy this skill. `status` may refer to doc lifecycle and must not be confused with the implementation status of individual features.

**Optional headings by purpose, adapt to local idiom:** architecture (context, boundaries, invariants, tradeoffs); how-to (prerequisites, steps, verify, troubleshoot); API reference (contract, parameters, errors, source); decisions (context, choice, consequences, date). Don't write empty headings for symmetry.

## 6. Semantic links and backlinks

Goal: a navigable, **purposeful** knowledge graph, not a maximal number of links.

1. Follow repository format: relative `[label](path.md#section)` for portability by default; preserve `[[Wiki page]]` where the actual renderer understands wiki-links.
2. Every actively maintained canonical page should be findable from an existing local navigation entrypoint where practical. Exceptions include changelogs, generated docs, historical archives and intentionally standalone pages.
3. Link concepts when the relation affects understanding, implementation, impact analysis or navigation. Typical optional edge labels: `Depends on`, `Used by`, `Implements`, `Supersedes`, `See also`; **do not mandate a `## Relationships` section**.
4. Links may appear in prose, indexes, tables or an optional explicit `Related` / `Relationships` section. Use the format the repository already uses.
5. Backlinks are computed mechanically. Don't maintain a duplicate backlinks list unless the target system requires one.
6. If a page is unreachable/orphaned, inspect whether it *should* be in scope first. A script cannot infer semantic relevance and must not fabricate links.
7. When moving/renaming pages, repair inbound links and anchors. Automated path fixes only when the exact target is unambiguous, preferably as reviewed diffs.

### Deterministic versus semantic findings

| Can be computed without LLM | Requires code/context or human/agent judgment |
| --- | --- |
| Broken local paths, missing heading anchors, backlinks | Which other page should link to this page |
| Pages unreachable from configured index roots | Whether an orphan is intentional or missing coverage |
| Exact duplicate bodies, identical sections, near-duplicate pages (shingle similarity) | Whether similar text is a real duplicate or a valid audience-specific copy |
| `path/like.ext` mentions and links to code that no longer exist | Whether the surrounding claim is still true |
| Duplicate page identifiers (when IDs exist) | Contradictions in requirements vs implementation |
| Docs that link to / mention changed code; configured ownership mappings | Whether a code change actually requires a docs update |
| Lexical routing of a task to pages and sections (`route`) | Which of the routed pages is actually canonical |

## 7. Maintenance protocol and gates

- **DISCOVER:** select minimal relevant docs and inspect their real code/source links; no file changes.
- **BOOTSTRAP:** inventory + small navigation improvements first; preserve paths; add optional standards only by explicit project choice.
- **SYNC:** identify changed public behavior/contracts, verify canonical docs, update links and examples, run checks; document why no change was needed if appropriate.
- **AUDIT:** run deterministic scan, fix confirmed broken references, triage orphan/duplicate warnings, then investigate code↔docs divergence selectively.
- **CONSOLIDATE:** only after confirming duplicate authority; protect unique content, archived ADRs and generated sources; update all inbound links.

Prefer one shared-docs editor per parallel agent team. Do not require full repo-wide re-auditing per small code change: `impact` and `check --changed <rev>` scope the work to what changed. CI can enforce deterministic link errors; orphan/duplicate warnings should usually be advisory. No script can prove all documentation is correct.

## 8. Tools and adoption

- `scan` — inventory + draft config + open questions (BOOTSTRAP step 1). `init --write` writes the draft.
- `route "<task>"` — DISCOVER: ranked pages, best sections with line ranges, code refs, neighbors.
- `check` — broken links/anchors/wiki-links; `--all` adds orphans, unreachable pages, duplicates and stale code refs; `--changed <rev>` limits findings to a change.
- `graph` — backlinks, outgoing links, typed relations, code refs of a page.
- `impact --base <rev>` — changed code → docs that reference it (+ configured `mappings`).
- `move` — rename/move pages or folders and rewrite every affected link; dry run by default.
- `index` — optional managed listing block; `--check` for staleness/coverage.

`--policy` is an **opt-in metadata check** that respects `.doc-gardener.json` `metadata_profile`. Default is `none`: do not require frontmatter or heading names. Set `metadata_profile` to `doc-gardener` only for documentation that intentionally adopts the example profile (see `references/CONFIG.md`).
