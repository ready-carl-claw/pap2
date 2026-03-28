# PAP2 live tool orchestration

Use this reference when performing real `/pap2 init`, `/pap2 start`, or `/pap2 stop` operations with OpenClaw tools.

The local scripts generate deterministic manifests and state updates, but category/channel creation and cron lifecycle still happen through OpenClaw tools.

## `/pap2 init`

Typical live sequence:
1. Run `python3 scripts/pap2.py init ...`
2. Ask whether summaries should be routed to a channel.
3. If a summary channel is chosen, persist it with `scripts/pap2.py init --summary-channel ...` or `scripts/pap2.py set-runtime --summary-routing-enabled --summary-channel ...`
4. Do not create cron yet unless the user explicitly asks for `/pap2 start`

## `/pap2 start`

### 1. Validate and render desired state
Run, in order:

```bash
python3 scripts/pap2.py validate-project --project-root "/abs/path/to/[PAP2]Project Name"
python3 scripts/build_start_manifest.py --project-root "/abs/path/to/[PAP2]Project Name"
```

If validation is not ready, stop and fix the project docs/state first.

### 2. Ensure Discord category and channel
Use `message` tool with `channel=discord`.

Suggested logic:
- find or create category named `PAP2`
- find or create channel named `<project-slug>-pap2` under that category
- persist returned `papChannelId`, `papChannelName`, and `papCategoryName` into `.pap.json`

Practical tool pattern:
1. `message action=channel-list channel=discord`
2. if category missing -> `message action=category-create`
3. if channel missing -> `message action=channel-create`
4. if channel exists under wrong category -> `message action=channel-edit` or `channel-move`

### 3. Ensure cron job
Use `cron` tool.

Suggested logic:
1. `cron action=list`
2. if PAP2 job for this project exists -> `cron action=update` or `cron action=run` as needed
3. if missing -> `cron action=add` with the manifest-generated cron payload
4. persist `cronJobId` into `.pap.json`

### 4. Persist runtime linkage
Use `python3 scripts/pap2.py set-runtime ...` to store:
- `autopilotEnabled=true`
- `cronJobId`
- `papChannelId`
- `papChannelName`
- `papCategoryName`
- any summary routing config

### 5. Immediate first run
After start succeeds:
- trigger one immediate cron run using `cron action=run`

## `/pap2 stop`

### 1. Render desired stop state
Run:

```bash
python3 scripts/build_stop_manifest.py --project-root "/abs/path/to/[PAP2]Project Name"
```

### 2. Disable future cron runs
Use `cron` tool:
- prefer disable/update over delete
- do not interrupt the active run

If the manifest reports `stopTakesEffectNextCycle=true`, tell the user the current run is still active and stop will take effect on the next cycle.

### 3. Persist runtime stop state
Use:

```bash
python3 scripts/pap2.py stop-runtime --project-root "/abs/path/to/[PAP2]Project Name"
```

Keep `.pap.json` and project docs intact for fast resume.

## Summary routing

When summary routing is enabled in `.pap.json`:
- every end-of-run summary should still append to `summary.md`
- and the same short summary may also be sent with the `message` tool to the configured target

## Guiding rule

Use local scripts for deterministic state/manifests.
Use OpenClaw `message` + `cron` tools for live external operations.
Do not try to replace tool orchestration with shell hacks.
