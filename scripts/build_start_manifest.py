#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def load_state(project_root: Path) -> dict:
    return json.loads((project_root / '.pap.json').read_text(encoding='utf-8'))


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a deterministic PAP2 start manifest')
    parser.add_argument('--project-root', required=True)
    parser.add_argument('--model')
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    state = load_state(project_root)

    validation = json.loads(
        subprocess.check_output(
            [
                'python3',
                str(Path(__file__).with_name('pap2.py')),
                'validate-project',
                '--project-root', str(project_root),
            ],
            text=True,
        )
    )

    cron_job = json.loads(
        subprocess.check_output(
            [
                'python3',
                str(Path(__file__).with_name('build_cron_job.py')),
                '--project-root', str(project_root),
                '--project-name', state['projectName'],
                '--every-minutes', str(state.get('cadenceMinutes', 2)),
                '--execution-minutes', str(state.get('runBudgetMinutes', 8)),
                '--tick-minutes', str(state.get('tickMinutes', 2)),
                '--stale-minutes', str(state.get('staleRunThresholdMinutes', 16)),
                *( ['--model', args.model] if args.model else [] ),
            ],
            text=True,
        )
    )

    manifest = {
        'projectRoot': str(project_root),
        'projectName': state.get('projectName'),
        'projectSlug': state.get('projectSlug'),
        'categoryName': state.get('papCategoryName', 'PAP2'),
        'channelName': state.get('papChannelName'),
        'summaryRoutingEnabled': state.get('summaryRoutingEnabled', False),
        'summaryChannel': state.get('summaryChannel'),
        'desiredCronCadenceMinutes': state.get('cadenceMinutes', 2),
        'desiredTickMinutes': state.get('tickMinutes', 2),
        'desiredRunBudgetMinutes': state.get('runBudgetMinutes', 8),
        'desiredStaleThresholdMinutes': state.get('staleRunThresholdMinutes', 16),
        'validation': validation,
        'readyToStart': bool(validation.get('valid', False)),
        'cronJob': cron_job,
        'runtimeUpdate': {
            'autopilotEnabled': True,
            'currentRunType': state.get('currentRunType', 'build'),
            'nextRunType': state.get('nextRunType', 'build'),
            'runInProgress': False,
        },
        'immediateRunRecommended': True,
    }
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
