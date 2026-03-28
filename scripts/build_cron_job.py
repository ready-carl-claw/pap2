#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def render_prompt(template: Path, project_root: str, project_name: str, execution_minutes: int, tick_minutes: int, stale_minutes: int) -> str:
    rendered = subprocess.check_output(
        [
            "python3",
            str(Path(__file__).with_name("build_cron_prompt.py")),
            "--template",
            str(template),
            "--project-root",
            project_root,
            "--project-name",
            project_name,
            "--execution-minutes",
            str(execution_minutes),
            "--tick-minutes",
            str(tick_minutes),
            "--stale-minutes",
            str(stale_minutes),
        ],
        text=True,
    )
    return rendered.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an OpenClaw cron job payload for PAP2")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--every-minutes", type=int, default=2)
    parser.add_argument("--execution-minutes", type=int, default=8)
    parser.add_argument("--tick-minutes", type=int, default=2)
    parser.add_argument("--stale-minutes", type=int, default=16)
    parser.add_argument("--session-target", default="isolated")
    parser.add_argument("--model")
    args = parser.parse_args()

    template = Path(__file__).resolve().parent.parent / "references" / "cron-run-template.md"
    prompt = render_prompt(template, args.project_root, args.project_name, args.execution_minutes, args.tick_minutes, args.stale_minutes)
    job = {
        "name": f"PAP2 {args.project_name}",
        "schedule": {"kind": "every", "everyMs": args.every_minutes * 60 * 1000},
        "payload": {
            "kind": "agentTurn",
            "message": prompt,
            "timeoutSeconds": max(args.execution_minutes * 60 + 240, 900),
        },
        "sessionTarget": args.session_target,
        "delivery": {"mode": "none"},
        "enabled": True,
    }
    if args.model:
        job["payload"]["model"] = args.model
    print(json.dumps(job, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
