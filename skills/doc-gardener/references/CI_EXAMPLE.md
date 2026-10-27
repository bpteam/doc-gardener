# CI and maintenance integration (opt in per repository)

Global skills do not install anything into CI. To run checks in CI, vendor a reviewed copy of `scripts/docgraph.py` into the repository (e.g. `tools/docgraph.py`, note the source version in a comment) or install a pinned release. Do not curl and execute unpinned `main` code.

GitHub Actions example for a repository that vendored the script:

```yaml
name: docs
on: [pull_request]
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {fetch-depth: 0}
      - name: Broken links / anchors / wiki-links (blocking)
        run: python3 tools/docgraph.py check --root .
      - name: Findings related to this PR (advisory)
        run: python3 tools/docgraph.py check --root . --all --changed origin/${{ github.base_ref }} || true
      - name: Docs to review for this PR (advisory)
        run: python3 tools/docgraph.py impact --root . --base origin/${{ github.base_ref }} --json > docs-impact.json
```

Optional:

```bash
python3 tools/docgraph.py index --root . --dir docs --check   # fail if a managed index is stale / a manual index misses pages
python3 tools/docgraph.py check --root . --all --json > docs-health.json
```

Only structural errors should fail by default. Orphans, duplicates and stale code references stay advisory until the team has triaged them; then `--strict` may be enabled.

Semantic review (Doc Gardener `AUDIT`/`SYNC`) belongs to an explicitly approved scheduled task or PR review step; do not grant automated reviewers write/merge permissions without consent. On multi-agent teams run one integrated pass after merging, not one per agent.
