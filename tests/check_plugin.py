#!/usr/bin/env python3
"""Static consistency checks for the plugin itself (run in CI and before releases)."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []


def frontmatter(path: Path) -> dict:
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        errors.append(f"{path}: missing frontmatter")
        return {}
    fm: dict = {}
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"^\s+- ", line) and key:
            fm.setdefault(key, []).append(line.strip()[2:])
        elif ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key = key.strip()
            fm[key] = val.strip() if val.strip() else fm.get(key, [])
    return fm


# versions agree
plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
versions = {plugin["version"], market["metadata"]["version"], *[p["version"] for p in market["plugins"]]}
if len(versions) != 1:
    errors.append(f"version mismatch: {versions}")

# agents: aliases only, names match files
agent_names = set()
for p in sorted((ROOT / "agents").glob("*.md")):
    fm = frontmatter(p)
    agent_names.add(fm.get("name"))
    if fm.get("name") != p.stem:
        errors.append(f"{p}: name '{fm.get('name')}' != filename")
    if fm.get("model") not in {"opus", "sonnet", "haiku", "inherit"}:
        errors.append(f"{p}: model should be an alias, got {fm.get('model')!r}")
    if fm.get("model") == "sonnet" and not str(fm.get("maxTurns", "")).isdigit():
        errors.append(f"{p}: execution agents need an integer maxTurns")
    for t in fm.get("tools", []):
        if t.startswith("mcp__"):
            errors.append(f"{p}: references MCP tool {t} the plugin does not ship")

# skills: names match dirs; agent references resolve; CLI references resolve
cli_cmds = set(re.findall(r'add\("([a-z-]+)"', (ROOT / "scripts/spec-state.py").read_text()))
for p in sorted((ROOT / "skills").glob("*/SKILL.md")):
    fm = frontmatter(p)
    if fm.get("name") != p.parent.name:
        errors.append(f"{p}: name '{fm.get('name')}' != directory")
    text = p.read_text()
    for m in re.finditer(r"spec-engine:(spec-[a-z-]+)", text):
        if m.group(1) not in agent_names:
            errors.append(f"{p}: references unknown agent {m.group(1)}")
    if re.search(r"spec-driven:", text):
        errors.append(f"{p}: stale 'spec-driven:' plugin prefix")
    for m in re.finditer(r"\$SS ([a-z][a-z-]*)", text):
        if m.group(1) not in cli_cmds and m.group(1) not in {"-h"}:
            errors.append(f"{p}: unknown spec-state command '{m.group(1)}'")
    if "AskUserQuestion" in text and "AskUserQuestion" not in fm.get("allowed-tools", []) and "never call askuserquestion" not in text.lower():
        errors.append(f"{p}: mentions AskUserQuestion but does not allow it")

for p in [ROOT / "references/execution-core.md"]:
    for m in re.finditer(r"\$SS ([a-z][a-z-]*)", p.read_text()):
        if m.group(1) not in cli_cmds:
            errors.append(f"{p}: unknown spec-state command '{m.group(1)}'")

# every agent referenced somewhere; every file referenced exists
all_text = "\n".join(p.read_text() for p in list(ROOT.glob("skills/*/SKILL.md")) + list(ROOT.glob("references/*.md")))
for name in agent_names:
    if name not in all_text:
        errors.append(f"agent {name} is never dispatched by any skill")
for m in set(re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)", all_text)):
    if not (ROOT / m).exists():
        errors.append(f"referenced plugin file missing: {m}")

# workflow scripts: valid meta literal and no forbidden APIs
for p in sorted((ROOT / "workflows").glob("*.js")):
    js = p.read_text()
    if not js.lstrip().startswith("export const meta = {"):
        errors.append(f"{p}: must start with `export const meta = {{`")
    for bad in (r"Date\.now\(", r"Math\.random\(", r"\brequire\(", r"^\s*import ", r"\bprocess\.", r"\bfs\."):
        if re.search(bad, js, re.M):
            errors.append(f"{p}: uses {bad!r}, unavailable in workflow scripts")
    for m in re.finditer(r"agentType: '([a-z-]+):([a-z-]+)'", js):
        if m.group(1) != "spec-engine" or m.group(2) not in agent_names:
            errors.append(f"{p}: unknown agentType {m.group(0)}")
for m in set(re.findall(r"workflows/([\w.-]+\.js)", all_text)):
    if not (ROOT / "workflows" / m).exists():
        errors.append(f"referenced workflow script missing: workflows/{m}")

# evals: each case has prompt.md and at least one grader
for case in sorted((ROOT / "evals").iterdir()) if (ROOT / "evals").exists() else []:
    if case.is_dir() and case.name != "results":
        if not (case / "prompt.md").exists() or not list((case / "graders").glob("*.md")):
            errors.append(f"evals/{case.name}: needs prompt.md and graders/*.md")

# hooks reference existing scripts
hooks = json.loads((ROOT / "hooks/hooks.json").read_text())
for event in hooks["hooks"].values():
    for group in event:
        for h in group["hooks"]:
            for m in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)", h["command"]):
                if not (ROOT / m).exists():
                    errors.append(f"hook script missing: {m}")

if errors:
    print("\n".join("ERROR: " + e for e in errors))
    sys.exit(1)
print("plugin consistency ok")
