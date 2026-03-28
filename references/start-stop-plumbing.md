# PAP2 start/stop plumbing

PAP2 uses a fixed tick scheduler.

## Runtime defaults
- tick = 2 minutes
- cron fire cadence = 2 minutes
- soft run budget = 8 minutes
- stale threshold = 16 minutes
- default next run type = `build`

## Deterministic validation + manifests

Run validation first, then generate manifests before live `/pap2 start` or `/pap2 stop` operations:

### Validation

```bash
python3 scripts/pap2.py validate-project \
  --project-root "/abs/path/to/[PAP2]Project Name"
```

## Deterministic manifests

Generate these before live `/pap2 start` or `/pap2 stop` operations:

### Start manifest

```bash
python3 scripts/build_start_manifest.py \
  --project-root "/abs/path/to/[PAP2]Project Name"
```

### Stop manifest

```bash
python3 scripts/build_stop_manifest.py \
  --project-root "/abs/path/to/[PAP2]Project Name"
```

## Runtime state on start

Recommended fields:
- `autopilotEnabled = true`
- `cadencePreset = tick`
- `cadenceMinutes = 2`
- `tickMinutes = 2`
- `runBudgetTicks = 4`
- `runBudgetMinutes = 8`
- `staleRunThresholdTicks = 8`
- `staleRunThresholdMinutes = 16`
- `currentRunType = build`
- `nextRunType = build`
- `runInProgress = false`

## Example set-runtime

```bash
python3 scripts/pap2.py set-runtime \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --autopilot-enabled \
  --cron-job-id "job_123" \
  --pap-channel-id "channel_123" \
  --pap-channel-name "project-name-pap2" \
  --pap-category-name "PAP2"
```

## Example stop-runtime

```bash
python3 scripts/pap2.py stop-runtime \
  --project-root "/abs/path/to/[PAP2]Project Name"
```

Use this after the live cron job has been disabled or marked to stop future runs.

## Example clear-runtime

```bash
python3 scripts/pap2.py clear-runtime \
  --project-root "/abs/path/to/[PAP2]Project Name"
```

## Example finish-run

```bash
python3 scripts/pap2.py finish-run \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --result success \
  --current-run-type build \
  --next-run-type qa \
  --todos-cleared 2 \
  --summary-text "✅ Milestone reached; QA next." \
  --blocker "None"
```
