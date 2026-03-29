# PAP2 command behavior

## `/pap2 init`

Expected flow:
1. Confirm the target session-base path.
2. Create or retrofit a PAP2 folder at `<session-base>/[PAP2]<project name>/`.
3. Ensure canonical files exist:
   - `PRD.md`
   - `Spec.md`
   - `Plan.md`
   - `TODO.md`
   - `progress.md`
   - `Lessons.md`
   - `summary.md`
   - `User-Steer.md`
   - `.pap.json`
4. Ask whether the user wants run summaries routed to a message channel.
5. Persist summary routing preferences into `.pap.json`.
6. Do not start cron unless the user separately asks for `/pap2 start`.

Use `python3 scripts/pap2.py init ...` for deterministic scaffolding.

## `/pap2 start`

Expected flow:
1. Re-read the canonical docs and `.pap.json`.
2. Read `references/live-tool-orchestration.md` if you are performing the real live start with OpenClaw tools.
3. Validate project readiness first:

```bash
python3 scripts/pap2.py validate-project \
  --project-root "/abs/path/to/[PAP2]Project Name"
```

3. Validate that the project is coherent enough for autonomous work.
4. Generate a deterministic start manifest:

The start manifest now includes embedded validation output and a `readyToStart` flag.

```bash
python3 scripts/build_start_manifest.py \
  --project-root "/abs/path/to/[PAP2]Project Name"
```

4. Ensure a Discord category named `PAP2` exists.
5. Ensure a channel named `<project-slug>-pap2` exists under that category.
6. Create or re-enable exactly one PAP2 cron job using the generated cron payload.
7. Persist runtime/channel linkage back into `.pap.json`.
8. PAP2 cron should fire every 2 minutes.
9. Immediately trigger one run after start succeeds.

## `/pap2 stop`

Expected flow:
1. Read `references/live-tool-orchestration.md` if you are performing the real live stop with OpenClaw tools.
2. Generate a deterministic stop manifest:

```bash
python3 scripts/build_stop_manifest.py \
  --project-root "/abs/path/to/[PAP2]Project Name"
```

2. Disable future cron runs.
3. Prefer disabling the job instead of deleting it.
4. Do not interrupt a currently active run.
5. If the stop manifest reports `stopTakesEffectNextCycle=true`, tell the user a run is still active and stop will take effect on the next cycle.
6. Persist `autopilotEnabled=false` into `.pap.json`.
7. Preserve `.pap.json` and project docs for quick resume.

## `/pap2 status`

Report:
- autopilot enabled/disabled
- cadence and tick model
- current/next run type
- whether a run is currently active
- stale recoveries
- run counters
- open task counts by kind
- next unfinished steer
- last run result/time/blockers
- summary routing status

Use `python3 scripts/pap2.py status ...` for deterministic metrics.

## Project validation helper

Use this before `/pap2 start` or when debugging project coherence:

```bash
python3 scripts/pap2.py validate-project \
  --project-root "/abs/path/to/[PAP2]Project Name"
```

Validation checks include:
- canonical files present
- valid run types in `.pap.json`
- TODO task count limit
- valid task kinds
- contiguous numbered steer format
- basic summary file sanity

## `/pap2 steer <text>`

Expected flow:
1. Append a new numbered steer line to the bottom of `User-Steer.md`.
2. Do not delete or reorder existing steer history.
3. Preserve append-only numbering.
4. Do not start project execution immediately just because steer was appended.

Use `python3 scripts/pap2.py steer ...`.

## `/pap2 migrate <project name>`

Expected flow:
1. Verify the legacy `[PAP]<project name>` folder exists
2. Create a new `[PAP2]<project name>` folder
3. Read and migrate:
   - `PRD.md` → generated via LLM (product-manager) merging legacy PRD + steers
   - `Spec.md` → generated via LLM (software-architect) from new PRD + legacy Plan
   - `Plan.md` → generated via LLM (project-manager-senior) from PRD + Spec + legacy progress
   - `progress.md` → migrated with migration timestamp
   - `User-Steer.md` → migrated as historical steer log
   - `TODO.md` → migrated (needs reformatting to PAP2 YAML blocks)
   - Other `*.md` files → migrated as reference files if useful
