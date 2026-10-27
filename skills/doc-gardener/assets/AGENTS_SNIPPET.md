# Optional project rule: Doc Gardener

Copy into the project's agent instructions (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules/…`). Replace `DOCGRAPH` with the path that works here: the installed skill's `scripts/docgraph.py`, or a vendored copy such as `tools/docgraph.py`.

```markdown
## Documentation (Doc Gardener)

- Before substantial work, find relevant docs with `python3 DOCGRAPH route --root . "<task>"` and read the listed sections, not the whole wiki.
- When behavior, APIs, configuration, interfaces or architectural rules change, run `python3 DOCGRAPH impact --root . --base HEAD --json` and update the canonical docs it routes to (or say why no update is needed). Never rewrite a documented invariant to match a bug; report the conflict.
- Before finishing, run `python3 DOCGRAPH check --root . --changed HEAD --code-refs` and fix reported errors. Do not invent links to silence orphan warnings.
- Before creating or moving docs: existing canonical page first, repository conventions first. Move/rename only via `python3 DOCGRAPH move …` (rewrites links) and only with approval.
- In parallel teams one agent owns edits to shared docs; others report needed changes to it.
```

Global installation alone does not make these rules active: they must be part of the agent's instructions (and optionally CI or hooks).
