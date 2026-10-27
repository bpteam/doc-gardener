# Doc Gardener

**Global, repository-agnostic documentation Skill.** Combines linked-knowledge practices inspired by Karpathy's LLM Wiki idea (see also [Hermes llm-wiki](https://github.com/hermes-agent-org/hermes/blob/main/skills/research/llm-wiki/SKILL.md)) with bidirectional code↔docs review inspired by [OpenAI Docs Sync](https://github.com/openai/openai-agents-python/blob/main/.agents/skills/docs-sync/SKILL.md). Independently adapted, not a vendored copy of either.

It helps an agent **set up, find, organize, link, update and audit documentation in any repository without imposing a knowledge-base structure**. Existing conventions win. New taxonomy, frontmatter, typed relation headings or wiki-link syntax are adopted only when the user chooses them.

## What using it looks like

> **You:** Set up a proper knowledge base in this repo.
>
> **Agent:** runs `scan` → reads the main entrypoints → asks 4–6 questions with defaults (scope of change, central vs per-package docs, renderer, what to exclude, …) → writes a proposal: target tree, page map (`current → target → action`), indexes, config, batches, what stays untouched, link follow-ups (validated by a `move` dry run).
>
> **You:** OK / change X.
>
> **Agent:** writes `.doc-gardener.json` → applies moves in one commit (`git mv`, all links rewritten) → content batches (indexes, merges, splits, cross-links), each checked and committed → adds the activation rule to `AGENTS.md`/`CLAUDE.md` → reports before/after health.

Afterwards, in everyday work: `route` before a task (read only the relevant sections), `impact` + `check --changed` after code changes.

The full procedure: [`skills/doc-gardener/references/ONBOARDING.md`](skills/doc-gardener/references/ONBOARDING.md).

## Installation

