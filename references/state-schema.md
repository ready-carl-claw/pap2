# PAP2 state schema

Use `.pap.json` in the project root for explicit PAP2 operational state.

## Suggested shape

```json
{
  "projectName": "Project Auto Pilot 2",
  "projectSlug": "project-auto-pilot-2",
  "projectRoot": "/abs/path/to/[PAP2]Project Auto Pilot 2",
  "autopilotEnabled": false,
  "cadencePreset": "tick",
  "cadenceMinutes": 2,
  "tickMinutes": 2,
  "runBudgetTicks": 4,
  "runBudgetMinutes": 8,
  "staleRunThresholdTicks": 8,
  "staleRunThresholdMinutes": 16,
  "cronJobId": null,
  "papCategoryName": "PAP2",
  "papChannelName": "project-auto-pilot-2-pap2",
  "papChannelId": null,
  "summaryRoutingEnabled": false,
  "summaryChannel": null,
  "currentRunType": "build",
  "nextRunType": "build",
  "runInProgress": false,
  "activeRunId": null,
  "activeRunStartedAt": null,
  "activeRunTickBudget": 4,
  "lastRunType": null,
  "lastStaleRecoveryAt": null,
  "staleRecoveryCount": 0,
  "runCount": 0,
  "todosClearedCount": 0,
  "userSteersFulfilledCount": 0,
  "lastRunAt": null,
  "lastRunResult": null,
  "lastBlockers": [],
  "createdAt": "2026-03-28T00:00:00Z",
  "updatedAt": "2026-03-28T00:00:00Z"
}
```

## Field semantics

- `projectName`: human display name.
- `projectSlug`: filesystem-safe and channel-safe slug.
- `projectRoot`: absolute path to the PAP2 project folder.
- `autopilotEnabled`: whether future cycles should run.
- `cadencePreset`: recommended to use `tick`.
- `cadenceMinutes`: cron fire cadence in minutes; recommended default is `2`.
- `tickMinutes`: tick size in minutes. Current design: `2`.
- `runBudgetTicks`: soft per-run planning budget in ticks. Current design: `4`.
- `runBudgetMinutes`: soft per-run planning budget in minutes. Current design: `8`.
- `staleRunThresholdTicks`: stale-run recovery threshold in ticks. Current design: `8`.
- `staleRunThresholdMinutes`: stale-run recovery threshold in minutes. Current design: `16`.
- `cronJobId`: the OpenClaw cron job id.
- `papCategoryName`: recommended Discord category name for PAP2.
- `papChannelName`: expected report channel name, usually `<project-slug>-pap2`.
- `papChannelId`: Discord channel id once created.
- `summaryRoutingEnabled`: whether end-of-run summaries should also be routed to a message channel.
- `summaryChannel`: optional configured summary target.
- `currentRunType`: the run type currently being executed. Values: `build`, `qa`, `plan`, `design`.
- `nextRunType`: the run type the next eligible cron cycle should execute.
- `runInProgress`: overlap-suppression flag.
- `activeRunId`: identifier for the active run when one is in progress.
- `activeRunStartedAt`: UTC ISO timestamp for when the active run began.
- `activeRunTickBudget`: soft budget allocated to the active run in ticks.
- `lastRunType`: the most recent finished run type.
- `lastStaleRecoveryAt`: UTC ISO timestamp of the most recent stale-run recovery.
- `staleRecoveryCount`: count of stale-run recoveries.
- `runCount`: increment after each finished cycle.
- `todosClearedCount`: increment when one or more tasks are completed and removed/resolved.
- `userSteersFulfilledCount`: increment when a steer item is marked `[Done]`.
- `lastRunAt`: UTC ISO timestamp of the latest finished cycle.
- `lastRunResult`: short result label such as `success`, `partial`, `blocked`, `failed`, `stale-recovered`.
- `lastBlockers`: short array of unresolved blockers from the last cycle.
- `createdAt` / `updatedAt`: UTC ISO timestamps.

## Counter discipline

- Prefer explicit counters in `.pap.json` over reparsing all history every time.
- Update counters only after durable file updates are complete.
- Do not silently reset counters when retrofitting an existing project.
