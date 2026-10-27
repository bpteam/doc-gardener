"""Tests for the secret scan of .claude/skills/pr-review-loop/codex-review.sh, with fake `codex` and `gh`."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "pr-review-loop" / "codex-review.sh"

# `codex exec ... -o <file> <prompt>` writes $FAKE_REVIEW to <file>; `gh pr view` finds no PR.
FAKE_CODEX = """#!/usr/bin/env bash
while [[ $# -gt 0 ]]; do [[ $1 == -o ]] && { cp "$FAKE_REVIEW" "$2"; shift; }; shift; done
"""
FAKE_GH = "#!/usr/bin/env bash\nexit 1\n"
SECRET = "sk-live-0123456789abcdef"


@unittest.skipUnless(shutil.which("jq") and shutil.which("bash"), "needs bash and jq")
class CodexReviewSecretScanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.repo = self.tmp / "repo"
        self.git("init", "-q", "--bare", "-b", "main", str(self.tmp / "origin.git"), cwd=self.tmp)
        self.git("clone", "-q", str(self.tmp / "origin.git"), str(self.repo), cwd=self.tmp)
        self.git("commit", "-q", "--allow-empty", "-m", "base")
        self.git("push", "-q", "origin", "main")
        self.git("remote", "set-head", "origin", "main")
        self.git("checkout", "-q", "-b", "feature")
        bindir = self.tmp / "bin"
        bindir.mkdir()
        for name, text in (("codex", FAKE_CODEX), ("gh", FAKE_GH)):
            (bindir / name).write_text(text)
            (bindir / name).chmod(0o755)
        self.env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}", CODEX_BIN=str(bindir / "codex"),
                        FAKE_REVIEW=str(self.tmp / "review.json"))
        self.out = self.tmp / "out" / "review.md"

    def git(self, *args, cwd=None):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd or self.repo,
                       check=True, capture_output=True)

    def commit(self, files):
        for name, text in files.items():
            (self.repo / name).write_text(text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "change")
        self.git("push", "-q", "origin", "feature")

    def run_review(self, failure_text):
        finding = {"priority": "P1", "title": "t", "file": "a.py", "line_start": 1, "line_end": 1,
                   "failure": failure_text, "recommendation": "r", "confidence": 0.9}
        (self.tmp / "review.json").write_text(json.dumps(
            {"verdict": "needs-attention", "summary": "s", "findings": [finding]}))
        return subprocess.run([str(SCRIPT), str(self.out)], cwd=self.repo, env=self.env,
                              capture_output=True, text=True)

    def test_clean_review_is_written(self):
        self.commit({".env": f"API_KEY={SECRET}\n"})
        result = self.run_review("nothing secret here")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("verdict: needs-attention", result.stdout)
        self.assertTrue(self.out.exists())

    def test_value_of_tracked_env_file_is_refused(self):
        self.commit({".env": f"API_KEY={SECRET}\n"})
        result = self.run_review(f"leaks {SECRET}")
        self.assertEqual(result.returncode, 3)
        self.assertIn(".env", result.stderr)
        self.assertFalse(self.out.exists())

    def test_value_of_ignored_env_file_is_refused(self):
        self.commit({".gitignore": ".env.local\n"})
        (self.repo / ".env.local").write_text(f'export API_KEY="{SECRET}" # local\n')
        result = self.run_review(f"leaks {SECRET}")
        self.assertEqual(result.returncode, 3)
        self.assertIn(".env.local", result.stderr)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
