# Review guidelines

What a reviewer of a pull request in this repository checks, Codex or any agent. The loop around the review:
[review-loop.md](review-loop.md).

## How to review

- Read the PR description first, then the diff, then the code and docs around it. The description is the author's
  claim: say when a claim (a check that ran, a behaviour that changed) is not supported by the diff.
- A finding names `file:line`, a concrete failure scenario (input or state, then the wrong result) and the fix.
  No failure scenario, no finding.
- Skip what tests and `docgraph.py check` already catch, and style. Nothing to report: say so, no filler nits.
- One strong finding beats several weak ones. A finding that rests on an inference says so and keeps its confidence
  honest.

## Priorities

- **P0**: data loss in the user's repository (a write mode that deletes or corrupts docs, `move --apply` losing
  content or links), secrets or private content leaking, a broken published plugin or skill install.
- **P1**: a hard rule below broken, a real bug in `docgraph.py`, a breaking change to a command, flag or JSON output
  without a note, a silent failure (an error reported as a warning, a check that passes on broken input).
- **P2**: a missing test for changed behaviour, stale docs, a bug on a rare path.

## Hard rules to check

Each rule is written in the linked place; the reviewer reads it there.

- The deterministic tool is one file, standard library only, Python 3.10+, no LLM and no network:
  [README: Deterministic tool](../README.md#deterministic-tool-no-libraries-no-llm-no-network),
  [SKILL.md frontmatter](../skills/doc-gardener/SKILL.md).
- Repository-agnostic: no assumed domain, layout, stack, renderer or metadata schema; repo conventions outrank the
  skill: [SKILL.md: invariants](../skills/doc-gardener/SKILL.md#always-follow-these-invariants) 1 and 3.
- Only `init --write`, `index --write` and `move --apply` write to the target repository; everything else is
  read-only: [SKILL.md: deterministic commands](../skills/doc-gardener/SKILL.md#deterministic-commands-no-llm-no-dependencies).
- Structural change to a user's docs needs the user's approval; moves are mechanical and in their own commit:
  [SKILL.md: invariants](../skills/doc-gardener/SKILL.md#always-follow-these-invariants) 7 and 8.
- A capability marked "implemented, tested" has tests in `tests/`, and the suite passes:
  [README: capabilities](../README.md#deterministic-tool-no-libraries-no-llm-no-network), [README: Testing](../README.md#testing).
- Docs follow the code: the README command table, the capability table and [STATUS.md](STATUS.md) match what the
  code and [`commands/`](../commands/) do; this repository's own docs pass `docgraph.py check`
  ([AGENTS.md](../AGENTS.md)).
- Nested agent instructions of touched projects (`AGENTS.md`, `CLAUDE.md`) apply to their subtree.
