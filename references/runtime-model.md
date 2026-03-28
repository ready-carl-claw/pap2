# PAP2 runtime model

PAP2 uses a fixed-tick scheduler with overlap suppression and stale-run recovery.

## Tick model
- 1 tick = 2 minutes
- cron fires every 1 tick

## Soft budget
- soft work budget = 4 ticks = 8 minutes
- this is a planning budget, not a hard kill timeout
- slight overrun is acceptable
- avoid massively under-utilizing the budget when meaningful work exists

This matters most for:
- Build runs
- QA runs

Planning runs may often exit earlier.

## Overlap suppression
At the start of every cron fire:
1. inspect `.pap.json`
2. if `runInProgress=false`, acquire the run slot and continue
3. if `runInProgress=true`, compare active-run age against stale threshold
4. if still healthy, silently exit
5. if stale, recover flags and continue

## Stale-run recovery
Recommended stale threshold:
- 2x soft budget

With current defaults:
- soft budget = 8 minutes
- stale threshold = 16 minutes

When a stale run is detected:
- clear active runtime flags
- record stale recovery in state
- allow the new cron cycle to start

## Runtime flags in `.pap.json`
- `currentRunType`
- `nextRunType`
- `runInProgress`
- `activeRunId`
- `activeRunStartedAt`
- `activeRunTickBudget`
- `lastStaleRecoveryAt`
- `staleRecoveryCount`

## Deterministic helper usage

### Acquire run
```bash
python3 scripts/pap2.py acquire-run \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --require-autopilot-enabled
```

### Finish run
```bash
python3 scripts/pap2.py finish-run \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --result partial \
  --current-run-type build \
  --next-run-type qa \
  --summary-text "🛠️ Build made progress; QA next."
```

## Summary output

After every run:
- append a short user-facing summary to `summary.md`
- never read `summary.md` as an input
- if summary routing is configured, send the same summary to the configured channel
