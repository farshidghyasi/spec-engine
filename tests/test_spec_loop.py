"""Behavioural checks for scripts/spec-loop.sh using a fake `claude` binary.

The fake claude completes one task per invocation through spec-state (like the real
/spec-exec would), or crashes, so the loop's accounting, stop conditions and rollback
can be verified without a model.
"""
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
CLI = PLUGIN / "scripts" / "spec-state.py"
LOOP = PLUGIN / "scripts" / "spec-loop.sh"

TASKS = """# Tasks: demo

### T-1: One
- **Status**: pending
- **Wave**: 0
- **Wired**: pending
- **Wire into**: n/a
- **Dependencies**: none
- **Covers**: US-1
- **Files**: a.txt
- **Description**: x
- **Acceptance Criteria**:
  1. ok
  2. err

### T-2: Two
- **Status**: pending
- **Wave**: 1
- **Wired**: pending
- **Wire into**: n/a
- **Dependencies**: T-1
- **Covers**: US-1
- **Files**: b.txt
- **Description**: x
- **Acceptance Criteria**:
  1. ok
  2. err
"""

FAKE_CLAUDE_OK = """#!/usr/bin/env bash
# completes the first pending task, commits it, prints a claude -p style JSON result
SS="python3 {cli}"
tid=$($SS summary demo | awk '/ pending /{{print $1; exit}}')
if [ -n "$tid" ]; then
  f=$($SS get demo tasks.$tid.files | python3 -c 'import json,sys;print(json.load(sys.stdin)[0])')
  echo "done $tid" > "$f"
  $SS set-task demo "$tid" --status completed >/dev/null
  git add "$f" .claude/specs >/dev/null 2>&1; git -c user.email=t@t -c user.name=t commit -qm "feat: $tid"
fi
echo '{{"type":"result","result":"did '"$tid"'","usage":{{"input_tokens":100,"output_tokens":50}},"is_error":false}}'
"""

FAKE_CLAUDE_CRASH = """#!/usr/bin/env bash
echo "half-done" > junk.txt; git add junk.txt; git -c user.email=t@t -c user.name=t commit -qm "partial"
exit 1
"""


class SpecLoopTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old = os.getcwd()
        os.chdir(self.root)
        subprocess.run(["git", "init", "-q"], check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init"], check=True)
        subprocess.run(["python3", str(CLI), "init", "demo"], check=True, capture_output=True)
        Path(".claude/specs/demo/tasks.md").write_text(TASKS)
        subprocess.run(["python3", str(CLI), "sync-tasks", "demo"], check=True, capture_output=True)
        subprocess.run(["python3", str(CLI), "phase", "demo", "validated"], check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "spec"], check=True)
        self.bin = self.root / "bin"
        self.bin.mkdir()

    def tearDown(self):
        os.chdir(self.old)
        self.tmp.cleanup()

    def fake_claude(self, body: str):
        p = self.bin / "claude"
        p.write_text(body.format(cli=CLI))
        p.chmod(p.stat().st_mode | stat.S_IEXEC)

    def run_loop(self, *args):
        env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}")
        return subprocess.run(["bash", str(LOOP), "--no-worktree", *args], capture_output=True, text=True, env=env)

    def state(self):
        return json.loads(Path(".claude/specs/demo/state.json").read_text())

    def test_loop_runs_until_complete_and_accounts_tokens(self):
        self.fake_claude(FAKE_CLAUDE_OK)
        r = self.run_loop("--max-iterations", "5")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("All tasks complete", r.stdout)
        st = self.state()
        self.assertEqual(st["execution"]["iteration"], 2)
        self.assertEqual(st["execution"]["total_tokens"], 300)
        self.assertFalse(Path(".claude/specs/demo/.executing").exists())
        self.assertFalse(Path(".claude/specs/demo/.lock").exists())
        self.assertIn("execution_ended", [e["event"] for e in st["audit_log"]])

    def test_max_iterations_stops_early(self):
        self.fake_claude(FAKE_CLAUDE_OK)
        r = self.run_loop("--max-iterations", "1")
        self.assertIn("Loop ended before completion", r.stdout)
        self.assertEqual(self.state()["tasks"]["T-2"]["status"], "pending")

    def test_crash_rolls_back_and_stops_after_two(self):
        self.fake_claude(FAKE_CLAUDE_CRASH)
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        r = self.run_loop("--max-iterations", "5")
        self.assertIn("2 consecutive crashes", r.stderr)
        self.assertEqual(subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(), head)
        self.assertFalse(Path("junk.txt").exists())
        self.assertEqual([e["event"] for e in self.state()["audit_log"]].count("iteration_failed"), 2)

    def test_budget_cap_stops_loop(self):
        self.fake_claude(FAKE_CLAUDE_OK)
        subprocess.run(["python3", str(CLI), "set", "demo", "execution.budget_cap", "100"], check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "cap"], check=True)
        r = self.run_loop("--max-iterations", "5")
        self.assertIn("budget cap reached", r.stdout)
        self.assertEqual(self.state()["tasks"]["T-2"]["status"], "pending")

    def test_refuses_dirty_tree_and_phase_gate(self):
        self.fake_claude(FAKE_CLAUDE_OK)
        Path("a.txt").write_text("x")
        subprocess.run(["git", "add", "a.txt"], check=True)
        r = self.run_loop()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("uncommitted changes", r.stderr)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "a"], check=True)
        subprocess.run(["python3", str(CLI), "phase", "demo", "spec"], check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "phase"], check=True)
        r = self.run_loop()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Phase gate", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
