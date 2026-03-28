# PAP2 file templates

Use these as starter structures. Keep them lean and project-specific.

## `PRD.md`

```md
# <Project Name> PRD

## Goal
- What the project must achieve.

## Requirements
- Functional requirement 1
- Functional requirement 2

## Success Criteria
- Observable success signal 1
- Observable success signal 2
```

## `Spec.md`

```md
# <Project Name> Spec

## System Design
- Main subsystems
- Boundaries and contracts
- High-level flows

## Testable Surfaces
- Components / routes / APIs / jobs that QA should be able to validate

## Architectural Risks
- Important constraints or fragile points
```

## `Plan.md`

```md
# <Project Name> Plan

## Phases
1. Phase 1
2. Phase 2

## Milestones
### M1
- Objective
- Success conditions
- QA checkpoint

### M2
- Objective
- Success conditions
- QA checkpoint

## Execution Notes
- Ordering
- Dependencies
- Replan triggers
```

## `progress.md`

```md
# <Project Name> Progress

## Current Status
- Grounded summary relative to `Plan.md`

## Completed
- Completed item tied to the plan

## In Progress
- Current active work

## Blockers
- None
```

## `Lessons.md`

```md
# <Project Name> Lessons

> Build mode owns this file.
> Only write non-trivial lessons that matter for future redesign or replanning.
> Do not dump routine mistakes or noisy scratch notes here.

## Lessons
- Assumption from `Spec.md` that `<x>` would work was wrong because `<environment/integration reality>`.
- Unexpectedly, `<approach>` worked well and may be a better design direction.
- `<constraint or behavior>` materially changes what is feasible in the system design.
```

## `summary.md`

```md
# <Project Name> Run Summaries

> User-facing append-only log.
> Cron appends one short readable summary after each run.
> Cron never reads this file.

## Summaries

### 2026-03-28 15:40 UTC
- 🛠️ Run type: build
- ✅ Finished: implemented gallery card grid
- 🧪 Validation: smoke test passed
- 📌 Next: QA on milestone M1 browsing flow
```

## `TODO.md`

```md
# <Project Name> TODO

> Keep at most 5 active unfinished items.
> Store tasks as structured YAML blocks inside the Markdown file.
> Every task must declare its kind: `build`, `test`, or `fix`.
> `build` and `fix` are handled by Build mode.
> `test` is handled by QA mode.
> Internal engineer validation and smoke testing still belong inside `build` work.
> Build mode writes QA-facing `test` tasks, but QA may strengthen or overwrite weak test requirements before running them.

---
id: task-001
kind: build
title: Implement gallery card grid
milestone: M1
refs:
  - Spec.md#gallery-surface
  - Plan.md#milestone-m1
files:
  - app/gallery.tsx
  - app/gallery.css
acceptance:
  - gallery renders cards in responsive grid
  - cards open detail view
status: open
---

---
id: task-002
kind: test
title: Validate anonymous gallery browsing
milestone: M1
refs:
  - Spec.md#gallery-surface
  - Plan.md#qa-checkpoint-m1
acceptance:
  - anonymous user can browse gallery
  - image detail loads correctly
  - no auth prompt appears
status: open
---

---
id: task-003
kind: fix
title: Fix broken anonymous detail route
milestone: M1
refs:
  - BugRepro.md
acceptance:
  - detail route works for anonymous browsing
status: open
---
```

## `BugRepro.md`

```md
# <Project Name> Bug Reproduction

## Source Test Task
- task id
- task title

## How It Was Tested
- exact validation steps performed

## Expected Result
- what should have happened

## Actual Result
- what broke or what failed to meet the bar

## Notes
- logs, screenshots, routes, APIs, files, or checkpoints involved
```

A failed QA `test` task should normally be converted into a `fix` task that references `BugRepro.md`.

## `User-Steer.md`

```md
1. [Done] Previous steer item that has already been handled.
2. Current steer item still pending.
```

## `.pap.json`

See `references/state-schema.md`.
