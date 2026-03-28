# pap2

PAP2 is a second-generation **Project Auto Pilot** implemented as an OpenClaw skill package.

It is designed as a **side-by-side successor** to the original `pap` workflow, not an in-place replacement. The goal is to let Carl compare a more structured, phase-driven autonomous project loop against the legacy PAP model.

## What PAP2 is

PAP2 is currently best understood as an **advanced operational skill** with plugin-like architecture.

It provides:
- a stricter phase model
- deterministic helper scripts
- structured project files
- explicit cron run types
- steering-first autonomous execution
- stronger Build / QA / redesign separation

It does **not** modify the original `pap` skill.

## Core idea

PAP2 splits project automation into distinct artifacts and phases:

- `PRD.md` — product definition
- `Spec.md` — system design
- `Plan.md` — execution phases, milestones, QA checkpoints
- `TODO.md` — structured YAML task queue
- `progress.md` — grounded execution status
- `Lessons.md` — non-trivial insights from Build that should influence redesign
- `summary.md` — user-facing append-only run summaries
- `User-Steer.md` — append-only human steering input
- `.pap.json` — explicit runtime state
- `BugRepro.md` — QA failure handoff to Build

## Phase model

### Strategic phases
- `prd` → writes `PRD.md`
- `design` → writes `Spec.md`
- `plan` → writes `Plan.md`

### Routine cron run types
- `build`
- `qa`
- `plan`
- `design`

Key rule:
- Build can explicitly set `nextRunType=design`
- a `design` run means: `design -> plan -> exit`

## Scheduler model

PAP2 uses a fixed tick scheduler:

- **1 tick = 2 minutes**
- cron fires every tick
- soft work budget = **4 ticks = 8 minutes**
- stale threshold = **8 ticks = 16 minutes**

If a previous run is still healthy, the next tick exits silently.
If a previous run is stale, PAP2 recovers and continues.

## Steering-first behavior

Every cron cycle reads `User-Steer.md` first.

Steer is append-only and numbered:

```md
1. [Done] Previous steer
2. Current pending steer
```

The first unfinished steer is classified as one of:
- product-level → `prd -> design -> plan`
- design-level → `design -> plan`
- planning-level → `plan`
- task-level → Build handles it directly

Steer-triggered PRD / Design / Planning flows are **non-interactive**.
They update files and move on without asking the user follow-up questions.

## Build vs QA

### Build
Build is a strong engineer, not a blind executor.

Build owns:
- normal `TODO.md` maintenance
- implementation work
- internal validation / smoke testing
- `progress.md`
- `Lessons.md`
- creation of QA-facing `test` tasks

Build can request QA in two main cases:
1. milestone-driven QA
2. confidence-driven “another pair of eyes” QA

### QA
QA is the independent skeptical validation layer.

QA:
- reads `PRD.md`, `Spec.md`, `Plan.md`, `TODO.md`, and `progress.md`
- consumes only `kind: test` tasks
- may strengthen weak test definitions before testing
- on failure:
  - writes `BugRepro.md`
  - converts the failed `test` task into a `fix` task
- on pass:
  - marks the test passed/completed
  - may append evidence to `progress.md`

## Task model

`TODO.md` is a Markdown file containing structured YAML task blocks.

Task kinds are strict:
- `build` → Build mode
- `fix` → Build mode
- `test` → QA mode

Internal engineer validation still lives inside `build` work.
Independent QA uses `kind: test` tasks.

## Repository layout

```text
pap2/
├── README.md
├── SKILL.md
├── references/
│   ├── command-behavior.md
│   ├── cron-run-template.md
│   ├── file-templates.md
│   ├── live-tool-orchestration.md
│   ├── phase-model.md
│   ├── runtime-model.md
│   ├── start-stop-plumbing.md
│   └── state-schema.md
└── scripts/
    ├── build_cron_job.py
    ├── build_cron_prompt.py
    ├── build_start_manifest.py
    ├── build_stop_manifest.py
    ├── pap.py
    └── pap2.py
```

## Main helper scripts

### `scripts/pap2.py`
Deterministic helper for local PAP2 state and file operations.

Supports operations like:
- `init`
- `validate-project`
- `status`
- `steer`
- `mark-steer-done`
- `list-tasks`
- `add-task`
- `update-task`
- `request-qa`
- `pass-test-task`
- `fail-test-task`
- `complete-task`
- `note-progress`
- `add-lesson`
- `append-summary`
- `acquire-run`
- `finish-run`
- `set-runtime`
- `stop-runtime`
- `clear-runtime`

### `scripts/build_cron_job.py`
Builds the OpenClaw cron payload for a PAP2 project.

### `scripts/build_start_manifest.py`
Builds a deterministic start manifest including:
- validation output
- `readyToStart`
- desired channel/category names
- cron payload
- runtime updates

### `scripts/build_stop_manifest.py`
Builds a deterministic stop manifest including:
- active run status
- whether stop takes effect next cycle
- runtime update intent
- resume preservation guidance

## Real `/pap2 start|stop` operations

Local scripts do **not** replace OpenClaw live tool orchestration.

The current split is:
- local scripts generate deterministic state/manifests
- OpenClaw tools perform live actions such as:
  - creating Discord categories/channels
  - creating/enabling/disabling cron jobs
  - routing summaries to channels

See:
- `references/live-tool-orchestration.md`

## Current status

PAP2 is already substantial enough to be used as a serious prototype, but it is still evolving.

Current maturity:
- strong local helper surface
- explicit runtime model
- explicit task model
- packaged as a standalone skill
- still relies on OpenClaw tool orchestration for live external actions

So today it is:
- **implemented as a skill**
- **architecturally drifting toward a plugin**

## Relationship to legacy PAP

PAP2 exists specifically so it can be compared against legacy PAP without modifying the original skill.

Legacy `pap` remains untouched.

## Packaging

A packaged skill artifact can be generated or distributed as:
- `pap2.skill`

## License / status note

This repository is currently a working prototype for Carl’s internal OpenClaw workflow development.
