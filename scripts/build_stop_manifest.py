#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_iso_utc(text: str | None):
    if not text:
        return None
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def minutes_between(start):
    if start is None:
        return None
    return max((datetime.now(timezone.utc) - start).total_seconds() / 60.0, 0.0)


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a deterministic PAP2 stop manifest')
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    state = json.loads((project_root / '.pap.json').read_text(encoding='utf-8'))
    active_started = parse_iso_utc(state.get('activeRunStartedAt'))

    run_in_progress = state.get('runInProgress', False)
    manifest = {
        'projectRoot': str(project_root),
        'projectName': state.get('projectName'),
        'cronJobId': state.get('cronJobId'),
        'autopilotEnabled': state.get('autopilotEnabled', False),
        'runInProgress': run_in_progress,
        'activeRunId': state.get('activeRunId'),
        'activeRunAgeMinutes': minutes_between(active_started),
        'recommendedCronAction': 'disable',
        'interruptCurrentRun': False,
        'stopTakesEffectNextCycle': bool(run_in_progress),
        'runtimeUpdate': {
            'autopilotEnabled': False,
        },
        'preserveForResume': [
            '.pap.json',
            'PRD.md',
            'Spec.md',
            'Plan.md',
            'TODO.md',
            'progress.md',
            'Lessons.md',
            'summary.md',
            'User-Steer.md',
        ],
    }
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