The repository is both a **Claude Code plugin** (with its own marketplace) and a **skill package** for [`npx skills`](https://www.npmjs.com/package/skills). Pick one per agent: plugin for Claude Code, `npx skills` for Codex, Cursor and others. Installing both for Claude Code gives two copies of the same skill.

Examples use `bpteam/doc-gardener`; replace it with your GitHub `owner/repo` if you forked.

### Claude Code: plugin from GitHub

Inside Claude Code:

```text
/plugin marketplace add bpteam/doc-gardener
/plugin install doc-gardener@doc-gardener
```

Or from a shell:

```bash
claude plugin marketplace add bpteam/doc-gardener
```

```bash
claude plugin install doc-gardener@doc-gardener
```

Restart the session; the commands appear in the `+` / `/` menu:

| Command | Does |
| --- | --- |
| `/doc-gardener:init [intent]` | BOOTSTRAP: scan → questions → proposal → approval → config, moves, content batches |
| `/doc-gardener:scan` | Read-only snapshot: where docs live, conventions, health, draft config |
| `/doc-gardener:find <task>` | DISCOVER: docs and sections worth reading for a task |
| `/doc-gardener:check` | AUDIT: links, anchors, orphans, duplicates, stale code refs; fixes on confirmation |
| `/doc-gardener:sync [base]` | SYNC: docs affected by code changes since `base` (default `HEAD`), updated |
| `/doc-gardener:review [base]` | Read-only docs-drift review of the branch |
| `/doc-gardener:move <src> <dst>` | Move/rename docs with link rewriting (dry run, then apply) |
| `/doc-gardener:consolidate` | Merge duplicated knowledge into canonical pages |
| `/doc-gardener:activate [agents\|vendor\|ci\|hook]` | Wire into the project: agent rule, vendored script, CI, Stop hook |

Update / remove:

```bash
claude plugin marketplace update doc-gardener
```

```bash
claude plugin update doc-gardener@doc-gardener
```

```bash
claude plugin uninstall doc-gardener@doc-gardener
```

### Codex, Cursor and other agents: skill from GitHub via `npx skills`

```bash
npx skills add bpteam/doc-gardener --skill doc-gardener -g -a codex -a cursor -y
```

`-g` installs for the user (all projects); drop it to install into the current project only. `-a` picks agents (`'*'` for all supported). Interactive selection: `npx skills add https://github.com/bpteam/doc-gardener`.

Update / list / remove:

```bash
npx skills update doc-gardener -g -y
```

```bash
npx skills list -g
```

```bash
npx skills remove doc-gardener -g -y
```

### Local checkout (development)

Same commands with a path instead of `owner/repo`: `/plugin marketplace add ~/p/doc-gardener`, `npx skills add ~/p/doc-gardener --skill doc-gardener -g -a codex -y`. Both copy the files: after local edits run the update commands above (plugin) or `npx skills add` again (skill).

### After installing

Neither method installs hooks, CI or project rules. For reliable use run `/doc-gardener:activate` in a project (or add [`skills/doc-gardener/assets/AGENTS_SNIPPET.md`](skills/doc-gardener/assets/AGENTS_SNIPPET.md) to its agent instructions).

## Files

- [`SKILL.md`](skills/doc-gardener/SKILL.md) — triggers, invariants, modes, commands.
- [`skills/doc-gardener/references/ONBOARDING.md`](skills/doc-gardener/references/ONBOARDING.md) — BOOTSTRAP: scan → interview → proposal → approval → config → moves → content batches → activation.
- [`skills/doc-gardener/references/KNOWLEDGE_ARCHITECTURE.md`](skills/doc-gardener/references/KNOWLEDGE_ARCHITECTURE.md) — canonical ownership, create-vs-update, folder/index strategy, page shape, linking.
- [`skills/doc-gardener/references/CONFIG.md`](skills/doc-gardener/references/CONFIG.md) — optional `.doc-gardener.json`, what the parser understands.
- [`skills/doc-gardener/references/CI_EXAMPLE.md`](skills/doc-gardener/references/CI_EXAMPLE.md), [`skills/doc-gardener/references/HOOKS.md`](skills/doc-gardener/references/HOOKS.md) — CI and Claude Code Stop hook examples.
- [`skills/doc-gardener/assets/AGENTS_SNIPPET.md`](skills/doc-gardener/assets/AGENTS_SNIPPET.md) — activation rule; [`skills/doc-gardener/assets/templates/`](skills/doc-gardener/assets/templates/) — optional page examples.
- [`.claude-plugin/`](.claude-plugin/) and [`commands/`](commands/) — Claude Code plugin manifest, marketplace and slash commands.
- [`skills/doc-gardener/scripts/docgraph.py`](skills/doc-gardener/scripts/docgraph.py) — the deterministic tool (single file, stdlib only, Python 3.10+).

## Modes

| Mode | Purpose |
| --- | --- |
| `DISCOVER` | Route a task to the few pages/sections and code worth reading. |
| `BOOTSTRAP` | Set up or restructure the knowledge base together with the user. |
| `SYNC` | Route code changes to docs; verify claims both ways. |
| `AUDIT` | Mechanical health checks, then targeted semantic review. |
| `CONSOLIDATE` | Merge verified duplicates; preserve unique content. |

## Deterministic tool (no libraries, no LLM, no network)

```bash
python3 skills/doc-gardener/scripts/docgraph.py scan   --root /path/to/repo
python3 skills/doc-gardener/scripts/docgraph.py init   --root /path/to/repo [--write]
python3 skills/doc-gardener/scripts/docgraph.py route  --root /path/to/repo "how are refunds retried"
python3 skills/doc-gardener/scripts/docgraph.py check  --root /path/to/repo [--all] [--changed HEAD~1] [--json]
python3 skills/doc-gardener/scripts/docgraph.py graph  --root /path/to/repo [--page docs/x.md] [--format dot]
python3 skills/doc-gardener/scripts/docgraph.py impact --root /path/to/repo --base HEAD~1 --json
python3 skills/doc-gardener/scripts/docgraph.py move   --root /path/to/repo docs/a.md docs/guides/a.md [--apply]
python3 skills/doc-gardener/scripts/docgraph.py index  --root /path/to/repo --dir docs [--write | --check]
```

| Capability | Status |
| --- | --- |
| Broken local links, heading anchors (ATX/setext, GitHub slugs, `{#id}`, HTML ids), wiki-links incl. `#^block`, extensionless links | implemented, tested |
| Backlinks, orphans, reachability from entrypoints, graph export (json/dot) | implemented, tested |
| Exact duplicates, identical sections, near-duplicate pages, duplicate titles/ids | implemented, tested (near/section = triage) |
| Stale code references (`path/like.ext` mentions, links to code) | implemented, tested (advisory) |
| Change impact without config (docs referencing changed code) + optional mappings; incremental `check --changed` | implemented, tested |
| Task routing to pages and sections (`route`) | implemented, tested (lexical, no embeddings) |
| Repository inventory, draft config, open questions (`scan`, `init`) | implemented, tested |
| Safe moves with link rewriting and follow-up report (`move`) | implemented, tested |
| Semantic drift, whether a link *should* exist, which duplicate is canonical | agent judgment (procedure in SKILL.md) |

Detailed status against the original brief: [`docs/STATUS.md`](docs/STATUS.md). Tested on this suite and on three real repositories (agent-skill monorepo, backend service, ~900-page Obsidian-style notes vault; ~0.5–1.5 s per full `check --all`).

## Testing

```bash
python3 -m unittest discover -s tests -v
```

## Operational model

Doc Gardener does documentation discovery and maintenance. Implementation, planning and code review stay with your normal workflow (Superpowers, Agent Teams, etc. are optional, not dependencies).
