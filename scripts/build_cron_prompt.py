#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


def extract_prompt_body(template: str) -> str:
    match = re.search(r"```text\n(.*?)\n```", template, flags=re.DOTALL)
    return match.group(1) if match else template


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the PAP2 cron run prompt template")
    parser.add_argument("--template", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--execution-minutes", type=int, default=8)
    parser.add_argument("--tick-minutes", type=int, default=2)
    parser.add_argument("--stale-minutes", type=int, default=16)
    args = parser.parse_args()

    template = Path(args.template).read_text(encoding="utf-8")
    rendered = extract_prompt_body(template)
    rendered = rendered.replace("{{PROJECT_ROOT}}", args.project_root)
    rendered = rendered.replace("{{PROJECT_NAME}}", args.project_name)
    rendered = rendered.replace("{{EXECUTION_MINUTES}}", str(args.execution_minutes))
    rendered = rendered.replace("{{TICK_MINUTES}}", str(args.tick_minutes))
    rendered = rendered.replace("{{STALE_MINUTES}}", str(args.stale_minutes))
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
