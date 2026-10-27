"""Tests for the Codex review loop Stop hook (.claude/hooks/review-gate.sh), with a fake `gh` on PATH."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "review-gate.sh"

# `gh pr view` prints $FAKE_PR; `gh api ... --jq EXPR` runs EXPR over the JSON array in $FAKE_COMMENTS with jq.
FAKE_GH = """#!/usr/bin/env bash
case $1 in
  pr) cat "$FAKE_PR" ;;
  api) while [[ $# -gt 0 && $1 != --jq ]]; do shift; done; jq -c "$2" "$FAKE_COMMENTS" ;;
  *) exit 1 ;;
esac
"""


@unittest.skipUnless(shutil.which("jq") and shutil.which("bash"), "needs bash and jq")
class ReviewGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        repo = self.tmp / "repo"
        repo.mkdir()
        git = lambda *a: subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True, text=True).stdout
        git("init", "-q", "-b", "feature")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "x")
        self.repo, self.sha = repo, git("rev-parse", "HEAD").strip()
        bindir = self.tmp / "bin"
        bindir.mkdir()
        (bindir / "gh").write_text(FAKE_GH)
        (bindir / "gh").chmod(0o755)
        self.env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}",
                        FAKE_PR=str(self.tmp / "pr.json"), FAKE_COMMENTS=str(self.tmp / "comments.json"))
        (self.tmp / "pr.json").write_text(json.dumps(
            {"number": 7, "state": "OPEN", "headRefOid": self.sha, "author": {"login": "owner"}}))

    def gate(self, comments):
        (self.tmp / "comments.json").write_text(json.dumps(
            [{"id": i, "user": {"login": login}, "body": body} for i, (login, body) in enumerate(comments)]))
        return subprocess.run(["bash", str(HOOK)], cwd=self.repo, env=self.env, input='{"stop_hook_active":false}',
                              capture_output=True, text=True).returncode

    def review(self, verdict, findings=0):
        body = f"### Codex review (gpt-6-luna, high) of {self.sha[:7]}\n\n**Verdict: {verdict}**. x\n"
        return body + "".join(f"\n- **P1** `a.py:{i + 1}` bug {i}\n  fails\n  Fix: y" for i in range(findings))

    def answer(self, lines):
        return f"🤖 **Claude Code** (agent):\r\nAnswers to Codex review of {self.sha[:7]}:\r\n" + \
            "".join(f"- answer {i}\r\n" for i in range(lines))

    def test_no_review_blocks(self):
        self.assertEqual(self.gate([]), 2)

    def test_approve_passes(self):
        self.assertEqual(self.gate([("owner", self.review("approve"))]), 0)

    def test_answered_needs_attention_passes(self):
        self.assertEqual(self.gate([("owner", self.review("needs-attention", 2)), ("owner", self.answer(2))]), 0)

    def test_answer_without_a_line_per_finding_blocks(self):
        self.assertEqual(self.gate([("owner", self.review("needs-attention", 2)), ("owner", self.answer(0))]), 2)
        self.assertEqual(self.gate([("owner", self.review("needs-attention", 2)), ("owner", self.answer(1))]), 2)

    def test_answer_to_an_earlier_review_blocks(self):
        comments = [("owner", self.answer(1)), ("owner", self.review("needs-attention", 1))]
        self.assertEqual(self.gate(comments), 2)

    def test_loop_stopped_passes(self):
        stopped = "🤖 **Claude Code** (agent):\nLoop stopped: product decision"
        self.assertEqual(self.gate([("owner", self.review("needs-attention", 1)), ("owner", stopped)]), 0)

    def test_unanswered_needs_attention_blocks(self):
        self.assertEqual(self.gate([("owner", self.review("needs-attention", 1))]), 2)

    def test_answer_from_another_account_blocks(self):
        self.assertEqual(self.gate([("owner", self.review("needs-attention", 1)), ("stranger", self.answer(1))]), 2)
        self.assertEqual(self.gate([("owner", self.review("needs-attention", 1)), ("stranger", "Loop stopped: x")]), 2)

    def test_review_from_another_account_blocks(self):
        self.assertEqual(self.gate([("stranger", self.review("approve"))]), 2)


if __name__ == "__main__":
    unittest.main()
