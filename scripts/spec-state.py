#!/usr/bin/env python3
"""spec-state: deterministic state operations for spec-engine.

Everything an orchestrating LLM used to do by hand (hashing, topological sort,
JSON edits, grep-based wiring checks, quality gates) lives here so it is done
the same way every time. Stdlib only; python3 >= 3.9.

Usage: spec-state.py <command> [spec] [options]   (run with -h for the list)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = Path(".claude/specs")
SPEC_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,62}[a-z0-9]?$")
TASK_HEAD_RE = re.compile(r"^###\s+(T-[A-Za-z0-9]+)\s*:\s*(.*)$")
FIELD_RE = re.compile(r"^-\s+\*\*([A-Za-z ]+)\*\*\s*:\s*(.*)$")
PHASES = ["spec", "validated", "executed", "accepted", "audited", "documented", "released", "verified", "retro"]
PHASE_ORDER = {"spec": 1, "validated": 2, "executed": 3, "accepted": 4, "audited": 4,
               "documented": 5, "released": 6, "verified": 7, "retro": 8}
SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rs", ".rb", ".java", ".kt", ".cs", ".vue", ".svelte"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", ".turbo", "vendor", "target", "coverage", ".claude", "__pycache__", ".venv", "venv"}
SECRET_PATTERNS = [
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github-token", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("openai-style-key", re.compile(r"\bsk-[A-Za-z0-9]{32,}")),
    ("slack-token", re.compile(r"xox[abp]-[A-Za-z0-9-]{10,}")),
]
SECRET_FILES = re.compile(r"(^|/)(\.env(\..*)?|.*\.(pem|key|p12|pfx))$")


# ---------------------------------------------------------------- helpers

def die(msg: str, code: int = 1) -> None:
    print(f"spec-state: {msg}", file=sys.stderr)
    sys.exit(code)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def git(*args: str, check: bool = False) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        die(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def list_specs() -> list[str]:
    if not SPECS_DIR.is_dir():
        return []
    return sorted(p.name for p in SPECS_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))


def resolve_spec(name: str | None) -> str:
    if name:
        if not SPEC_NAME_RE.match(name):
            die(f"invalid spec name '{name}'")
        if not (SPECS_DIR / name).is_dir():
            die(f"spec not found: {SPECS_DIR / name}")
        return name
    specs = list_specs()
    if len(specs) == 1:
        return specs[0]
    if not specs:
        die("no specs found in .claude/specs/ (run /spec <name> first)")
    die("multiple specs found, pass a name: " + ", ".join(specs))
    return ""  # unreachable


def spec_dir(name: str) -> Path:
    return SPECS_DIR / name


def load_state(name: str) -> dict:
    p = spec_dir(name) / "state.json"
    if not p.exists():
        die(f"missing {p}")
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        die(f"{p} is not valid JSON: {e}")
    return {}


def save_state(name: str, state: dict) -> None:
    p = spec_dir(name) / "state.json"
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n")
    tmp.replace(p)  # atomic on POSIX


def get_path(obj: dict, dotted: str):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def set_path(obj: dict, dotted: str, value) -> None:
    parts = dotted.split(".")
    cur = obj
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value


def append_log(state: dict, event: str, **fields) -> None:
    entry = {"timestamp": now(), "event": event}
    entry.update({k: v for k, v in fields.items() if v is not None})
    state.setdefault("audit_log", []).append(entry)


def plugin_version() -> str:
    try:
        return json.loads((PLUGIN_ROOT / ".claude-plugin/plugin.json").read_text())["version"]
    except Exception:
        return "unknown"


def split_list(value: str) -> list[str]:
    value = value.strip().strip("`")
    if not value or value.lower() in {"none", "n/a", "-"}:
        return []
    return [v.strip().strip("`") for v in re.split(r"[,\n]", value) if v.strip().strip("`")]


# ---------------------------------------------------------------- tasks.md

def parse_tasks_md(name: str) -> dict[str, dict]:
    """Parse tasks.md into {task_id: {title, fields..., line}}. Order preserved."""
    p = spec_dir(name) / "tasks.md"
    if not p.exists():
        die(f"missing {p}")
    tasks: dict[str, dict] = {}
    cur: dict | None = None
    for lineno, line in enumerate(p.read_text().splitlines(), 1):
        m = TASK_HEAD_RE.match(line)
        if m:
            tid = m.group(1)
            if tid in tasks:
                die(f"tasks.md: duplicate task id {tid} (line {lineno})")
            cur = {"id": tid, "title": m.group(2).strip(), "line": lineno, "fields": {}}
            tasks[tid] = cur
            continue
        if cur is None:
            continue
        if line.startswith("## "):
            cur = None
            continue
        f = FIELD_RE.match(line)
        if f:
            cur["fields"][f.group(1).strip().lower()] = f.group(2).strip()
    return tasks


def task_deps(t: dict) -> list[str]:
    return [d for d in split_list(t["fields"].get("dependencies", "")) if d.upper().startswith("T-")]


def task_files(t: dict) -> list[str]:
    return split_list(t["fields"].get("files", ""))


def compute_waves(tasks: dict[str, dict]) -> dict[str, int]:
    """Kahn's algorithm. Dies on dangling deps or cycles."""
    deps = {tid: task_deps(t) for tid, t in tasks.items()}
    for tid, ds in deps.items():
        for d in ds:
            if d not in tasks:
                die(f"{tid} depends on unknown task {d}")
    indeg = {tid: len(ds) for tid, ds in deps.items()}
    succ: dict[str, list[str]] = {tid: [] for tid in tasks}
    for tid, ds in deps.items():
        for d in ds:
            succ[d].append(tid)
    wave: dict[str, int] = {}
    frontier = [tid for tid, n in indeg.items() if n == 0]
    level = 0
    while frontier:
        nxt = []
        for tid in frontier:
            wave[tid] = level
            for s in succ[tid]:
                indeg[s] -= 1
                if indeg[s] == 0:
                    nxt.append(s)
        frontier = nxt
        level += 1
    if len(wave) != len(tasks):
        die("circular dependency among: " + ", ".join(sorted(set(tasks) - set(wave))))
    return wave


