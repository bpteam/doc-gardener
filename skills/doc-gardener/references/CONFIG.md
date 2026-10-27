# Target-repository configuration (optional)

The global skill never configures or writes to a repository on its own. Without config, the scanner reads **all Markdown** (`.md`, `.markdown`, `.mdx`) that git knows about — tracked plus untracked-but-not-ignored — and skips gitignored files, nested repositories/worktrees, and common vendor/build folders (`node_modules`, `vendor`, `dist`, `build`, `.venv`, …). Outside git it walks the tree with the same skips.

Generate a draft from the actual repository instead of writing one by hand:

```bash
python3 <skill-root>/scripts/docgraph.py init --root .          # preview
python3 <skill-root>/scripts/docgraph.py init --root . --write  # write .doc-gardener.json (never overwrites)
```

`--docs path` (repeatable) overrides `include` for a single run. Sample: [`assets/doc-gardener.example.json`](../assets/doc-gardener.example.json).

```json
{
  "include": ["README.md", "handbook", "modules/*/wiki"],
  "exclude": ["**/generated/**", ".agents/**"],
  "entrypoints": ["README.md", "handbook/INDEX.md"],
  "allow_orphans": ["handbook/archive/**"],
  "metadata_profile": "none",
  "mappings": [{"code": "modules/core/**", "docs": ["modules/core/wiki/**"]}],
  "code_ref_ignore": ["examples/**"]
}
```

- `include`: paths, directories or globs to scan. Omit to scan all Markdown.
- `exclude`: content to ignore (generated pages, test fixtures, agent skill libraries).
- `entrypoints`: navigation roots for reachability. Default: every `README`, `INDEX`, `SUMMARY`, `AGENTS`, `CLAUDE`, `CONTRIBUTING` page. Use the repo's real navigation.
- `allow_orphans`: intentionally standalone pages. `CHANGELOG`, `LICENSE`, `SECURITY`, `CODE_OF_CONDUCT`, … and `.github/**` are exempt by default.
- `mappings`: optional source-path → docs globs for `impact`. Usually unnecessary: `impact` already routes changes to docs that link to or mention the changed path. Use mappings for ownership that docs do not express by reference.
- `code_ref_ignore`: globs of `path/like.ext` mentions that are examples, not real paths (skipped by `check --code-refs`). Mentions starting with `path/to/` are always skipped.
- `metadata_profile`: `none` (default; no required frontmatter/relationship headings) or `doc-gardener` (optional convention for teams explicitly adopting `id`, `title`, `summary`, `kind`, `status`).
- `policy_exclude`: exempt files from the chosen metadata-profile checks (e.g. generated or historical content).

## What the parser understands

Inline links and images, reference definitions, `[[wiki links]]` (with `|label` and `#heading` / `#^block` anchors), extensionless page links (`[x](guide)` → `guide.md`), ATX and setext headings, GitHub-style slugs (snake_case kept), duplicate-heading suffixes, `{#custom-id}`, HTML `id`/`name` anchors, Obsidian block ids, frontmatter, fenced/inline code and HTML comments (ignored).

It is still a static approximation, not a full CommonMark/MkDocs/Docusaurus parser: no external URL checks, no renderer-specific routing (e.g. Docusaurus `slug`), no semantic inference. A missing connection is a **triage signal**, not proof of error. Use the repository's native documentation build too when available.
