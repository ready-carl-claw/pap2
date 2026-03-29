#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

CANONICAL_FILES = [
    "PRD.md",
    "Spec.md",
    "Plan.md",
    "TODO.md",
    "progress.md",
    "Lessons.md",
    "summary.md",
    "User-Steer.md",
    ".pap.json",
]

RUN_TYPES = ["build", "qa", "plan", "design"]
TASK_KINDS = ["build", "test", "fix"]
DONE_STATUSES = {"done", "completed", "closed", "passed"}
REQUIRED_CANONICAL_FILES = [
    "PRD.md",
    "Spec.md",
    "Plan.md",
    "TODO.md",
    "progress.md",
    "Lessons.md",
    "summary.md",
    "User-Steer.md",
    ".pap.json",
]


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def now_utc_iso() -> str:
    return now_utc().isoformat().replace("+00:00", "Z")


def now_utc_stamp() -> str:
    return now_utc().strftime("%Y-%m-%d %H:%M UTC")


def parse_iso_utc(text: str | None) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def minutes_between(start: datetime | None, end: datetime | None = None) -> float | None:
    if start is None:
        return None
    end = end or now_utc()
    return max((end - start).total_seconds() / 60.0, 0.0)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "project"


@dataclass
class ProjectPaths:
    base_dir: Path
    project_name: str

    @property
    def root(self) -> Path:
        return self.base_dir / f"[PAP2]{self.project_name}"

    @property
    def slug(self) -> str:
        return slugify(self.project_name)


STEER_LINE_RE = re.compile(r"^(?P<indent>\s*)(?P<number>\d+)\.\s*(?P<body>.*)$")


def default_texts(project_name: str) -> dict[str, str]:
    return {
        "PRD.md": (
            f"# {project_name} PRD\n\n"
            "## Goal\n- TODO\n\n"
            "## Requirements\n- TODO\n\n"
            "## Success Criteria\n- TODO\n"
        ),
        "Spec.md": (
            f"# {project_name} Spec\n\n"
            "## System Design\n- TODO\n\n"
            "## Testable Surfaces\n- TODO\n\n"
            "## Architectural Risks\n- TODO\n"
        ),
        "Plan.md": (
            f"# {project_name} Plan\n\n"
            "## Phases\n1. TODO\n\n"
            "## Milestones\n### M1\n- Objective\n- Success conditions\n- QA checkpoint\n"
        ),
        "progress.md": (
            f"# {project_name} Progress\n\n"
            "## Current Status\n- TODO\n\n"
            "## Completed\n- None yet\n\n"
            "## In Progress\n- None yet\n\n"
            "## Blockers\n- None\n"
        ),
        "Lessons.md": (
            f"# {project_name} Lessons\n\n"
            "> Build mode owns this file.\n"
            "> Only write non-trivial lessons that matter for redesign or replanning.\n\n"
            "## Lessons\n"
        ),
        "summary.md": (
            f"# {project_name} Run Summaries\n\n"
            "> User-facing append-only log. Cron writes here and never reads it.\n\n"
            "## Summaries\n"
        ),
        "TODO.md": (
            f"# {project_name} TODO\n\n"
            "> Keep at most 5 active unfinished items.\n"
            "> Task kinds: build, test, fix.\n\n"
            "---\n"
            "id: task-001\n"
            "kind: build\n"
            "title: TODO\n"
            "milestone: M1\n"
            "acceptance:\n"
            "  - TODO\n"
            "status: open\n"
            "---\n"
        ),
        "User-Steer.md": "",
    }