def rewrite_task_field(name: str, tid: str, field: str, value: str) -> None:
    """Update one `- **Field**: value` line inside a task block in tasks.md."""
    p = spec_dir(name) / "tasks.md"
    lines = p.read_text().splitlines(keepends=True)
    inside = False
    for i, line in enumerate(lines):
        m = TASK_HEAD_RE.match(line)
        if m:
            inside = m.group(1) == tid
            continue
        if inside and line.startswith("## "):
            break
        if inside:
            f = FIELD_RE.match(line.rstrip("\n"))
            if f and f.group(1).strip().lower() == field.lower():
                lines[i] = f"- **{f.group(1).strip()}**: {value}\n"
                break
    p.write_text("".join(lines))


# ---------------------------------------------------------------- commands

def cmd_init(a) -> None:
    name = a.spec
    if not SPEC_NAME_RE.match(name):
        die(f"invalid spec name '{name}'")
    d = spec_dir(name)
    if d.exists() and not a.force:
        die(f"{d} already exists (use --force to overwrite)")
    d.mkdir(parents=True, exist_ok=True)
    for sub in ("evidence/screenshots", "evidence/reviews", "evidence/tests", "handoffs"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    subs = {"{{SPEC_NAME}}": name, "{{ISO_TIMESTAMP}}": now(), "{{PLUGIN_VERSION}}": plugin_version(),
            "{{FEATURE_NAME}}": name}
    files = ["state.json", "init.sh"] + ([] if a.quick else ["requirements.md", "design.md", "tasks.md"])
    for f in files:
        text = (PLUGIN_ROOT / "templates" / f).read_text()
        for k, v in subs.items():
            text = text.replace(k, v)
        (d / f).write_text(text)
    os.chmod(d / "init.sh", 0o755)
    state = load_state(name)
    state["quick_mode"] = bool(a.quick)
    state["reproducibility"]["git_sha_start"] = git("rev-parse", "HEAD") or None
    append_log(state, "spec_initialized", quick=bool(a.quick))
    save_state(name, state)
    print(f"initialized {d}")


def cmd_get(a) -> None:
    v = get_path(load_state(resolve_spec(a.spec)), a.path)
    print(json.dumps(v) if not isinstance(v, str) else v)


def cmd_set(a) -> None:
    name = resolve_spec(a.spec)
    state = load_state(name)
    try:
        value = json.loads(a.value)
    except json.JSONDecodeError:
        value = a.value  # bare string
    set_path(state, a.path, value)
    save_state(name, state)


def cmd_log(a) -> None:
    name = resolve_spec(a.spec)
    state = load_state(name)
    append_log(state, a.event, task_id=a.task, wave=a.wave, details=a.details)
    save_state(name, state)


def cmd_progress(a) -> None:
    name = resolve_spec(a.spec)
    line = f"[{dt.datetime.now().strftime('%H:%M:%S')}] ▸ {a.event} │ {a.details}"
    print(line)
    with (spec_dir(name) / "progress.log").open("a") as fh:
        fh.write(line + "\n")


def cmd_phase(a) -> None:
    name = resolve_spec(a.spec)
    if a.new not in PHASE_ORDER:
        die(f"unknown phase '{a.new}' (one of {', '.join(PHASES)})")
    state = load_state(name)
    state["phase"] = a.new
    append_log(state, "phase_advanced", details=a.new)
    save_state(name, state)
    print(f"phase: {a.new}")


def cmd_phase_gate(a) -> None:
    name = resolve_spec(a.spec)
    state = load_state(name)
    cur = state.get("phase") or "spec"
    if PHASE_ORDER.get(cur, 0) < PHASE_ORDER[a.required]:
        print(f"Phase gate: requires phase '{a.required}', current phase is '{cur}'.")
        sys.exit(1)
    print(f"phase gate ok ({cur} >= {a.required})")


def cmd_integrity(a) -> None:
    name = resolve_spec(a.spec)
    state = load_state(name)
    d = spec_dir(name)
    current = {f"{f}_sha256": sha256(d / f"{f}.md") for f in ("requirements", "design", "tasks")}
    stored = state.setdefault("integrity", {})
    changed = [k for k, v in current.items() if stored.get(k) and stored.get(k) != v]
    if a.update:
        stored.update(current)
        stored["computed_at"] = now()
        if changed:
            append_log(state, "integrity_updated", details="changed: " + ", ".join(changed))
        save_state(name, state)
        print("integrity updated")
        return
    if changed:
        print("integrity MISMATCH: " + ", ".join(changed))
        sys.exit(1)
    print("integrity ok")


def cmd_drift(a) -> None:
    name = resolve_spec(a.spec)
    state = load_state(name)
    sha = get_path(state, "reproducibility.git_sha_start")
    files = get_path(state, "reproducibility.referenced_codebase_files") or []
    if not sha or not files:
        print("drift check skipped (no baseline sha or no referenced files)")
        return
    out = git("diff", "--name-only", f"{sha}..HEAD", "--", *files)
    if out:
        print("DRIFT: referenced files changed since spec was written:\n" + out)
        sys.exit(1)
    print("no drift")


def cmd_sync_tasks(a) -> None:
    """tasks.md is the source for structure; state.json keeps runtime fields."""
    name = resolve_spec(a.spec)
    state = load_state(name)
    tasks = parse_tasks_md(name)
    if not tasks:
        die("tasks.md has no '### T-x:' headings")
    waves = compute_waves(tasks)
    old = state.get("tasks") or {}
    new_tasks: dict[str, dict] = {}
    for tid, t in tasks.items():
        prev = old.get(tid, {})
        wired_decl = t["fields"].get("wired", "pending").lower()
        wire_into = t["fields"].get("wire into", "").strip().lower()
        default_wired = "n/a" if (wire_into == "n/a" or wired_decl == "n/a") else "pending"
        new_tasks[tid] = {
            "title": t["title"],
            "status": prev.get("status", "pending"),
            "wave": waves[tid],
            "wired": prev.get("wired", default_wired),
            "failures": prev.get("failures", 0),
            "files": task_files(t),
            "dependencies": task_deps(t),
        }
        if prev.get("decomposed"):
            new_tasks[tid]["decomposed"] = True
    max_wave = max(waves.values())
    state["tasks"] = new_tasks
    state["waves"] = [{"wave": w, "tasks": [tid for tid, tw in waves.items() if tw == w]} for w in range(max_wave + 1)]
    # keep tasks.md Wave fields honest
    for tid, w in waves.items():
        if tasks[tid]["fields"].get("wave", "").strip() != str(w):
            rewrite_task_field(name, tid, "Wave", str(w))
    # referenced codebase files (existing files only) for drift detection
    referenced = sorted({f for t in new_tasks.values() for f in t["files"] if Path(f).exists()})
    state.setdefault("reproducibility", {})["referenced_codebase_files"] = referenced
    if state.get("execution", {}).get("budget_cap") is None:
        state.setdefault("execution", {})["budget_cap"] = len(new_tasks) * 50000
    append_log(state, "tasks_synced", details=f"{len(new_tasks)} tasks, {max_wave + 1} waves")
    save_state(name, state)
    overlaps = same_wave_overlaps(new_tasks)
    print(f"synced {len(new_tasks)} tasks across {max_wave + 1} waves")
    for w, f, ids in overlaps:
        print(f"note: wave {w} tasks {', '.join(ids)} share file {f} (they will run sequentially)")


def same_wave_overlaps(tasks: dict[str, dict]) -> list[tuple[int, str, list[str]]]:
    seen: dict[tuple[int, str], list[str]] = {}
    for tid, t in tasks.items():
        for f in t.get("files", []):
            seen.setdefault((t["wave"], f), []).append(tid)
    return [(w, f, ids) for (w, f), ids in seen.items() if len(ids) > 1]


def cmd_validate(a) -> None:
    """Structural checks between tasks.md and state.json. Exit 1 on any error."""
    name = resolve_spec(a.spec)
    state = load_state(name)
    tasks = parse_tasks_md(name)
    errors: list[str] = []
    st_tasks = state.get("tasks") or {}
    for tid in tasks:
        if tid not in st_tasks:
            errors.append(f"{tid} in tasks.md but not in state.json (run sync-tasks)")
    for tid in st_tasks:
        if tid not in tasks:
            errors.append(f"{tid} in state.json but not in tasks.md (run sync-tasks)")
    waves = compute_waves(tasks)
    for tid, w in waves.items():
        if tid in st_tasks and st_tasks[tid].get("wave") != w:
            errors.append(f"{tid}: state.json wave {st_tasks[tid].get('wave')} != computed {w}")
        if tasks[tid]["fields"].get("wave", "").strip() not in ("", str(w)):
            errors.append(f"{tid}: tasks.md Wave {tasks[tid]['fields']['wave']} != computed {w}")
    for tid, t in tasks.items():
        for req in ("status", "wave", "dependencies", "covers", "files", "description", "acceptance criteria"):
            if req not in t["fields"]:
                errors.append(f"{tid}: missing field '{req}'")
        if not task_files(t):
            errors.append(f"{tid}: Files field is empty")
        wire = t["fields"].get("wire into", "").strip()
        if wire and wire.lower() != "n/a":
            target = wire.split("—")[0].split(" - ")[0].strip().strip("`")
            if target and target not in task_files(t):
                errors.append(f"{tid}: Wire into target '{target}' is not in its Files list")
    if errors:
        print("\n".join("ERROR: " + e for e in errors))
        sys.exit(1)
    print(f"structure ok: {len(tasks)} tasks, {max(waves.values()) + 1 if waves else 0} waves")


def cmd_deps(a) -> None:
    """Cross-spec dependencies from '## Depends On'. Dependency must be phase >= executed."""
    name = resolve_spec(a.spec)
    visiting: list[str] = []

    def parse(n: str) -> list[str]:
        p = spec_dir(n) / "requirements.md"
        if not p.exists():
            return []
        deps, inside = [], False
        for line in p.read_text().splitlines():
            if line.startswith("## "):
                inside = line.strip() == "## Depends On"
                continue
            if inside:
                m = re.match(r"^-\s+([a-z0-9][a-z0-9._-]*)\s*$", line.strip())
                if m:
                    deps.append(m.group(1))
        return deps

    def walk(n: str) -> list[str]:
        if n in visiting:
            die("circular spec dependency: " + " -> ".join(visiting + [n]))
        visiting.append(n)
        problems = []
        for d in parse(n):
            if not SPEC_NAME_RE.match(d):
                problems.append(f"invalid dependency name '{d}'")
                continue
            if not (spec_dir(d) / "state.json").exists():
                problems.append(f"dependency '{d}' not found")
                continue
            ph = load_state(d).get("phase") or "spec"
            if PHASE_ORDER.get(ph, 0) < PHASE_ORDER["executed"]:
                problems.append(f"dependency '{d}' is at phase '{ph}', needs 'executed'")
            problems += walk(d)
        visiting.pop()
        return problems

    problems = walk(name)
    if problems:
        print("\n".join("Dependency gate: " + p for p in problems))
        sys.exit(1)
    print("dependencies ok")


def current_wave_index(state: dict) -> int:
    return int(get_path(state, "execution.current_wave") or 0)


def cmd_batch(a) -> None:
    """Pending tasks of the current wave, partitioned into parallel groups by file ownership."""
    name = resolve_spec(a.spec)
    state = load_state(name)
    tasks = state.get("tasks") or {}
    if not tasks:
        die("no tasks in state.json (run sync-tasks)")
    terminal = {"completed", "skipped", "decomposed"}
    while True:
        w = current_wave_index(state)
        in_wave = {tid: t for tid, t in tasks.items() if t.get("wave") == w}
        max_wave = max(t.get("wave", 0) for t in tasks.values())
        if not in_wave and w > max_wave:
            print(json.dumps({"done": True}))
            return
        pending = {tid: t for tid, t in in_wave.items()
                   if t.get("status") not in terminal or (t["status"] == "completed" and t.get("wired") == "pending")}
        if pending:
            break
        state["execution"]["current_wave"] = w + 1
        save_state(name, state)
    shared = set(get_path(state, "parallel.shared_files") or [])
    max_par = 1 if a.no_parallel else int(get_path(state, "parallel.max_parallel_agents") or 3)
    sequential = [tid for tid, t in pending.items() if shared & set(t.get("files", [])) or t.get("failures", 0) >= 1]
    groups: list[list[str]] = []
    owned: list[set[str]] = []
    for tid, t in pending.items():
        if tid in sequential:
            continue
        files = set(t.get("files", []))
        placed = False
        for g, o in zip(groups, owned):
            if len(g) < max_par and not (o & files):
                g.append(tid)
                o |= files
                placed = True
                break
        if not placed:
            groups.append([tid])
            owned.append(set(files))
    print(json.dumps({"done": False, "wave": current_wave_index(state), "groups": groups,
                      "sequential": sequential, "max_parallel": max_par}, indent=2))


def cmd_set_task(a) -> None:
    name = resolve_spec(a.spec)
    state = load_state(name)
    t = (state.get("tasks") or {}).get(a.task)
    if t is None:
        die(f"unknown task {a.task}")
    if a.status:
        t["status"] = a.status
        rewrite_task_field(name, a.task, "Status", a.status)
    if a.wired:
        t["wired"] = a.wired
        rewrite_task_field(name, a.task, "Wired", a.wired)
    if a.fail:
        t["failures"] = t.get("failures", 0) + 1
    if a.tokens:
        t["tokens_used"] = t.get("tokens_used", 0) + a.tokens
    append_log(state, "task_updated", task_id=a.task, wave=t.get("wave"),
               details=f"status={t['status']} wired={t['wired']} failures={t.get('failures', 0)}")
    save_state(name, state)
    print(f"{a.task}: status={t['status']} wired={t['wired']} failures={t.get('failures', 0)}")


def cmd_check_files(a) -> None:
    name = resolve_spec(a.spec)
    state = load_state(name)
    t = (state.get("tasks") or {}).get(a.task)
    if t is None:
        die(f"unknown task {a.task}")
    missing = [f for f in t.get("files", []) if not Path(f).exists()]
    oversized = []
    for f in t.get("files", []):
        p = Path(f)
        if p.is_file():
            n = sum(1 for _ in p.open(errors="ignore"))
            if n > a.max_lines:
                oversized.append(f"{f} ({n} lines)")
    for o in oversized:
        print(f"OVERSIZED: {o} (limit {a.max_lines})")
    if missing:
        print("MISSING: " + ", ".join(missing))
        sys.exit(1)
    print(f"{a.task}: all {len(t.get('files', []))} declared files exist")


EXPORT_RES = {
    "js": [re.compile(r"export\s+(?:default\s+)?(?:async\s+)?(?:function\*?|class|const|let|var|interface|type|enum|abstract\s+class)\s+([A-Za-z_$][\w$]*)"),
           re.compile(r"export\s*\{([^}]+)\}")],
    "py": [re.compile(r"^(?:def|class)\s+([A-Za-z]\w*)", re.M)],
    "go": [re.compile(r"^func\s+(?:\([^)]*\)\s*)?([A-Z]\w*)", re.M), re.compile(r"^type\s+([A-Z]\w*)", re.M)],
    "rs": [re.compile(r"pub\s+(?:async\s+)?(?:fn|struct|enum|trait|type|const|static)\s+([A-Za-z_]\w*)")],
}


def extract_exports(path: Path) -> list[str]:
    ext = path.suffix
    kind = "js" if ext in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte"} else \
           "py" if ext == ".py" else "go" if ext == ".go" else "rs" if ext == ".rs" else None
    if kind is None or not path.is_file():
        return []
    text = path.read_text(errors="ignore")
    names: list[str] = []
    for rx in EXPORT_RES[kind]:
        for m in rx.finditer(text):
            g = m.group(1)
            if rx.pattern.startswith("export\\s*\\{"):
                for part in g.split(","):
                    nm = part.strip().split(" as ")[-1].strip()
                    if nm and nm != "default":
                        names.append(nm)
            else:
                names.append(g)
    return sorted({n for n in names if n and not n.startswith("_")})


def is_test_path(p: Path) -> bool:
    s = str(p)
    return bool(re.search(r"(^|/)(tests?|__tests__|spec)(/|$)|\.(test|spec)\.[a-z]+$|_test\.(py|go)$|^test_.*\.py$", s))


def source_files(root: Path = Path(".")) -> list[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix in SOURCE_EXT:
                out.append(p)
    return out


def cmd_verify_wired(a) -> None:
    """Grep the codebase for usage of the task's exports outside its own files and tests."""
    name = resolve_spec(a.spec)
    state = load_state(name)
    tasks = state.get("tasks") or {}
    if a.task:
        ids = [a.task]
    elif a.all:
        ids = [tid for tid, t in tasks.items() if t.get("status") == "completed"]
    else:
        ids = [tid for tid, t in tasks.items() if t.get("wave") == current_wave_index(state)]
    label = "all" if a.all else str(current_wave_index(state))
    report = [f"# Wiring Evidence: wave {label} ({now()})", ""]
    failed = []
    all_sources = source_files()
    for tid in ids:
        t = tasks.get(tid)
        if t is None:
            die(f"unknown task {tid}")
        if t.get("wired") == "n/a":
            report.append(f"## {tid}: wired=n/a (declared, skipped)")
            continue
        exports: dict[str, list[str]] = {}
        for f in t.get("files", []):
            p = Path(f)
            if p.is_file() and not is_test_path(p):
                ex = extract_exports(p)
                if ex:
                    exports[f] = ex
        hits: dict[str, list[str]] = {}
        # ponytail: usage anywhere outside the defining file (and tests) counts, including the
        # task's own "Wire into" file; reachability from the app entry point is the reviewer's job.
        for f, names in exports.items():
            defining = Path(f).resolve()
            for nm in names:
                rx = re.compile(r"\b" + re.escape(nm) + r"\b")
                for sp in all_sources:
                    if sp.resolve() == defining or is_test_path(sp):
                        continue
                    try:
                        for i, line in enumerate(sp.open(errors="ignore"), 1):
                            if rx.search(line):
                                hits.setdefault(nm, []).append(f"{sp}:{i}")
                                break
                    except OSError:
                        pass
        wired = bool(hits)
        report.append(f"## {tid}: {'PASS' if wired else 'FAIL'}")
        report.append(f"- exports: {json.dumps(exports)}")
        report.append(f"- usages outside task/tests: {json.dumps(hits)}")
        report.append("")
        if not exports:
            report.append("- note: no exports detected in declared files; mark wired=n/a if this is config/infra")
        if a.apply:
            new = "yes" if wired else "pending"
            if t.get("wired") != new:
                t["wired"] = new
                rewrite_task_field(name, tid, "Wired", new)
                append_log(state, "wired_verified" if wired else "wired_downgraded", task_id=tid,
                           details=f"{len(hits)} exports used" if wired else "0 usages found")
        if not wired:
            failed.append(tid)
    evid = spec_dir(name) / "evidence" / f"wiring-wave-{label}.md"
    evid.parent.mkdir(parents=True, exist_ok=True)
    evid.write_text("\n".join(report) + "\n")
    if a.apply:
        save_state(name, state)
    print("\n".join(report))
    if failed:
        print(f"WIRING FAIL: {', '.join(failed)}")
        sys.exit(1)


def cmd_manifest(a) -> None:
    """Import manifest: exports from files of completed tasks (for agent prompts)."""
    name = resolve_spec(a.spec)
    state = load_state(name)
    seen = set()
    print("== Import Manifest (from completed tasks) ==")
    for tid, t in (state.get("tasks") or {}).items():
        if t.get("status") != "completed":
            continue
        for f in t.get("files", []):
            if f in seen:
                continue
            seen.add(f)
            p = Path(f)
            if p.is_file() and not is_test_path(p):
                ex = extract_exports(p)
                if ex:
                    print(f"{f}  ({tid})")
                    for nm in ex:
                        print(f"  -> {nm}")


def cmd_summary(a) -> None:
    name = resolve_spec(a.spec)
    state = load_state(name)
    tasks = state.get("tasks") or {}
    done = [t for t in tasks.values() if t["status"] == "completed"]
    print(f"spec={name} phase={state.get('phase')} wave={current_wave_index(state)} "
          f"tasks={len(done)}/{len(tasks)} completed")
    for tid, t in tasks.items():
        print(f"  {tid} w{t['wave']} {t['status']} wired={t['wired']} fails={t.get('failures', 0)} files={','.join(t.get('files', []))}")


def cmd_complete(a) -> None:
    state = load_state(resolve_spec(a.spec))
    tasks = state.get("tasks") or {}
    open_ = [tid for tid, t in tasks.items()
             if t.get("status") not in {"completed", "skipped", "decomposed"}
             or (t.get("status") == "completed" and t.get("wired") not in {"yes", "n/a"})]
    if open_ or not tasks:
        print("incomplete: " + (", ".join(open_) if open_ else "no tasks"))
        sys.exit(1)
    print("complete")


def gates_from_init(name: str) -> list[tuple[str, str]]:
    init = spec_dir(name) / "init.sh"
    if not init.exists():
        return []
    script = f"""set -a; source {json.dumps(str(init))} >/dev/null 2>&1 || true
if [ -n "${{gates+x}}" ]; then for g in "${{gates[@]}}"; do printf '%s\\n' "$g"; done
else
  [ -n "${{lint_cmd:-}}" ] && echo "lint:$lint_cmd"
  [ -n "${{typecheck_cmd:-}}" ] && echo "typecheck:$typecheck_cmd"
  [ -n "${{test_cmd:-}}" ] && echo "test:$test_cmd"
  [ -n "${{integration_cmd:-}}" ] && echo "integration:$integration_cmd"
fi; true"""
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    out = []
    for line in r.stdout.splitlines():
        if ":" in line:
            n, c = line.split(":", 1)
            out.append((n.strip(), c.strip()))
    return out


def init_var(name: str, var: str) -> str:
    init = spec_dir(name) / "init.sh"
    if not init.exists():
        return ""
    r = subprocess.run(["bash", "-c", f"source {json.dumps(str(init))} >/dev/null 2>&1; printf '%s' \"${{{var}:-}}\""],
                       capture_output=True, text=True)
    return r.stdout.strip()


def cmd_gates(a) -> None:
    for n, c in gates_from_init(resolve_spec(a.spec)):
        print(f"{n}:{c}")


def detect_gates() -> list[str]:
    g: list[str] = []
    if Path("package.json").exists():
        scripts = json.loads(Path("package.json").read_text()).get("scripts", {})
        if "lint" in scripts:
            g.append("lint:npm run lint")
        if "typecheck" in scripts:
            g.append("typecheck:npm run typecheck")
        elif Path("tsconfig.json").exists():
            g.append("typecheck:npx tsc --noEmit")
        if "test" in scripts:
            g.append("test:npm test")
    elif Path("pyproject.toml").exists() or Path("setup.py").exists():
        txt = Path("pyproject.toml").read_text() if Path("pyproject.toml").exists() else ""
        g.append("lint:ruff check ." if "ruff" in txt or shutil.which("ruff") else "lint:python -m pyflakes .")
        if "mypy" in txt:
            g.append("typecheck:mypy .")
        g.append("test:pytest" if "pytest" in txt or shutil.which("pytest") else "test:python -m unittest")
    elif Path("Cargo.toml").exists():
        g += ["lint:cargo clippy -- -D warnings", "typecheck:cargo check", "test:cargo test"]
    elif Path("go.mod").exists():
        if shutil.which("golangci-lint"):
            g.append("lint:golangci-lint run")
        g += ["typecheck:go vet ./...", "test:go test ./..."]
    elif Path("Makefile").exists():
        mk = Path("Makefile").read_text()
        for tgt in ("lint", "test"):
            if re.search(rf"^{tgt}:", mk, re.M):
                g.append(f"{tgt}:make {tgt}")
    return g


def cmd_detect_gates(a) -> None:
    name = resolve_spec(a.spec)
    existing = gates_from_init(name)
    if existing and not a.force:
        print("gates already configured: " + ", ".join(n for n, _ in existing))
        return
    g = detect_gates()
    if not g:
        print("no quality gates detected; edit init.sh to add gates=(...)")
        return
    init = spec_dir(name) / "init.sh"
    arr = " ".join(json.dumps(x) for x in g)
    init.write_text(init.read_text().rstrip("\n") + f"\n\n# auto-detected by spec-state\ngates=({arr})\n")
    print("configured gates: " + ", ".join(g))


def count_errors(output: str) -> int:
    return sum(1 for line in output.splitlines() if re.search(r"\berror\b|\bFAIL(ED|ING)?\b|✗", line, re.I))


def cmd_run_gates(a) -> None:
    """Run gates from init.sh in diff mode. Writes evidence/tests/wave-N-<gate>.txt."""
    name = resolve_spec(a.spec)
    state = load_state(name)
    gates = gates_from_init(name)
    qg = state.setdefault("quality_gates", {})
    qg["gates"] = [f"{n}:{c}" for n, c in gates]
    baseline = qg.setdefault("baseline_errors", {}) or {}
    evid = spec_dir(name) / "evidence" / "tests"
    evid.mkdir(parents=True, exist_ok=True)
    label = "baseline" if a.baseline else f"wave-{a.wave if a.wave is not None else current_wave_index(state)}"
    failures: list[str] = []
    if not gates:
        print("no gates configured (init.sh); skipping")
        append_log(state, "gates_skipped", details="no gates configured")
    for n, c in gates:
        if a.only and n not in a.only:
            continue
        if n == "integration" and not a.integration:
            continue
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=a.timeout)
        out = (r.stdout or "") + (r.stderr or "")
        (evid / f"{label}-{n}.txt").write_text(f"$ {c}\nexit={r.returncode}\n\n{out}")
        errs = count_errors(out) if r.returncode != 0 else 0
        if a.baseline:
            baseline[n] = errs
            print(f"{n}: baseline {errs} errors (exit {r.returncode})")
            continue
        base = baseline.get(n)
        ok = r.returncode == 0 or (base is not None and errs <= base)
        print(f"{n}: {'PASS' if ok else 'FAIL'} (exit {r.returncode}, errors {errs}, baseline {base})")
        append_log(state, "gate_passed" if ok else "gate_failed", wave=a.wave, details=f"{n}: {errs} errors (baseline {base})")
        if not ok:
            failures.append(n)
    # built-in secret scan on changed files
    changed = a.changed or []
    found = []
    for f in changed:
        p = Path(f)
        if SECRET_FILES.search(f):
            found.append(f"{f}: sensitive filename")
            continue
        if p.is_file() and p.stat().st_size < 2_000_000:
            for i, line in enumerate(p.open(errors="ignore"), 1):
                for pname, rx in SECRET_PATTERNS:
                    if rx.search(line):
                        found.append(f"{f}:{i}: {pname}")
    if found:
        (evid / f"{label}-secrets.txt").write_text("\n".join(found) + "\n")
        print("secret-scan: FAIL\n  " + "\n  ".join(found))
        append_log(state, "gate_failed", wave=a.wave, details="secret-scan: " + "; ".join(found))
        failures.append("secret-scan")
    elif changed:
        print(f"secret-scan: PASS ({len(changed)} files)")
    qg["baseline_errors"] = baseline
    if not failures and not a.baseline and gates:
        qg["last_regression_pass"] = now()
    save_state(name, state)
    if failures:
        print("GATES FAILED: " + ", ".join(failures))
        sys.exit(1)


def cmd_hook(a) -> None:
    name = resolve_spec(a.spec)
    cmd = init_var(name, f"hook_on_{a.event}")
    if not cmd:
        return
    try:
        r = subprocess.run(["bash", "-c", cmd + ' "$@"', "spec-hook", name, *a.args],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            print(f"[hook:{a.event}] exit {r.returncode}: {r.stderr.strip()[:300]}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"[hook:{a.event}] timed out after 30s", file=sys.stderr)


def cmd_tokens_add(a) -> None:
    name = resolve_spec(a.spec)
    state = load_state(name)
    ex = state.setdefault("execution", {})
    ex["total_tokens"] = int(ex.get("total_tokens") or 0) + a.n
    ex["iteration"] = int(ex.get("iteration") or 0) + (1 if a.iteration else 0)
    ex["last_iteration_at"] = now()
    ex.setdefault("started_at", ex["last_iteration_at"])
    save_state(name, state)
    print(f"total_tokens={ex['total_tokens']}")


def cmd_budget_ok(a) -> None:
    state = load_state(resolve_spec(a.spec))
    cap = get_path(state, "execution.budget_cap")
    used = int(get_path(state, "execution.total_tokens") or 0)
    if cap and used >= int(cap):
        print(f"budget exceeded: {used} >= {cap}")
        sys.exit(1)
    print(f"budget ok: {used}/{cap if cap else 'unlimited'}")


def cmd_open_batch(a) -> None:
    """Tasks in execution.current_batch that are not finalized. Exit 1 if any (used by the Stop hook)."""
    state = load_state(resolve_spec(a.spec))
    tasks = state.get("tasks") or {}
    open_ = []
    for tid in get_path(state, "execution.current_batch") or []:
        t = tasks.get(tid, {})
        if t.get("status") == "in_progress" or (t.get("status") == "completed" and t.get("wired") == "pending"):
            open_.append(f"{tid}({t.get('status')},wired={t.get('wired')})")
    print(", ".join(open_))
    sys.exit(1 if open_ else 0)


def cmd_exec_start(a) -> None:
    name = resolve_spec(a.spec)
    (spec_dir(name) / ".executing").write_text(f"{os.getpid()} {now()}\n")
    state = load_state(name)
    state.setdefault("execution", {}).setdefault("started_at", now())
    append_log(state, "execution_started")
    save_state(name, state)


def cmd_exec_end(a) -> None:
    name = resolve_spec(a.spec)
    marker = spec_dir(name) / ".executing"
    if marker.exists():
        marker.unlink()
    state = load_state(name)
    state.setdefault("execution", {})["current_batch"] = []
    append_log(state, "execution_ended")
    save_state(name, state)


def spec_row(name: str) -> dict:
    d = spec_dir(name)
    st = json.loads((d / "state.json").read_text()) if (d / "state.json").exists() else {}
    tasks = st.get("tasks") or {}
    done = sum(1 for t in tasks.values() if t.get("status") == "completed")
    sec = get_path(st, "security.posture_score")
    return {
        "spec": name,
        "phase": st.get("phase") or ("quick" if st.get("quick_mode") else "spec"),
        "req": (d / "requirements.md").exists() and "### US-" in (d / "requirements.md").read_text(),
        "design": (d / "design.md").exists() and re.search(r"^## (Components|Architecture)", (d / "design.md").read_text(), re.M) is not None,
        "tasks": bool(tasks),
        "valid": get_path(st, "validation.status") == "pass",
        "sec": sec,
        "exec": f"{done}/{len(tasks)}" if tasks else "—",
        "accepted": get_path(st, "acceptance.status") == "accepted",
        "docs": any((d / "docs").glob("*")) if (d / "docs").exists() else False,
        "released": (d / "release.md").exists() and (d / "release.md").read_text().strip() != "",
        "retro": (d / "retro.md").exists(),
    }


def cmd_dashboard(a) -> None:
    specs = list_specs()
    if not specs:
        print("No specs found in .claude/specs/. Run /spec <name> to create one.")
        return
    rows = [spec_row(s) for s in specs]
    rows.sort(key=lambda r: (-PHASE_ORDER.get(r["phase"], 0), r["spec"]))
    y, n = "✅", "❌"
    print("| Spec | Phase | Req | Design | Tasks | Valid | Sec | Exec | Accepted | Docs | Rel | Retro |")
    print("|------|-------|-----|--------|-------|-------|-----|------|----------|------|-----|-------|")
    for r in rows:
        sec = f"{y} {r['sec']}" if r["sec"] is not None else n
        print(f"| {r['spec']} | {r['phase']} | {y if r['req'] else n} | {y if r['design'] else n} | {y if r['tasks'] else n} | "
              f"{y if r['valid'] else n} | {sec} | {r['exec']} | {y if r['accepted'] else n} | {y if r['docs'] else n} | "
              f"{y if r['released'] else n} | {y if r['retro'] else n} |")
    print(f"\n{len(rows)} specs")


def cmd_status(a) -> None:
    name = resolve_spec(a.spec)
    state = load_state(name)
    tasks = state.get("tasks") or {}
    total = len(tasks)
    done = [tid for tid, t in tasks.items() if t.get("status") == "completed"]
    pct = int(100 * len(done) / total) if total else 0
    bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
    print(f"== Spec Status: {name} ==\n")
    print(f"Phase: {state.get('phase') or 'spec'}   Progress: [{bar}] {len(done)}/{total} ({pct}%)\n")
    wired = sum(1 for t in tasks.values() if t.get("status") == "completed" and t.get("wired") in {"yes", "n/a"})
    print(f"Wired: {wired} of {len(done)} completed tasks   Current wave: {current_wave_index(state)}")
    waves = state.get("waves") or []
    for w in waves:
        ids = w.get("tasks", [])
        c = sum(1 for tid in ids if tasks.get(tid, {}).get("status") == "completed")
        print(f"  Wave {w['wave']}: {c}/{len(ids)}  {' '.join(ids)}")
    ex = state.get("execution", {})
    print(f"\nTokens: {ex.get('total_tokens', 0)} / cap {ex.get('budget_cap') or 'none'}   Iterations: {ex.get('iteration', 0)}")
    gates = gates_from_init(name)
    print("Gates: " + (", ".join(f"{n} ({c})" for n, c in gates) if gates else "not configured (edit init.sh)"))
    sec = state.get("security") or {}
    print(f"Security: posture={sec.get('posture_score', 'not audited')} threat_model={sec.get('threat_model_status', 'pending')} "
          f"findings={sec.get('findings', {})}")
    stuck = [f"{tid} ({t.get('failures')} failures)" for tid, t in tasks.items() if t.get('failures', 0) >= 2]
    if stuck:
        print("Attention: " + ", ".join(stuck))
    val = state.get("validation") or {}
    print(f"Validation: {val.get('status', 'never run')}   Acceptance: {get_path(state, 'acceptance.status') or 'none'}")


def cmd_list(a) -> None:
    for s in list_specs():
        print(s)


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="spec-state", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(cmd_name, fn, spec=True, help=""):
        p = sub.add_parser(cmd_name, help=help)
        if spec:
            p.add_argument("spec", nargs="?", help="spec name (auto-detected if only one)")
        p.set_defaults(fn=fn)
        return p

    p = add("init", cmd_init, spec=False, help="create spec dir from templates"); p.add_argument("spec"); p.add_argument("--quick", action="store_true"); p.add_argument("--force", action="store_true")
    p = add("get", cmd_get, help="read a dotted path from state.json"); p.add_argument("path")
    p = add("set", cmd_set, help="write a dotted path in state.json (value parsed as JSON, else string)"); p.add_argument("path"); p.add_argument("value")
    p = add("log", cmd_log, help="append an audit_log entry"); p.add_argument("event"); p.add_argument("--task"); p.add_argument("--wave", type=int); p.add_argument("--details")
    p = add("progress", cmd_progress, help="print + append a progress.log line"); p.add_argument("event"); p.add_argument("details", nargs="?", default="")
    p = add("phase", cmd_phase, help="set lifecycle phase"); p.add_argument("new")
    p = add("phase-gate", cmd_phase_gate, help="exit 1 unless phase >= required"); p.add_argument("required", choices=PHASES)
    p = add("integrity", cmd_integrity, help="check (or --update) SHA256 manifest of spec files"); p.add_argument("--update", action="store_true")
    add("drift", cmd_drift, help="exit 1 if referenced codebase files changed since git_sha_start")
    add("sync-tasks", cmd_sync_tasks, help="parse tasks.md -> state.json tasks/waves (Kahn)")
    add("validate", cmd_validate, help="structural checks between tasks.md and state.json")
    add("deps", cmd_deps, help="cross-spec dependency gate (## Depends On)")
    p = add("batch", cmd_batch, help="pending tasks of current wave as parallel groups (JSON)"); p.add_argument("--no-parallel", action="store_true")
    p = add("set-task", cmd_set_task, help="update task status/wired/failures"); p.add_argument("task"); p.add_argument("--status"); p.add_argument("--wired", choices=["yes", "pending", "n/a"]); p.add_argument("--fail", action="store_true"); p.add_argument("--tokens", type=int)
    p = add("check-files", cmd_check_files, help="verify declared files exist; warn on oversized"); p.add_argument("task"); p.add_argument("--max-lines", type=int, default=500)
    p = add("verify-wired", cmd_verify_wired, help="grep for usages of task exports; --apply updates wired"); p.add_argument("task", nargs="?"); p.add_argument("--apply", action="store_true"); p.add_argument("--all", action="store_true", help="all completed tasks, not just the current wave")
    add("manifest", cmd_manifest, help="import manifest of exports from completed tasks")
    add("summary", cmd_summary, help="compact state summary for agent prompts")
    add("complete", cmd_complete, help="exit 0 if all tasks completed and wired")
    add("gates", cmd_gates, help="list gates from init.sh")
    p = add("detect-gates", cmd_detect_gates, help="auto-detect gates and write to init.sh"); p.add_argument("--force", action="store_true")
    p = add("run-gates", cmd_run_gates, help="run gates in diff mode, persist evidence"); p.add_argument("--wave", type=int); p.add_argument("--baseline", action="store_true"); p.add_argument("--only", nargs="*"); p.add_argument("--integration", action="store_true"); p.add_argument("--changed", nargs="*"); p.add_argument("--timeout", type=int, default=900)
    p = add("hook", cmd_hook, help="run hook_on_<event> from init.sh (30s timeout)"); p.add_argument("event", choices=["wave_start", "task_complete", "spec_complete"]); p.add_argument("args", nargs="*")
    p = add("tokens-add", cmd_tokens_add, help="add tokens to execution.total_tokens"); p.add_argument("n", type=int); p.add_argument("--iteration", action="store_true")
    add("budget-ok", cmd_budget_ok, help="exit 1 if total_tokens >= budget_cap")
    add("open-batch", cmd_open_batch, help="exit 1 if current_batch has unfinished tasks")
    add("exec-start", cmd_exec_start, help="mark spec as executing (enables hook gates)")
    add("exec-end", cmd_exec_end, help="clear executing marker")
    add("status", cmd_status, help="human-readable status")
    add("dashboard", cmd_dashboard, spec=False, help="table of all specs")
    add("list", cmd_list, spec=False, help="list spec names")

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
