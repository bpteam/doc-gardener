# Agent instructions

Doc Gardener is a skill package and Claude Code plugin; what it is and how it is laid out: [README.md](README.md).

Checks before every commit:

```bash
python3 -m unittest discover -s tests -v
```

```bash
python3 skills/doc-gardener/scripts/docgraph.py check --root . --all
```

## ⛔ HARD RULE: every PR goes through the Codex review loop; the owner only merges

After opening a PR, the author agent runs the review loop on it every time, without being asked: Claude Code with
`/loop /pr-review-loop <number>`, other agents by hand along [docs/review-loop.md](docs/review-loop.md). Each round:
review with the local Codex CLI, post the review, fix (with a test) or argue with a reason every finding, push, and
again, until the verdict is `approve` or every finding left is answered with a reason; at most 3 rounds. Then
`gh pr ready` and one notice to the owner listing the findings left open. The owner is not asked to look before
that, except when the loop stops on its own rules (a product decision, 3 rounds used up, the review script failing
twice). A Stop hook ([`.claude/hooks/review-gate.sh`](.claude/hooks/review-gate.sh)) keeps Claude Code from
finishing while the open PR of its branch has no review of its head.

## Review guidelines

Reviewing a pull request (Codex or any agent): read [docs/review-guidelines.md](docs/review-guidelines.md) first and
follow it.
