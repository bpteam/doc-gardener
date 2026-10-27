#!/usr/bin/env bash
# Stop hook: the agent may not finish while the open PR of its branch has no Codex review of its head
# (docs/review-loop.md). Approved, or needs-attention followed by "Answers to Codex review of <sha>" or "Loop stopped:"
# passes. No PR or no gh: passes; a gh or network error blocks. Blocks once (stop_hook_active), never loops.
# Register in .claude/settings.json: hooks.Stop[].hooks[] = {"type": "command",
#   "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/review-gate.sh", "timeout": 120}
set -uo pipefail

if [[ ! -t 0 ]]; then
  HOOK_INPUT="$(timeout 2 cat 2>/dev/null || true)"
  [[ "$(jq -r '.stop_hook_active // false' <<<"$HOOK_INPUT" 2>/dev/null)" == "true" ]] && exit 0
fi
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT" || exit 0
DEFAULT="$({ git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null || true; } | sed 's#^origin/##')"

fail() { # stage project command output_file
  {
    echo "REVIEW GATE: the Codex review loop has not finished on this PR. You may not finish yet."
    echo "This hook blocks once. If the loop cannot run, say so to the owner with this output."
    echo "Command: $3"
    echo "---"
    tail -n 40 "$4"
  } >&2
  exit 2
}

gate_review() { # the Codex review loop ran on the PR head (docs/review-loop.md)
  command -v gh >/dev/null || return 0
  local branch pr num head author tree out
  branch="$(git rev-parse --abbrev-ref HEAD)"
  [[ "$branch" == "${DEFAULT:-main}" || "$branch" == HEAD ]] && return 0
  out="$(mktemp)"
  # No PR yet is the only reason to skip; a gh or network error blocks (the review cannot be confirmed).
  if ! pr="$(gh pr view "$branch" --json number,state,headRefOid,author 2>"$out")"; then
    grep -qi 'no pull requests found' "$out" && { rm -f "$out"; return 0; }
    fail review . "gh pr view $branch" "$out"
  fi
  [[ "$(jq -r .state <<<"$pr")" == OPEN ]] || { rm -f "$out"; return 0; }
  num="$(jq -r .number <<<"$pr")" head="$(jq -r .headRefOid <<<"$pr")" author="$(jq -r .author.login <<<"$pr")"
  if [[ "$(git rev-parse HEAD)" != "$head" ]]; then
    echo "Local HEAD is not the head of PR #$num: push, then run /loop /pr-review-loop $num." >"$out"
    fail review . "git push && /loop /pr-review-loop $num" "$out"
  fi
  tree="$(git rev-parse "$head^{tree}")"
  # Newest review whose commit has the same tree as the PR head (a squash keeps the tree, not the sha).
  # Only the PR author's comments count: the loop posts from that account, and on a public repository anyone else
  # could post a fake review or answer. GitHub logins are [A-Za-z0-9-], safe to put in the jq string.
  local comments verdict sha c
  [[ "$author" =~ ^[A-Za-z0-9-]+$ ]] || { echo "Unexpected PR author login '$author'." >"$out"; fail review . "gh pr view $branch --json author" "$out"; }
  comments="$(gh api "repos/{owner}/{repo}/issues/$num/comments" --paginate \
    --jq ".[] | select(.user.login == \"$author\") | {id, body: .body}" 2>"$out")" || fail review . "gh api repos/{owner}/{repo}/issues/$num/comments" "$out"
  verdict="" sha="" at=-1
  local i=0
  while IFS= read -r c; do
    local h s
    h="$(jq -r '.body | split("\n")[0]' <<<"$c")"
    if [[ "$h" =~ ^"### Codex review (".*") of "([0-9a-f]{7,40})$ ]]; then
      s="${BASH_REMATCH[1]}"
      if [[ "$(git rev-parse -q --verify "$s^{tree}" 2>/dev/null)" == "$tree" ]]; then
        sha="$s" at=$i verdict="$(jq -r '.body' <<<"$c" | grep -oE '\*\*Verdict: [a-z-]+\*\*' | head -1)"
      fi
    fi
    i=$((i + 1))
  done < <(jq -c '.' <<<"$comments")
  if [[ -z "$sha" ]]; then
    echo "PR #$num head ${head:0:7} has no Codex review. Run the review loop before finishing (AGENTS.md hard rule)." >"$out"
    fail review . "/loop /pr-review-loop $num" "$out"
  fi
  [[ "$verdict" == "**Verdict: approve**" ]] && { rm -f "$out"; return 0; }
  # needs-attention: every finding answered (soft rule), or the loop stopped and told the owner. Only comments posted
  # after this review count: an answer or an escalation of an earlier round says nothing about this one. An answer
  # needs one "- " line per finding of the review ("- **P<n>**" lines) after its "Answers to Codex review of" line.
  if jq -s -e --argjson at "$at" --arg sha "$sha" '
      def lines: gsub("\r"; "") | split("\n");
      (.[$at].body | lines | map(select(test("^- \\*\\*P[0-2]\\*\\*"))) | length) as $n
      | any(.[$at + 1:][] | .body | lines;
          any(.[]; startswith("Loop stopped:"))
          or ((to_entries | map(select(.value | startswith("Answers to Codex review of \($sha)"))) | first | .key) as $k
              | $k != null and ((.[$k + 1:] | map(select(startswith("- "))) | length) >= $n)))' \
      <<<"$comments" >/dev/null; then
    rm -f "$out"; return 0
  fi
  echo "Codex review of $sha on PR #$num is needs-attention and no 'Answers to Codex review of $sha' comment answers each of its findings on its own '- ' line. Fix or answer every finding (docs/review-loop.md)." >"$out"
  fail review . "/loop /pr-review-loop $num" "$out"
}

gate_review
exit 0
