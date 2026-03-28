# PAP2 phase model

PAP2 separates product definition, system design, execution planning, building, and QA into distinct phases.

## Phase chain

### PRD phase
- specialist: full `product-manager` profile
- output: `PRD.md`
- triggers:
  - `/pap2 init` when creating/retrofitting a project
  - `/pap2 prd`
- non-cron phase

### Design phase
- specialist: full `software-architect` profile
- required inputs:
  - `PRD.md`
  - `Lessons.md` when it exists
- output: `Spec.md`
- non-default run type under cron: `design`
- a `design` run means:
  1. revise `Spec.md`
  2. then run Planning
  3. then exit

### Planning phase
- specialist: full `project-manager-senior` profile
- inputs:
  - `PRD.md`
  - `Spec.md`
- output: `Plan.md`
- cron-eligible run type: `plan`

### Build phase
- primary owner of normal execution
- inputs:
  - `Spec.md`
  - `Plan.md`
  - `TODO.md`
  - `progress.md`
- owns:
  - `TODO.md`
  - `progress.md`
  - `Lessons.md`
  - QA-facing `test` tasks
- can request QA by creating a `kind: test` task and setting `nextRunType=qa`
- can set next run type to:
  - `qa`
  - `plan`
  - `design`

### QA phase
- independent skeptical validation layer
- inputs:
  - `PRD.md`
  - `Spec.md`
  - `Plan.md`
  - `TODO.md`
  - `progress.md`
- consumes only `kind: test` tasks
- may strengthen or overwrite weak test requirements before running them
- on pass:
  - mark the `test` task passed/completed
  - optionally append completion evidence to `progress.md`
- on failure:
  - write `BugRepro.md`
  - convert the failed `test` task into a `fix` task for Build

## Run types

Explicit run types in `.pap.json`:
- `build`
- `qa`
- `plan`
- `design`

`prd` is not a normal cron run type.

## Redesign routing

Build is the phase allowed to flip the next run type to `design` when it realizes the current design may be wrong.

Deterministic redesign flow:
1. Build detects design may be wrong
2. Build sets `nextRunType=design`
3. next cron run performs `design -> plan -> exit`

## QA split across docs

### `Spec.md`
Defines what is testable:
- testable components
- testable routes
- APIs / jobs / flows / subsystems
- contracts and architectural surfaces that need validation

### `Plan.md`
Defines when QA engages:
- milestones
- milestone success conditions
- QA checkpoints
- QA timing and sequencing against milestones

## User steer precedence

Every cron cycle reads `User-Steer.md` first.

Steer classification:
- product-level steer -> `prd -> design -> plan`, then exit
- design-level steer -> `design -> plan`, then exit
- planning-level steer -> `plan`, then exit
- task-level steer -> update `TODO.md`, do Build work, then exit

Steer-triggered PRD / Design / Planning flows are non-interactive.
They modify files and continue the required downstream phase flow without asking the user follow-up questions.