def cmd_migrate(args: argparse.Namespace) -> int:
    """Migrate from legacy PAP folder to PAP2 folder."""
    import sys
    
    # Resolve the base directory (workspace root)
    base_dir = Path(args.base_dir).expanduser().resolve()
    project_name = args.project_name
    
    # Legacy PAP folder
    legacy_root = base_dir / f"[PAP]{project_name}"
    # PAP2 folder
    pap2_root = base_dir / f"[PAP2]{project_name}"
    
    if not legacy_root.exists():
        print(f"Error: Legacy PAP folder not found: {legacy_root}", file=sys.stderr)
        return 1
    
    # Create PAP2 folder if it doesn't exist
    pap2_root.mkdir(parents=True, exist_ok=True)
    
    # Read legacy files
    legacy_prd = (legacy_root / "PRD.md").read_text(encoding="utf-8") if (legacy_root / "PRD.md").exists() else ""
    legacy_plan = (legacy_root / "Plan.md").read_text(encoding="utf-8") if (legacy_root / "Plan.md").exists() else ""
    legacy_progress = (legacy_root / "progress.md").read_text(encoding="utf-8") if (legacy_root / "progress.md").exists() else ""
    legacy_steer = (legacy_root / "User-Steer.md").read_text(encoding="utf-8") if (legacy_root / "User-Steer.md").exists() else ""
    legacy_todo = (legacy_root / "TODO.md").read_text(encoding="utf-8") if (legacy_root / "TODO.md").exists() else ""
    
    # Find additional reference files in legacy folder
    reference_files = {}
    for md_file in legacy_root.glob("*.md"):
        if md_file.name in CANONICAL_FILES:
            continue
        reference_files[md_file.name] = md_file.read_text(encoding="utf-8")
    
    # Build migration result
    result = {
        "legacyRoot": str(legacy_root),
        "pap2Root": str(pap2_root),
        "projectName": project_name,
        "filesRead": {
            "PRD.md": bool(legacy_prd),
            "Plan.md": bool(legacy_plan),
            "progress.md": bool(legacy_progress),
            "User-Steer.md": bool(legacy_steer),
            "TODO.md": bool(legacy_todo),
        },
        "referenceFiles": list(reference_files.keys()),
    }
    
    # Write canonical files to PAP2 folder
    # 1. PRD.md - will be strengthened by LLM
    # 2. Spec.md - will be generated by design phase
    # 3. Plan.md - will be generated by planning phase
    # 4. progress.md - migrated
    # 5. User-Steer.md - migrated
    # 6. TODO.md - migrated as-is (will be reformatted in PAP2 format later)
    # 7. .pap.json - initial state
    # 8. Lessons.md, summary.md - created empty
    
    # progress.md - migrate relevant content
    progress_content = f"# {project_name} Progress\n\n"
    if legacy_progress:
        # Extract key info from legacy progress
        progress_content += legacy_progress + "\n\n"
    progress_content += "## Migrated from legacy PAP\n"
    progress_content += f"- Original: {legacy_root.name}\n"
    progress_content += f"- Migrated: {now_utc_stamp()}\n"
    
    (pap2_root / "progress.md").write_text(progress_content, encoding="utf-8")
    
    # User-Steer.md - migrate all steers
    steer_content = f"# {project_name} User Steer\n\n"
    if legacy_steer:
        steer_content += "## Historical Steers (Migrated)\n\n"
        steer_content += legacy_steer + "\n"
    else:
        steer_content += "## Active Log\n"
    
    (pap2_root / "User-Steer.md").write_text(steer_content, encoding="utf-8")
    
    # TODO.md - migrate as-is (basic conversion to PAP2 format)
    todo_content = f"# {project_name} TODO\n\n"
    todo_content += "> Migrated from legacy PAP. Tasks need reformatting to PAP2 YAML blocks.\n\n"
    if legacy_todo:
        todo_content += "---\n" + legacy_todo + "\n---\n"
    else:
        todo_content += "---\nid: task-001\nkind: build\ntitle: TODO\nmilestone: M1\nacceptance:\n  - TODO\nstatus: open\n---\n"
    
    (pap2_root / "TODO.md").write_text(todo_content, encoding="utf-8")
    
    # Create empty Lessons.md and summary.md
    (pap2_root / "Lessons.md").write_text(
        f"# {project_name} Lessons\n\n"
        "> Build mode owns this file.\n"
        "> Only write non-trivial lessons that matter for redesign or replanning.\n\n"
        "## Lessons\n",
        encoding="utf-8"
    )
    (pap2_root / "summary.md").write_text(
        f"# {project_name} Run Summaries\n\n"
        "> User-facing append-only log.\n\n"
        "## Summaries\n",
        encoding="utf-8"
    )
    
    # Create initial PRD.md placeholder (will be strengthened by LLM)
    (pap2_root / "PRD.md").write_text(
        f"# {project_name} PRD\n\n"
        "## Goal\n- TODO (migrated from legacy PAP)\n\n"
        "## Requirements\n- TODO\n\n"
        "## Success Criteria\n- TODO\n\n"
        "---\n"
        "## Legacy Migration Notes\n"
        f"Original PRD:\n{legacy_prd[:500] if legacy_prd else 'N/A'}...\n",
        encoding="utf-8"
    )
    
    # Create initial Spec.md placeholder (will be generated by design phase)
    (pap2_root / "Spec.md").write_text(
        f"# {project_name} Spec\n\n"
        "## System Design\n- TODO\n\n"
        "## Testable Surfaces\n- TODO\n\n"
        "## Architectural Risks\n- TODO\n",
        encoding="utf-8"
    )
    
    # Create initial Plan.md placeholder (will be generated by planning phase)
    (pap2_root / "Plan.md").write_text(
        f"# {project_name} Plan\n\n"
        "## Phases\n1. TODO\n\n"
        "## Milestones\n### M1\n- Objective\n- Success conditions\n- QA checkpoint\n",
        encoding="utf-8"
    )
    
    # Migrate useful reference files
    migrated_refs = []
    for ref_name, ref_content in reference_files.items():
        # Skip very large binary-like files
        if len(ref_content) > 500000:
            continue
        dest_path = pap2_root / ref_name
        dest_path.write_text(ref_content, encoding="utf-8")
        migrated_refs.append(ref_name)
    
    # Create initial .pap.json state
    state = build_state(ProjectPaths(base_dir=base_dir, project_name=project_name))
    save_state(pap2_root, state)
    
    result["pap2FilesCreated"] = [
        "PRD.md",
        "Spec.md",
        "Plan.md", 
        "progress.md",
        "Lessons.md",
        "summary.md",
        "User-Steer.md",
        "TODO.md",
        ".pap.json",
    ]
    result["migratedReferences"] = migrated_refs
    result["status"] = "migrated"
    result["note"] = "PRD/Spec/Plan need LLM strengthening. TODO needs reformatting to YAML blocks."
    
    print_json(result)
    return 0


def build_state(paths: ProjectPaths, summary_channel: str | None = None) -> dict[str, Any]:
    timestamp = now_utc_iso()
    return {
        "projectName": paths.project_name,
        "projectSlug": paths.slug,
        "projectRoot": str(paths.root.resolve()),
        "autopilotEnabled": False,
        "cadencePreset": "tick",
        "cadenceMinutes": 2,
        "tickMinutes": 2,
        "runBudgetTicks": 4,
        "runBudgetMinutes": 8,
        "staleRunThresholdTicks": 8,
        "staleRunThresholdMinutes": 16,
        "cronJobId": None,
        "papCategoryName": "PAP2",
        "papChannelName": f"{paths.slug}-pap2",
        "papChannelId": None,
        "summaryRoutingEnabled": bool(summary_channel),
        "summaryChannel": summary_channel,
        "currentRunType": "build",
        "nextRunType": "build",
        "runInProgress": False,
        "activeRunId": None,
        "activeRunStartedAt": None,
        "activeRunTickBudget": 4,
        "lastRunType": None,
        "lastStaleRecoveryAt": None,
        "staleRecoveryCount": 0,
        "runCount": 0,
        "todosClearedCount": 0,
        "userSteersFulfilledCount": 0,
        "lastRunAt": None,
        "lastRunResult": None,
        "lastBlockers": [],
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }


def write_if_missing(path: Path, content: str, force: bool = False) -> None:
    if force or not path.exists() or not path.read_text(encoding="utf-8").strip():
        path.write_text(content, encoding="utf-8")


