# Codex review loop

Every pull request goes through this loop; the owner only merges ([AGENTS.md](../AGENTS.md) hard rule). What the
reviewer checks: [review-guidelines.md](review-guidelines.md).

## Roles

- **Author agent** (Claude Code or another agent): writes the change, opens the PR, runs the loop, fixes or argues
  every finding, posts from the owner's GitHub account. Every comment it posts starts with
  `🤖 **Claude Code** (agent, posted from the owner's account):` (or the agent's own name).
- **Codex CLI**: the reviewer. The CLI shipped with the ChatGPT desktop app (`/usr/lib/chatgpt/resources/codex`,
  login in `~/.codex`), model `gpt-6-luna`, reasoning effort `high`, read-only sandbox. It is a tool of the owner's
  machine, like `gh`, not a dependency of the project.
- **Owner**: gets one notice when the PR is ready, and merges. Is asked earlier only when the loop stops.

## Steps

Claude Code runs one round per call of `/loop /pr-review-loop <number>`
([`.claude/skills/pr-review-loop/SKILL.md`](../.claude/skills/pr-review-loop/SKILL.md)); other agents follow the
same steps by hand.

1. Count the rounds: `### Codex review (` comments since the last `**Verdict: approve**` or the last
   `Owner decided: ...; round count restarts.` comment. Never a fourth round.
2. Review the pushed PR head: `.claude/skills/pr-review-loop/codex-review.sh <file>.md`. The script refuses a dirty
   tree or an unpushed head, reviews `origin/<default branch>...HEAD` with this file's guidelines and the PR
   description, and writes `<file>.md` (ready to post, headed `### Codex review (<model>, <effort>) of <sha>`) and
   `<file>.md.json` (verdict and findings, schema
   [`review-output.schema.json`](../.claude/skills/pr-review-loop/review-output.schema.json)). Its last line is
   `verdict: approve|needs-attention`; exit 3 names the failed step. It refuses to write a review that quotes a
   value of any `.env` file (tracked, untracked or ignored); tests:
   [`tests/test_codex_review.py`](../tests/test_codex_review.py). Env overrides: `CODEX_BIN`,
   `CODEX_REVIEW_MODEL`, `CODEX_REVIEW_EFFORT`, `CODEX_REVIEW_BASE`, `CODEX_REVIEW_TIMEOUT`.
3. Post the review as is: `gh pr comment <n> --body-file <file>.md`.
4. Answer every finding in one comment: line 1 the signature, line 2 `Answers to Codex review of <sha>:`, then one
   `- ` line per finding, in the review's order: fixed (with a test) or the reason it is not. Never change code only to silence a finding.
   Run the tests and checks from [AGENTS.md](../AGENTS.md), push, next round.
5. Stop by the table below.

## Stop table

| State | Then |
|---|---|
| `verdict: approve` on the last pushed commit, checks green | `gh pr ready`, push notification "PR #n ready to merge" |
| only findings the author disagrees with, each answered | same; the notice names them so the owner decides |
| 3 rounds since the last `approve` or owner's answer (never a 4th) with a finding unanswered, or a product decision | stop: comment `Loop stopped: <why>` with open findings and both positions, notify the owner |
| `codex-review.sh` fails twice | stop, notify the owner with its error |

Before merge, follow the repo's merge rules; if a squash changes the tree, run one more round on the new head.
After the owner answers an escalation in the PR, the author posts `Owner decided: <decision>; round count restarts.`
and the loop goes on from round 1.

## Stop hook

[`.claude/hooks/review-gate.sh`](../.claude/hooks/review-gate.sh), registered in
[`.claude/settings.json`](../.claude/settings.json), blocks Claude Code from finishing while the open PR of the
current branch has no Codex review of its head (matched by tree, so a squash keeps the review). It passes on
`approve`, or on `needs-attention` followed by a `Loop stopped:` comment or an `Answers to Codex review of <sha>` comment with at least as many
`- ` lines after that header as the review has findings (`- **P<n>**` lines); only
comments by the PR author (the owner's account the loop posts from) count, so another account cannot fake a review
or an answer; no PR passes; a `gh` error blocks. Tests: [`tests/test_review_gate.py`](../tests/test_review_gate.py). It blocks once per stop, never loops. It is a reminder, not a security boundary.

## Why the local CLI, not the Codex GitHub app

The GitHub app (`@codex review`) has no model choice and needs a Codex cloud environment of the repository. The
loop uses `codex exec` with an output schema instead (`codex review --base` refuses a custom prompt), so the verdict
and findings come as JSON, not free text. If the app reviews anyway, its comments are findings like any other.
PRs are opened from the owner's account, so GitHub refuses a review request to the owner: "ready" is `gh pr ready`
plus a notification.