4. Create canonical PAP2 files:
   - `Lessons.md` (empty)
   - `summary.md` (empty)
   - `.pap.json` (initial state)
5. Report what was migrated

This command only works on projects with an existing `[PAP]` folder.
The result is a fully migrated `[PAP2]` folder ready for execution.

Use `python3 scripts/pap2.py migrate --base-dir <workspace> --project-name <name>`.

## `/pap2 prd`

Expected flow:
1. Treat this as explicit PRD drafting/revision.
2. Write or revise `PRD.md`.
3. Set the next run type to `design` so PAP2 can continue with `design -> plan`.

## Task-queue helpers

Use these deterministic helpers when you want structured TODO queue mutation instead of hand-editing:

### List tasks

```bash
python3 scripts/pap2.py list-tasks \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --open-only
```

### Add a task

```bash
python3 scripts/pap2.py add-task \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --kind build \
  --title "Implement anonymous gallery browsing" \
  --milestone M1 \
  --ref "Spec.md#gallery-surface" \
  --acceptance "anonymous user can browse gallery"
```

### Update a task

```bash
python3 scripts/pap2.py update-task \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --task-id task-002 \
  --status passed
```

### Convert failed test to fix task + BugRepro

```bash
python3 scripts/pap2.py fail-test-task \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --task-id task-002 \
  --how-tested "Opened anonymous gallery and clicked detail card" \
  --expected "detail page should load without auth prompt" \
  --actual "route redirected to login"
```

### Mark test passed

```bash
python3 scripts/pap2.py pass-test-task \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --task-id task-002 \
  --progress-note "QA passed anonymous gallery browsing"
```

### Mark task complete

```bash
python3 scripts/pap2.py complete-task \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --task-id task-001 \
  --progress-note "Finished gallery card grid implementation"
```

### Build requests QA

```bash
python3 scripts/pap2.py request-qa \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --title "Validate milestone M1 anonymous browsing" \
  --milestone M1 \
  --ref "Plan.md#qa-checkpoint-m1" \
  --acceptance "anonymous browsing works without auth" \
  --acceptance "detail route loads correctly"
```

Behavior:
- adds a `kind: test` task
- sets `nextRunType=qa`

## File-update helpers

Use these deterministic helpers when you want structured file updates instead of hand-editing:

### Append progress

```bash
python3 scripts/pap2.py note-progress \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --section "Completed" \
  --text "Finished milestone M1 card-grid implementation"
```

### Append a lesson

```bash
python3 scripts/pap2.py add-lesson \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --text "Spec assumption about API pagination was wrong because the provider returns unstable page sizes."
```

### Append a user-facing summary

```bash
python3 scripts/pap2.py append-summary \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --text "- 🛠️ Run type: build\n- ✅ Finished: implemented M1\n- 📌 Next: QA"
```

## Run-start / run-finish helpers

Use these deterministic runtime helpers:

### Acquire a run slot

```bash
python3 scripts/pap2.py acquire-run \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --require-autopilot-enabled
```

Behavior:
- if no healthy active run exists, mark the run active and return acquired state
- if an active run exists but is stale, recover and acquire a fresh run
- if a healthy active run exists, return skipped state so cron can silently exit

### Finish a run

```bash
python3 scripts/pap2.py finish-run \
  --project-root "/abs/path/to/[PAP2]Project Name" \
  --result partial \
  --current-run-type build \
  --next-run-type qa \
  --todos-cleared 1 \
  --summary-text "🛠️ Build made progress; QA next." \
  --blocker "Waiting on external API key"
```

Behavior:
- clears active runtime flags
- updates last-run fields and counters
- appends `summary.md`
- persists next run type