def load_state(project_root: Path) -> dict[str, Any]:
    state_path = project_root / ".pap.json"
    if not state_path.exists():
        raise SystemExit(f"Missing state file: {state_path}")
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(project_root: Path, state: dict[str, Any]) -> None:
    state["updatedAt"] = now_utc_iso()
    (project_root / ".pap.json").write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def extract_yaml_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    in_block = False
    buf: list[str] = []
    for line in text.splitlines():
        if line.strip() == "---":
            if in_block:
                blocks.append("\n".join(buf).strip())
                buf = []
                in_block = False
            else:
                in_block = True
                buf = []
            continue
        if in_block:
            buf.append(line)
    return [b for b in blocks if b.strip()]


def simple_yaml_parse(block: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw in block.splitlines():
        if not raw.strip():
            continue
        if raw.lstrip().startswith("- ") and current_list_key:
            data.setdefault(current_list_key, []).append(raw.split("- ", 1)[1].strip())
            continue
        if ":" in raw:
            key, value = raw.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                data[key] = []
                current_list_key = key
            else:
                data[key] = value
                current_list_key = None
    return data


def parse_task_blocks(todo_text: str) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for block in extract_yaml_blocks(todo_text):
        if yaml is not None:
            try:
                parsed = yaml.safe_load(block)
            except Exception:
                parsed = simple_yaml_parse(block)
        else:
            parsed = simple_yaml_parse(block)
        if isinstance(parsed, dict):
            tasks.append(parsed)
    return tasks


def task_is_open(task: dict[str, Any]) -> bool:
    status = str(task.get("status", "open")).strip().lower()
    return status not in DONE_STATUSES


def task_counts(todo_text: str) -> dict[str, int]:
    counts = {kind: 0 for kind in TASK_KINDS}
    active = 0
    for task in parse_task_blocks(todo_text):
        kind = str(task.get("kind", "")).strip().lower()
        if kind in counts and task_is_open(task):
            counts[kind] += 1
            active += 1
    counts["activeTotal"] = active
    return counts


def normalize_task(task: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(task)
    normalized["id"] = str(normalized.get("id", "")).strip()
    normalized["kind"] = str(normalized.get("kind", "build")).strip().lower() or "build"
    normalized["title"] = str(normalized.get("title", "")).strip()
    normalized["milestone"] = str(normalized.get("milestone", "")).strip()
    for key in ("refs", "files", "acceptance"):
        value = normalized.get(key, [])
        if isinstance(value, str):
            value = [value] if value.strip() else []
        elif not isinstance(value, list):
            value = []
        normalized[key] = [str(x).strip() for x in value if str(x).strip()]
    normalized["status"] = str(normalized.get("status", "open")).strip().lower() or "open"
    return normalized


def dump_yaml_block(task: dict[str, Any]) -> str:
    task = normalize_task(task)
    lines: list[str] = ["---"]
    ordered_keys = ["id", "kind", "title", "milestone", "refs", "files", "acceptance", "status"]
    for key in ordered_keys:
        value = task.get(key)
        if value in (None, "") or value == []:
            continue
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def read_tasks(project_root: Path) -> list[dict[str, Any]]:
    todo_path = project_root / "TODO.md"
    if not todo_path.exists():
        return []
    return [normalize_task(t) for t in parse_task_blocks(todo_path.read_text(encoding="utf-8"))]


def write_tasks(project_root: Path, tasks: list[dict[str, Any]]) -> None:
    state = load_state(project_root) if (project_root / ".pap.json").exists() else {}
    project_name = state.get("projectName") or project_root.name
    header = [
        f"# {project_name} TODO",
        "",
        "> Keep at most 5 active unfinished items.",
        "> Store tasks as structured YAML blocks inside the Markdown file.",
        "> Every task must declare its kind: `build`, `test`, or `fix`.",
        "> `build` and `fix` are handled by Build mode.",
        "> `test` is handled by QA mode.",
        "> Internal engineer validation and smoke testing still belong inside `build` work.",
        "> Build mode writes QA-facing `test` tasks, but QA may strengthen or overwrite weak test requirements before running them.",
        "",
    ]
    blocks = [dump_yaml_block(t) for t in tasks]
    content = "\n".join(header + blocks).rstrip() + "\n"
    (project_root / "TODO.md").write_text(content, encoding="utf-8")


def next_task_id(tasks: list[dict[str, Any]]) -> str:
    max_n = 0
    for task in tasks:
        m = re.match(r"task-(\d+)$", str(task.get("id", "")).strip())
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"task-{max_n + 1:03d}"


def parse_steer_lines(text: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line in text.splitlines():
        m = STEER_LINE_RE.match(line)
        if not m:
            continue
        body = m.group("body").strip()
        done = body.lower().startswith("[done]")
        normalized = re.sub(r"^\[done\]\s*", "", body, flags=re.IGNORECASE)
        result.append({
            "number": int(m.group("number")),
            "done": done,
            "text": normalized,
            "raw": line,
        })
    return result


def next_unfinished_steer(text: str) -> dict[str, Any] | None:
    for item in parse_steer_lines(text):
        if not item["done"]:
            return item
    return None


def append_steer_line(text: str, steer: str) -> str:
    lines = text.splitlines()
    existing = parse_steer_lines(text)
    next_number = (max((item["number"] for item in existing), default=0) + 1)
    if text and not text.endswith("\n"):
        text += "\n"
    text += f"{next_number}. {steer.strip()}\n"
    return text


def mark_steer_done_text(text: str, number: int) -> tuple[str, bool]:
    changed = False
    out_lines: list[str] = []
    had_trailing_newline = text.endswith("\n")
    for line in text.splitlines():
        m = STEER_LINE_RE.match(line)
        if not m or int(m.group("number")) != number:
            out_lines.append(line)
            continue
        body = m.group("body").strip()
        if body.lower().startswith("[done]"):
            out_lines.append(line)
            continue
        out_lines.append(f"{m.group('indent')}{number}. [Done] {body}")
        changed = True
    updated = "\n".join(out_lines)
    if had_trailing_newline or changed:
        updated += "\n"
    return updated, changed


def append_summary(project_root: Path, summary_text: str, stamp: str | None = None) -> None:
    summary_path = project_root / "summary.md"
    if not summary_path.exists():
        summary_path.write_text("# Run Summaries\n\n## Summaries\n", encoding="utf-8")
    current = summary_path.read_text(encoding="utf-8")
    if current and not current.endswith("\n"):
        current += "\n"
    stamp = stamp or now_utc_stamp()
    normalized = summary_text.replace("\\n", "\n").strip()
    current += f"\n### {stamp}\n{normalized}\n"
    summary_path.write_text(current, encoding="utf-8")


def validate_project(project_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    missing_files = [name for name in REQUIRED_CANONICAL_FILES if not (project_root / name).exists()]
    if missing_files:
        errors.append(f"Missing canonical files: {', '.join(missing_files)}")

    state = load_state(project_root) if (project_root / '.pap.json').exists() else None
    if state:
        current_run_type = state.get('currentRunType')
        next_run_type = state.get('nextRunType')
        if current_run_type not in RUN_TYPES:
            errors.append(f"Invalid currentRunType: {current_run_type}")
        if next_run_type not in RUN_TYPES:
            errors.append(f"Invalid nextRunType: {next_run_type}")
        if state.get('cadenceMinutes') != 2:
            warnings.append(f"cadenceMinutes is {state.get('cadenceMinutes')}; PAP2 default is 2")
        if state.get('runBudgetMinutes') != 8:
            warnings.append(f"runBudgetMinutes is {state.get('runBudgetMinutes')}; PAP2 default is 8")
        if state.get('staleRunThresholdMinutes') != 16:
            warnings.append(f"staleRunThresholdMinutes is {state.get('staleRunThresholdMinutes')}; PAP2 default is 16")

    todo_text = (project_root / 'TODO.md').read_text(encoding='utf-8') if (project_root / 'TODO.md').exists() else ''
    tasks = parse_task_blocks(todo_text)
    open_tasks = [t for t in tasks if task_is_open(t)]
    if len(open_tasks) > 5:
        errors.append(f"TODO.md has {len(open_tasks)} active tasks; limit is 5")
    for i, task in enumerate(tasks, start=1):
        kind = str(task.get('kind', '')).strip().lower()
        if kind not in TASK_KINDS:
            errors.append(f"Task {i} has invalid kind: {kind or '<missing>'}")
        if not str(task.get('title', '')).strip():
            warnings.append(f"Task {i} is missing a title")
        if not str(task.get('status', '')).strip():
            warnings.append(f"Task {i} is missing a status")

    steer_text = (project_root / 'User-Steer.md').read_text(encoding='utf-8') if (project_root / 'User-Steer.md').exists() else ''
    steer_items = parse_steer_lines(steer_text)
    if steer_text.strip() and not steer_items:
        errors.append('User-Steer.md is non-empty but contains no valid numbered steer lines')
    for idx, item in enumerate(steer_items, start=1):
        if item['number'] != idx:
            errors.append(f"User-Steer.md numbering is not contiguous at item {idx}; found {item['number']}")
            break

    summary_path = project_root / 'summary.md'
    if summary_path.exists() and not summary_path.read_text(encoding='utf-8').startswith('#'):
        warnings.append('summary.md does not begin with a markdown heading')

    readiness = {
        'projectRoot': str(project_root),
        'valid': not errors,
        'errors': errors,
        'warnings': warnings,
        'taskCounts': task_counts(todo_text),
        'nextSteer': next_unfinished_steer(steer_text),
    }
    return readiness


def append_bullet_under_heading(path: Path, heading: str, bullet_text: str, title: str | None = None) -> None:
    if not path.exists():
        if title is None:
            title = path.stem
        path.write_text(f"# {title}\n\n## {heading}\n", encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    heading_line = f"## {heading}"
    try:
        idx = lines.index(heading_line)
    except ValueError:
        if text and not text.endswith("\n"):
            text += "\n"
        text += f"\n## {heading}\n"
        lines = text.splitlines()
        idx = lines.index(heading_line)

    section_end = idx + 1
    while section_end < len(lines) and not lines[section_end].startswith("## "):
        section_end += 1

    section_body = lines[idx + 1:section_end]
    placeholders = {"- none", "- none yet", "- todo"}
    cleaned_body = [line for line in section_body if line.strip().lower() not in placeholders]

    while cleaned_body and cleaned_body[-1].strip() == "":
        cleaned_body.pop()

    cleaned_body.append(f"- {bullet_text.strip()}")

    remainder = lines[section_end:]
    if remainder and remainder[0].startswith("## "):
        cleaned_body.append("")

    new_lines = lines[:idx + 1] + cleaned_body + remainder
    updated = "\n".join(new_lines).rstrip() + "\n"
    path.write_text(updated, encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> int:
    base_dir = Path(args.base_dir).expanduser().resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    paths = ProjectPaths(base_dir=base_dir, project_name=args.project_name)
    paths.root.mkdir(parents=True, exist_ok=True)

    for name, content in default_texts(args.project_name).items():
        write_if_missing(paths.root / name, content, force=args.force)

    state_path = paths.root / ".pap.json"
    if args.force or not state_path.exists():
        save_state(paths.root, build_state(paths, summary_channel=args.summary_channel))

    todo_text = (paths.root / "TODO.md").read_text(encoding="utf-8")
    steer_text = (paths.root / "User-Steer.md").read_text(encoding="utf-8")
    result = {
        "projectRoot": str(paths.root),
        "projectSlug": paths.slug,
        "papChannelName": f"{paths.slug}-pap2",
        "canonicalFiles": CANONICAL_FILES,
        "taskCounts": task_counts(todo_text),
        "nextSteer": next_unfinished_steer(steer_text),
        "pap2Compatible": all((paths.root / name).exists() for name in CANONICAL_FILES),
    }
    print_json(result)
    return 0


def cmd_validate_project(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    print_json(validate_project(project_root))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    state = load_state(project_root)
    todo_text = (project_root / "TODO.md").read_text(encoding="utf-8") if (project_root / "TODO.md").exists() else ""
    steer_text = (project_root / "User-Steer.md").read_text(encoding="utf-8") if (project_root / "User-Steer.md").exists() else ""
    active_started = parse_iso_utc(state.get("activeRunStartedAt"))
    result = {
        "projectName": state.get("projectName"),
        "projectRoot": str(project_root),
        "autopilotEnabled": state.get("autopilotEnabled"),
        "cadencePreset": state.get("cadencePreset"),
        "cadenceMinutes": state.get("cadenceMinutes"),
        "tickMinutes": state.get("tickMinutes"),
        "runBudgetMinutes": state.get("runBudgetMinutes"),
        "staleRunThresholdMinutes": state.get("staleRunThresholdMinutes"),
        "cronJobId": state.get("cronJobId"),
        "currentRunType": state.get("currentRunType"),
        "nextRunType": state.get("nextRunType"),
        "runInProgress": state.get("runInProgress"),
        "activeRunId": state.get("activeRunId"),
        "activeRunAgeMinutes": minutes_between(active_started),
        "runCount": state.get("runCount", 0),
        "todosClearedCount": state.get("todosClearedCount", 0),
        "userSteersFulfilledCount": state.get("userSteersFulfilledCount", 0),
        "staleRecoveryCount": state.get("staleRecoveryCount", 0),
        "lastRunAt": state.get("lastRunAt"),
        "lastRunType": state.get("lastRunType"),
        "lastRunResult": state.get("lastRunResult"),
        "lastBlockers": state.get("lastBlockers", []),
        "summaryRoutingEnabled": state.get("summaryRoutingEnabled", False),
        "summaryChannel": state.get("summaryChannel"),
        "taskCounts": task_counts(todo_text),
        "nextSteer": next_unfinished_steer(steer_text),
        "papChannelName": state.get("papChannelName"),
        "papChannelId": state.get("papChannelId"),
    }
    print_json(result)
    return 0


def cmd_steer(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    steer_path = project_root / "User-Steer.md"
    if not steer_path.exists():
        raise SystemExit(f"Missing steer file: {steer_path}")
    current = steer_path.read_text(encoding="utf-8")
    updated = append_steer_line(current, args.text)
    steer_path.write_text(updated, encoding="utf-8")
    print_json({
        "projectRoot": str(project_root),
        "appended": True,
        "nextSteer": next_unfinished_steer(updated),
    })
    return 0


def cmd_mark_steer_done(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    steer_path = project_root / "User-Steer.md"
    current = steer_path.read_text(encoding="utf-8")
    updated, changed = mark_steer_done_text(current, args.number)
    if changed:
        steer_path.write_text(updated, encoding="utf-8")
        state = load_state(project_root)
        state["userSteersFulfilledCount"] = int(state.get("userSteersFulfilledCount", 0)) + 1
        save_state(project_root, state)
    print_json({
        "projectRoot": str(project_root),
        "number": args.number,
        "changed": changed,
        "nextSteer": next_unfinished_steer(updated if changed else current),
    })
    return 0


def cmd_set_runtime(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    state = load_state(project_root)
    if args.autopilot_enabled is not None:
        state["autopilotEnabled"] = args.autopilot_enabled
    if args.cron_job_id is not None:
        state["cronJobId"] = args.cron_job_id
    if args.pap_channel_id is not None:
        state["papChannelId"] = args.pap_channel_id
    if args.pap_channel_name is not None:
        state["papChannelName"] = args.pap_channel_name
    if args.pap_category_name is not None:
        state["papCategoryName"] = args.pap_category_name
    if args.summary_routing_enabled is not None:
        state["summaryRoutingEnabled"] = args.summary_routing_enabled
    if args.summary_channel is not None:
        state["summaryChannel"] = args.summary_channel
    if args.current_run_type is not None:
        state["currentRunType"] = args.current_run_type
    if args.next_run_type is not None:
        state["nextRunType"] = args.next_run_type
    save_state(project_root, state)
    print_json(state)
    return 0


def maybe_recover_stale_run(state: dict[str, Any]) -> bool:
    if not state.get("runInProgress"):
        return False
    started = parse_iso_utc(state.get("activeRunStartedAt"))
    age = minutes_between(started)
    threshold = float(state.get("staleRunThresholdMinutes", 16) or 16)
    if age is None or age <= threshold:
        return False
    state["runInProgress"] = False
    state["activeRunId"] = None
    state["activeRunStartedAt"] = None
    state["lastStaleRecoveryAt"] = now_utc_iso()
    state["staleRecoveryCount"] = int(state.get("staleRecoveryCount", 0)) + 1
    state["lastRunResult"] = "stale-recovered"
    return True


def cmd_acquire_run(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    state = load_state(project_root)

    if args.require_autopilot_enabled and not state.get("autopilotEnabled", False):
        print_json({
            "projectRoot": str(project_root),
            "acquired": False,
            "skipped": True,
            "reason": "autopilot-disabled",
            "state": state,
        })
        return 0

    stale_recovered = maybe_recover_stale_run(state)

    if state.get("runInProgress"):
        started = parse_iso_utc(state.get("activeRunStartedAt"))
        print_json({
            "projectRoot": str(project_root),
            "acquired": False,
            "skipped": True,
            "reason": "active-run-healthy",
            "activeRunId": state.get("activeRunId"),
            "activeRunAgeMinutes": minutes_between(started),
            "state": state,
        })
        return 0

    run_id = args.run_id or f"run_{uuid.uuid4().hex[:12]}"
    state["runInProgress"] = True
    state["activeRunId"] = run_id
    state["activeRunStartedAt"] = now_utc_iso()
    state["activeRunTickBudget"] = int(state.get("runBudgetTicks", 4) or 4)
    state["currentRunType"] = state.get("nextRunType") or state.get("currentRunType") or "build"
    save_state(project_root, state)
    print_json({
        "projectRoot": str(project_root),
        "acquired": True,
        "skipped": False,
        "staleRecovered": stale_recovered,
        "runId": run_id,
        "currentRunType": state.get("currentRunType"),
        "state": state,
    })
    return 0


def cmd_list_tasks(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    tasks = read_tasks(project_root)
    if args.kind:
        tasks = [t for t in tasks if t.get("kind") == args.kind]
    if args.open_only:
        tasks = [t for t in tasks if task_is_open(t)]
    print_json({
        "projectRoot": str(project_root),
        "count": len(tasks),
        "tasks": tasks,
    })
    return 0


def cmd_add_task(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    tasks = read_tasks(project_root)
    active_count = sum(1 for t in tasks if task_is_open(t))
    if args.status.lower() not in DONE_STATUSES and active_count >= 5 and not args.force:
        raise SystemExit("Refusing to add another open task: TODO.md already has 5 active tasks. Use --force to override.")
    task = normalize_task({
        "id": args.task_id or next_task_id(tasks),
        "kind": args.kind,
        "title": args.title,
        "milestone": args.milestone or "",
        "refs": args.ref or [],
        "files": args.file or [],
        "acceptance": args.acceptance or [],
        "status": args.status,
    })
    tasks.append(task)
    write_tasks(project_root, tasks)
    print_json({
        "projectRoot": str(project_root),
        "added": True,
        "task": task,
        "taskCounts": task_counts((project_root / 'TODO.md').read_text(encoding='utf-8')),
    })
    return 0


def cmd_update_task(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    tasks = read_tasks(project_root)
    updated_task = None
    for idx, task in enumerate(tasks):
        if task.get("id") != args.task_id:
            continue
        if args.kind is not None:
            task["kind"] = args.kind
        if args.status is not None:
            task["status"] = args.status.lower()
        if args.title is not None:
            task["title"] = args.title
        if args.milestone is not None:
            task["milestone"] = args.milestone
        updated_task = normalize_task(task)
        tasks[idx] = updated_task
        break
    if updated_task is None:
        raise SystemExit(f"Task not found: {args.task_id}")
    open_count = sum(1 for t in tasks if task_is_open(t))
    if open_count > 5 and not args.force:
        raise SystemExit("Update would leave TODO.md with more than 5 active tasks. Use --force to override.")
    write_tasks(project_root, tasks)
    print_json({
        "projectRoot": str(project_root),
        "updated": True,
        "task": updated_task,
        "taskCounts": task_counts((project_root / 'TODO.md').read_text(encoding='utf-8')),
    })
    return 0


def cmd_fail_test_task(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    tasks = read_tasks(project_root)
    target = None
    for idx, task in enumerate(tasks):
        if task.get("id") == args.task_id:
            target = (idx, task)
            break
    if target is None:
        raise SystemExit(f"Task not found: {args.task_id}")
    idx, task = target
    if task.get("kind") != "test" and not args.force:
        raise SystemExit(f"Task {args.task_id} is not a test task. Use --force to override.")

    bug_repro_path = project_root / "BugRepro.md"
    notes = args.note or []
    bug_repro = [
        f"# {load_state(project_root).get('projectName', project_root.name)} Bug Reproduction",
        "",
        "## Source Test Task",
        f"- {task.get('id')}",
        f"- {task.get('title')}",
        "",
        "## How It Was Tested",
        f"- {args.how_tested}",
        "",
        "## Expected Result",
        f"- {args.expected}",
        "",
        "## Actual Result",
        f"- {args.actual}",
    ]
    if notes:
        bug_repro += ["", "## Notes"] + [f"- {n}" for n in notes]
    bug_repro_path.write_text("\n".join(bug_repro).rstrip() + "\n", encoding="utf-8")

    fix_task = normalize_task({
        "id": task.get("id"),
        "kind": "fix",
        "title": args.fix_title or f"Fix: {task.get('title', args.task_id)}",
        "milestone": task.get("milestone", ""),
        "refs": ["BugRepro.md"],
        "files": task.get("files", []),
        "acceptance": task.get("acceptance", []),
        "status": "open",
    })
    tasks[idx] = fix_task
    write_tasks(project_root, tasks)
    print_json({
        "projectRoot": str(project_root),
        "updated": True,
        "bugRepro": str(bug_repro_path),
        "task": fix_task,
        "taskCounts": task_counts((project_root / 'TODO.md').read_text(encoding='utf-8')),
    })
    return 0


def cmd_pass_test_task(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    tasks = read_tasks(project_root)
    updated_task = None
    for idx, task in enumerate(tasks):
        if task.get("id") != args.task_id:
            continue
        if task.get("kind") != "test" and not args.force:
            raise SystemExit(f"Task {args.task_id} is not a test task. Use --force to override.")
        task["status"] = "passed"
        updated_task = normalize_task(task)
        tasks[idx] = updated_task
        break
    if updated_task is None:
        raise SystemExit(f"Task not found: {args.task_id}")
    write_tasks(project_root, tasks)
    if args.progress_note:
        append_bullet_under_heading(project_root / "progress.md", "Completed", args.progress_note, title=f"{project_root.name} Progress")
    print_json({
        "projectRoot": str(project_root),
        "updated": True,
        "task": updated_task,
        "taskCounts": task_counts((project_root / 'TODO.md').read_text(encoding='utf-8')),
    })
    return 0


def cmd_complete_task(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    tasks = read_tasks(project_root)
    updated_task = None
    status = args.status.lower()
    for idx, task in enumerate(tasks):
        if task.get("id") != args.task_id:
            continue
        task["status"] = status
        updated_task = normalize_task(task)
        tasks[idx] = updated_task
        break
    if updated_task is None:
        raise SystemExit(f"Task not found: {args.task_id}")
    write_tasks(project_root, tasks)
    if args.progress_note:
        append_bullet_under_heading(project_root / "progress.md", "Completed", args.progress_note, title=f"{project_root.name} Progress")
    print_json({
        "projectRoot": str(project_root),
        "updated": True,
        "task": updated_task,
        "taskCounts": task_counts((project_root / 'TODO.md').read_text(encoding='utf-8')),
    })
    return 0


def cmd_request_qa(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    tasks = read_tasks(project_root)
    active_count = sum(1 for t in tasks if task_is_open(t))
    if active_count >= 5 and not args.force:
        raise SystemExit("Refusing to add another open test task: TODO.md already has 5 active tasks. Use --force to override.")
    task = normalize_task({
        "id": args.task_id or next_task_id(tasks),
        "kind": "test",
        "title": args.title,
        "milestone": args.milestone or "",
        "refs": args.ref or [],
        "files": args.file or [],
        "acceptance": args.acceptance or [],
        "status": "open",
    })
    tasks.append(task)
    write_tasks(project_root, tasks)
    state = load_state(project_root)
    state["nextRunType"] = "qa"
    save_state(project_root, state)
    print_json({
        "projectRoot": str(project_root),
        "added": True,
        "task": task,
        "nextRunType": "qa",
        "taskCounts": task_counts((project_root / 'TODO.md').read_text(encoding='utf-8')),
    })
    return 0


def cmd_note_progress(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    progress_path = project_root / "progress.md"
    append_bullet_under_heading(progress_path, args.section, args.text, title=f"{project_root.name} Progress")
    print_json({"projectRoot": str(project_root), "updated": True, "file": str(progress_path), "section": args.section})
    return 0


def cmd_add_lesson(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    lessons_path = project_root / "Lessons.md"
    append_bullet_under_heading(lessons_path, "Lessons", args.text, title=f"{project_root.name} Lessons")
    print_json({"projectRoot": str(project_root), "updated": True, "file": str(lessons_path)})
    return 0


def cmd_append_summary(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    append_summary(project_root, args.text, stamp=args.stamp)
    print_json({"projectRoot": str(project_root), "updated": True, "file": str(project_root / 'summary.md')})
    return 0


def cmd_finish_run(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    state = load_state(project_root)

    if args.expected_run_id and state.get("activeRunId") != args.expected_run_id:
        print_json({
            "projectRoot": str(project_root),
            "finished": False,
            "skipped": True,
            "reason": "run-id-mismatch",
            "expectedRunId": args.expected_run_id,
            "actualRunId": state.get("activeRunId"),
            "state": state,
        })
        return 0

    current_run_type = args.current_run_type or state.get("currentRunType") or "build"
    next_run_type = args.next_run_type or state.get("nextRunType") or current_run_type
    blockers = [b.strip() for b in (args.blocker or []) if b and b.strip() and b.strip().lower() != "none"]

    state["runInProgress"] = False
    state["activeRunId"] = None
    state["activeRunStartedAt"] = None
    state["lastRunAt"] = args.last_run_at or now_utc_iso()
    state["lastRunType"] = current_run_type
    state["lastRunResult"] = args.result
    state["currentRunType"] = current_run_type
    state["nextRunType"] = next_run_type
    state["lastBlockers"] = blockers
    state["runCount"] = int(state.get("runCount", 0)) + 1
    if args.todos_cleared:
        state["todosClearedCount"] = int(state.get("todosClearedCount", 0)) + args.todos_cleared
    if args.steers_fulfilled:
        state["userSteersFulfilledCount"] = int(state.get("userSteersFulfilledCount", 0)) + args.steers_fulfilled
    save_state(project_root, state)

    summary_appended = False
    if args.summary_text:
        append_summary(project_root, args.summary_text, stamp=now_utc_stamp())
        summary_appended = True

    print_json({
        "projectRoot": str(project_root),
        "finished": True,
        "summaryAppended": summary_appended,
        "state": state,
    })
    return 0


def cmd_stop_runtime(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    state = load_state(project_root)
    state["autopilotEnabled"] = False
    save_state(project_root, state)
    print_json(state)
    return 0


def cmd_clear_runtime(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    state = load_state(project_root)
    state["autopilotEnabled"] = False
    state["cronJobId"] = None
    state["runInProgress"] = False
    state["activeRunId"] = None
    state["activeRunStartedAt"] = None
    save_state(project_root, state)
    print_json(state)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PAP2 helper")
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="Initialize or retrofit a PAP2 project folder")
    init_p.add_argument("--base-dir", required=True)
    init_p.add_argument("--project-name", required=True)
    init_p.add_argument("--summary-channel")
    init_p.add_argument("--force", action="store_true")
    init_p.set_defaults(func=cmd_init)

    migrate_p = sub.add_parser("migrate", help="Migrate from legacy [PAP] folder to [PAP2] folder")
    migrate_p.add_argument("--base-dir", required=True)
    migrate_p.add_argument("--project-name", required=True)
    migrate_p.set_defaults(func=cmd_migrate)

    status_p = sub.add_parser("status", help="Show PAP2 status")
    status_p.add_argument("--project-root", required=True)
    status_p.set_defaults(func=cmd_status)

    validate_p = sub.add_parser("validate-project", help="Validate PAP2 project readiness and structure")
    validate_p.add_argument("--project-root", required=True)
    validate_p.set_defaults(func=cmd_validate_project)

    list_tasks_p = sub.add_parser("list-tasks", help="List structured TODO tasks")
    list_tasks_p.add_argument("--project-root", required=True)
    list_tasks_p.add_argument("--kind", choices=TASK_KINDS)
    list_tasks_p.add_argument("--open-only", action="store_true")
    list_tasks_p.set_defaults(func=cmd_list_tasks)

    add_task_p = sub.add_parser("add-task", help="Add a structured task block to TODO.md")
    add_task_p.add_argument("--project-root", required=True)
    add_task_p.add_argument("--task-id")
    add_task_p.add_argument("--kind", required=True, choices=TASK_KINDS)
    add_task_p.add_argument("--title", required=True)
    add_task_p.add_argument("--milestone")
    add_task_p.add_argument("--ref", action="append")
    add_task_p.add_argument("--file", action="append")
    add_task_p.add_argument("--acceptance", action="append")
    add_task_p.add_argument("--status", default="open")
    add_task_p.add_argument("--force", action="store_true")
    add_task_p.set_defaults(func=cmd_add_task)

    update_task_p = sub.add_parser("update-task", help="Update basic fields on an existing task")
    update_task_p.add_argument("--project-root", required=True)
    update_task_p.add_argument("--task-id", required=True)
    update_task_p.add_argument("--kind", choices=TASK_KINDS)
    update_task_p.add_argument("--status")
    update_task_p.add_argument("--title")
    update_task_p.add_argument("--milestone")
    update_task_p.add_argument("--force", action="store_true")
    update_task_p.set_defaults(func=cmd_update_task)

    fail_test_p = sub.add_parser("fail-test-task", help="Convert a failed test task into a fix task and write BugRepro.md")
    fail_test_p.add_argument("--project-root", required=True)
    fail_test_p.add_argument("--task-id", required=True)
    fail_test_p.add_argument("--how-tested", required=True)
    fail_test_p.add_argument("--expected", required=True)
    fail_test_p.add_argument("--actual", required=True)
    fail_test_p.add_argument("--note", action="append")
    fail_test_p.add_argument("--fix-title")
    fail_test_p.add_argument("--force", action="store_true")
    fail_test_p.set_defaults(func=cmd_fail_test_task)

    pass_test_p = sub.add_parser("pass-test-task", help="Mark a test task passed and optionally append progress")
    pass_test_p.add_argument("--project-root", required=True)
    pass_test_p.add_argument("--task-id", required=True)
    pass_test_p.add_argument("--progress-note")
    pass_test_p.add_argument("--force", action="store_true")
    pass_test_p.set_defaults(func=cmd_pass_test_task)

    complete_task_p = sub.add_parser("complete-task", help="Mark any task completed/done/closed and optionally append progress")
    complete_task_p.add_argument("--project-root", required=True)
    complete_task_p.add_argument("--task-id", required=True)
    complete_task_p.add_argument("--status", default="done")
    complete_task_p.add_argument("--progress-note")
    complete_task_p.set_defaults(func=cmd_complete_task)

    request_qa_p = sub.add_parser("request-qa", help="Create a QA test task and set nextRunType=qa")
    request_qa_p.add_argument("--project-root", required=True)
    request_qa_p.add_argument("--task-id")
    request_qa_p.add_argument("--title", required=True)
    request_qa_p.add_argument("--milestone")
    request_qa_p.add_argument("--ref", action="append")
    request_qa_p.add_argument("--file", action="append")
    request_qa_p.add_argument("--acceptance", action="append")
    request_qa_p.add_argument("--force", action="store_true")
    request_qa_p.set_defaults(func=cmd_request_qa)

    steer_p = sub.add_parser("steer", help="Append a new numbered steer entry")
    steer_p.add_argument("--project-root", required=True)
    steer_p.add_argument("--text", required=True)
    steer_p.set_defaults(func=cmd_steer)

    done_p = sub.add_parser("mark-steer-done", help="Mark a numbered steer item as done")
    done_p.add_argument("--project-root", required=True)
    done_p.add_argument("--number", required=True, type=int)
    done_p.set_defaults(func=cmd_mark_steer_done)

    progress_p = sub.add_parser("note-progress", help="Append a bullet under a named progress.md section")
    progress_p.add_argument("--project-root", required=True)
    progress_p.add_argument("--section", required=True, choices=["Current Status", "Completed", "In Progress", "Blockers"])
    progress_p.add_argument("--text", required=True)
    progress_p.set_defaults(func=cmd_note_progress)

    lesson_p = sub.add_parser("add-lesson", help="Append a non-trivial lesson to Lessons.md")
    lesson_p.add_argument("--project-root", required=True)
    lesson_p.add_argument("--text", required=True)
    lesson_p.set_defaults(func=cmd_add_lesson)

    summary_p = sub.add_parser("append-summary", help="Append a user-facing entry to summary.md")
    summary_p.add_argument("--project-root", required=True)
    summary_p.add_argument("--text", required=True)
    summary_p.add_argument("--stamp")
    summary_p.set_defaults(func=cmd_append_summary)

    runtime_p = sub.add_parser("set-runtime", help="Persist live PAP2 runtime fields")
    runtime_p.add_argument("--project-root", required=True)
    runtime_p.add_argument("--autopilot-enabled", dest="autopilot_enabled", action="store_true")
    runtime_p.add_argument("--autopilot-disabled", dest="autopilot_enabled", action="store_false")
    runtime_p.add_argument("--cron-job-id")
    runtime_p.add_argument("--pap-channel-id")
    runtime_p.add_argument("--pap-channel-name")
    runtime_p.add_argument("--pap-category-name")
    runtime_p.add_argument("--summary-routing-enabled", dest="summary_routing_enabled", action="store_true")
    runtime_p.add_argument("--summary-routing-disabled", dest="summary_routing_enabled", action="store_false")
    runtime_p.add_argument("--summary-channel")
    runtime_p.add_argument("--current-run-type", choices=RUN_TYPES)
    runtime_p.add_argument("--next-run-type", choices=RUN_TYPES)
    runtime_p.set_defaults(func=cmd_set_runtime, autopilot_enabled=None, summary_routing_enabled=None)

    acquire_p = sub.add_parser("acquire-run", help="Acquire the PAP2 runtime slot if no healthy run is active")
    acquire_p.add_argument("--project-root", required=True)
    acquire_p.add_argument("--run-id")
    acquire_p.add_argument("--require-autopilot-enabled", action="store_true")
    acquire_p.set_defaults(func=cmd_acquire_run)

    finish_p = sub.add_parser("finish-run", help="Finish a PAP2 run, clear runtime flags, append summary, and persist routing")
    finish_p.add_argument("--project-root", required=True)
    finish_p.add_argument("--result", required=True)
    finish_p.add_argument("--current-run-type", choices=RUN_TYPES)
    finish_p.add_argument("--next-run-type", choices=RUN_TYPES)
    finish_p.add_argument("--todos-cleared", type=int, default=0)
    finish_p.add_argument("--steers-fulfilled", type=int, default=0)
    finish_p.add_argument("--summary-text")
    finish_p.add_argument("--blocker", action="append")
    finish_p.add_argument("--last-run-at")
    finish_p.add_argument("--expected-run-id")
    finish_p.set_defaults(func=cmd_finish_run)

    stop_p = sub.add_parser("stop-runtime", help="Disable autopilot while preserving cron linkage")
    stop_p.add_argument("--project-root", required=True)
    stop_p.set_defaults(func=cmd_stop_runtime)

    clear_p = sub.add_parser("clear-runtime", help="Disable autopilot and clear runtime linkage")
    clear_p.add_argument("--project-root", required=True)
    clear_p.set_defaults(func=cmd_clear_runtime)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
