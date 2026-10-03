"""End-to-end checks for scripts/spec-state.py against a throwaway git repo.

Run: python3 -m unittest discover -s tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
CLI = PLUGIN / "scripts" / "spec-state.py"

TASKS_MD = """# Tasks: demo

## Phase 1: Setup

### T-1: Shared types

- **Status**: pending
- **Wave**: 0
- **Wired**: pending
- **Wire into**: n/a
- **Dependencies**: none
- **Covers**: US-1
- **Files**: src/types.ts
- **Description**: types
- **Acceptance Criteria**:
  1. ok
  2. error path

### T-2: Service

- **Status**: pending
- **Wave**: 0
- **Wired**: pending
- **Wire into**: src/app.ts — import { greet } from './service'; call it
- **Dependencies**: T-1
- **Covers**: US-1
- **Files**: src/service.ts, src/app.ts, tests/service.test.ts
- **Description**: service
- **Acceptance Criteria**:
  1. ok
  2. error path

### T-3: Orphan util

- **Status**: pending
- **Wave**: 0
- **Wired**: pending
- **Dependencies**: T-1
- **Covers**: US-2
- **Files**: src/util.ts
- **Description**: util
- **Acceptance Criteria**:
  1. ok
  2. error path
"""


class SpecStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old = os.getcwd()
        os.chdir(self.root)
        subprocess.run(["git", "init", "-q"], check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init"], check=True)

    def tearDown(self):
        os.chdir(self.old)
        self.tmp.cleanup()

    def ss(self, *args, ok=True):
        r = subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True)
        if ok:
            self.assertEqual(r.returncode, 0, f"{args}\n{r.stdout}\n{r.stderr}")
        return r

    def state(self, name="demo"):
        return json.loads(Path(f".claude/specs/{name}/state.json").read_text())

    def make_spec(self):
        self.ss("init", "demo")
        Path(".claude/specs/demo/tasks.md").write_text(TASKS_MD)
        self.ss("sync-tasks", "demo")

    def test_init_fills_placeholders_and_rejects_bad_names(self):
        self.ss("init", "demo")
        st = self.state()
        self.assertEqual(st["spec_name"], "demo")
        self.assertNotIn("{{", json.dumps(st))
        self.assertTrue(Path(".claude/specs/demo/evidence/tests").is_dir())
        self.assertNotIn("{{", Path(".claude/specs/demo/tasks.md").read_text().splitlines()[2])
        r = self.ss("init", "Bad Name", ok=False)
        self.assertNotEqual(r.returncode, 0)

    def test_sync_tasks_computes_waves_and_fixes_wave_fields(self):
        self.make_spec()
        st = self.state()
        self.assertEqual(st["tasks"]["T-1"]["wave"], 0)
        self.assertEqual(st["tasks"]["T-2"]["wave"], 1)
        self.assertEqual(st["tasks"]["T-3"]["wave"], 1)
        self.assertEqual(st["tasks"]["T-1"]["wired"], "n/a")
        self.assertEqual([w["tasks"] for w in st["waves"]], [["T-1"], ["T-2", "T-3"]])
        self.assertEqual(st["execution"]["budget_cap"], 150000)
        self.assertIn("- **Wave**: 1", Path(".claude/specs/demo/tasks.md").read_text())
        self.ss("validate", "demo")

    def test_cycle_and_dangling_dependency_are_errors(self):
        self.ss("init", "demo")
        bad = TASKS_MD.replace("- **Dependencies**: none", "- **Dependencies**: T-2", 1)
        Path(".claude/specs/demo/tasks.md").write_text(bad)
        r = self.ss("sync-tasks", "demo", ok=False)
        self.assertIn("circular", r.stderr)
        Path(".claude/specs/demo/tasks.md").write_text(TASKS_MD.replace("- **Dependencies**: T-1", "- **Dependencies**: T-9", 1))
        r = self.ss("sync-tasks", "demo", ok=False)
        self.assertIn("unknown task", r.stderr)

    def test_batch_groups_by_file_overlap_and_advances_waves(self):
        self.make_spec()
        b = json.loads(self.ss("batch", "demo").stdout)
        self.assertEqual(b["wave"], 0)
        self.assertEqual(b["groups"], [["T-1"]])
        self.ss("set-task", "demo", "T-1", "--status", "completed")
        b = json.loads(self.ss("batch", "demo").stdout)
        self.assertEqual(b["wave"], 1)
        self.assertEqual(b["groups"], [["T-2", "T-3"]])
        self.ss("set", "demo", "parallel.shared_files", '["src/app.ts"]')
        b = json.loads(self.ss("batch", "demo").stdout)
        self.assertEqual(b["sequential"], ["T-2"])
        self.assertEqual(b["groups"], [["T-3"]])
        r = self.ss("complete", "demo", ok=False)
        self.assertEqual(r.returncode, 1)

    def test_set_task_updates_tasks_md_and_audit_log(self):
        self.make_spec()
        self.ss("set-task", "demo", "T-2", "--status", "completed", "--wired", "yes", "--fail")
        st = self.state()
        self.assertEqual(st["tasks"]["T-2"]["failures"], 1)
        md = Path(".claude/specs/demo/tasks.md").read_text()
        self.assertIn("- **Status**: completed", md)
        self.assertIn("- **Wired**: yes", md)
        self.assertEqual(st["audit_log"][-1]["event"], "task_updated")
        self.assertIn("timestamp", st["audit_log"][-1])

    def test_verify_wired_detects_usage_and_downgrades(self):
        self.make_spec()
        Path("src").mkdir()
        Path("tests").mkdir()
        Path("src/types.ts").write_text("export interface Greeting { text: string }\n")
        Path("src/service.ts").write_text("export function greet(): string { return 'hi' }\n")
        Path("src/app.ts").write_text("import { greet } from './service';\nconsole.log(greet());\n")
        Path("src/util.ts").write_text("export const unused = 1;\n")
        Path("tests/service.test.ts").write_text("import { unused } from '../src/util';\n")  # tests don't count
        for t in ("T-1", "T-2", "T-3"):
            self.ss("set-task", "demo", t, "--status", "completed")
        self.ss("set-task", "demo", "T-3", "--wired", "yes")  # agent self-report, must be downgraded
        self.ss("set", "demo", "execution.current_wave", "1")
        r = self.ss("verify-wired", "demo", "--apply", ok=False)
        self.assertEqual(r.returncode, 1)
        st = self.state()
        self.assertEqual(st["tasks"]["T-2"]["wired"], "yes")
        self.assertEqual(st["tasks"]["T-3"]["wired"], "pending")
        self.assertTrue(Path(".claude/specs/demo/evidence/wiring-wave-1.md").exists())
        self.assertIn("wired_downgraded", [e["event"] for e in st["audit_log"]])
        r = self.ss("complete", "demo", ok=False)
        self.assertIn("T-3", r.stdout)

    def test_check_files_and_manifest(self):
        self.make_spec()
        r = self.ss("check-files", "demo", "T-2", ok=False)
        self.assertIn("MISSING", r.stdout)
        Path("src").mkdir()
        Path("src/types.ts").write_text("export type Id = string;\nexport class Repo {}\n")
        self.ss("check-files", "demo", "T-1")
        self.ss("set-task", "demo", "T-1", "--status", "completed")
        out = self.ss("manifest", "demo").stdout
        self.assertIn("src/types.ts", out)
        self.assertIn("-> Id", out)
        self.assertIn("-> Repo", out)

    def test_integrity_phase_gate_and_deps(self):
        self.make_spec()
        self.ss("integrity", "demo", "--update")
        self.ss("integrity", "demo")
        Path(".claude/specs/demo/design.md").write_text("changed")
        r = self.ss("integrity", "demo", ok=False)
        self.assertIn("MISMATCH", r.stdout)
        r = self.ss("phase-gate", "demo", "validated", ok=False)
        self.assertIn("Phase gate", r.stdout)
        self.ss("phase", "demo", "validated")
        self.ss("phase-gate", "demo", "validated")
        self.ss("phase-gate", "demo", "spec")
        # cross-spec deps
        self.ss("init", "other")
        req = Path(".claude/specs/other/requirements.md")
        req.write_text(req.read_text() + "\n## Depends On\n\n- demo\n")
        r = self.ss("deps", "other", ok=False)
        self.assertIn("needs 'executed'", r.stdout)
        self.ss("phase", "demo", "executed")
        self.ss("deps", "other")

    def test_run_gates_diff_mode_and_secret_scan(self):
        self.make_spec()
        init = Path(".claude/specs/demo/init.sh")
        init.write_text(init.read_text() + '\ngates=("lint:echo error one; exit 1" "test:true")\n')
        self.assertEqual(self.ss("gates", "demo").stdout.strip().splitlines(), ["lint:echo error one; exit 1", "test:true"])
        self.ss("run-gates", "demo", "--baseline")
        self.assertEqual(self.state()["quality_gates"]["baseline_errors"]["lint"], 1)
        self.ss("run-gates", "demo", "--wave", "0")  # same error count as baseline -> pass
        self.assertTrue(Path(".claude/specs/demo/evidence/tests/wave-0-lint.txt").exists())
        init.write_text(init.read_text().replace("echo error one", "echo error one; echo error two"))
        r = self.ss("run-gates", "demo", "--wave", "0", ok=False)
        self.assertIn("GATES FAILED: lint", r.stdout)
        Path("leak.ts").write_text("const k = 'AKIAABCDEFGHIJKLMNOP';\n")
        r = self.ss("run-gates", "demo", "--wave", "0", "--only", "test", "--changed", "leak.ts", ok=False)
        self.assertIn("secret-scan", r.stdout)
        self.assertNotIn("AKIAABCDEFGHIJKLMNOP", Path(".claude/specs/demo/evidence/tests/wave-0-secrets.txt").read_text())

    def test_tokens_budget_and_exec_markers(self):
        self.make_spec()
        self.ss("set", "demo", "execution.budget_cap", "100")
        self.ss("tokens-add", "demo", "60", "--iteration")
        self.ss("budget-ok", "demo")
        self.ss("tokens-add", "demo", "60")
        r = self.ss("budget-ok", "demo", ok=False)
        self.assertIn("budget exceeded", r.stdout)
        self.assertEqual(self.state()["execution"]["iteration"], 1)
        self.ss("exec-start", "demo")
        self.assertTrue(Path(".claude/specs/demo/.executing").exists())
        self.ss("exec-end", "demo")
        self.assertFalse(Path(".claude/specs/demo/.executing").exists())

    def test_detect_gates_dashboard_status(self):
        self.make_spec()
        Path("package.json").write_text(json.dumps({"scripts": {"lint": "eslint .", "test": "jest"}}))
        Path("tsconfig.json").write_text("{}")
        out = self.ss("detect-gates", "demo").stdout
        self.assertIn("lint:npm run lint", out)
        self.assertIn("typecheck:npx tsc --noEmit", out)
        self.assertEqual(len(self.ss("gates", "demo").stdout.strip().splitlines()), 3)
        out = self.ss("dashboard").stdout
        self.assertIn("| demo |", out)
        out = self.ss("status", "demo").stdout
        self.assertIn("0/3", out)
        self.ss("hook", "demo", "wave_start", "0")  # no hook configured -> no-op

    def test_progress_and_log(self):
        self.make_spec()
        self.ss("progress", "demo", "Wave 0", "1 pending")
        self.assertIn("Wave 0", Path(".claude/specs/demo/progress.log").read_text())
        self.ss("log", "demo", "wave_started", "--wave", "0", "--details", "x")
        self.assertEqual(self.state()["audit_log"][-1]["wave"], 0)


if __name__ == "__main__":
    unittest.main()
