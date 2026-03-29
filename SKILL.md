---
name: pap2
description: Create, retrofit, and operate a second-generation Project Auto Pilot workflow via /pap2 commands, separate from the existing /pap skill. Use when Carl wants to scaffold or run a PAP v2 project with PRD.md, Spec.md, Plan.md, structured TODO.md YAML blocks, Lessons.md, summary.md, steering-first cron behavior, explicit run types (build|qa|plan|design), and a 2-minute tick scheduler without modifying the original pap skill.
---

# PAP2

Build and operate PAP2 as a separate skill from the existing `project-auto-pilot` skill.
Do not modify or route through `/pap` when the user asks for `pap2`.

## Core contract

A PAP2 project lives in exactly one folder and keeps operational truth inside that folder.

Canonical files:
- `PRD.md`
- `Spec.md`
- `Plan.md`
- `TODO.md`
- `progress.md`
- `Lessons.md`
- `summary.md`
- `User-Steer.md`
- `.pap.json`
- `BugRepro.md` when QA failures need handoff

Folder convention:
- working directory: `<session-base>/[PAP2]<project name>/`
- keep PAP2 projects separate from legacy PAP folders

## Command surface

Support this user-facing surface:
- `/pap2 init <project name>`
- `/pap2 start`
- `/pap2 stop`
- `/pap2 status`
- `/pap2 steer <text>`
- `/pap2 prd`

Alias rule:
- plain `pap2 ...` should be treated the same as `/pap2 ...`

## Operating model

### Strategic phases
- `prd` — writes `PRD.md`
- `design` — writes `Spec.md`
- `plan` — writes `Plan.md`

### Routine cron run types
- `build`
- `qa`
- `plan`
- `design`

`design` is an explicit run type, not the default recurring mode.
A `design` run means:
1. run Design mode
2. then run Planning mode
3. then exit

## Runtime model

- 1 tick = 2 minutes
- cron fires every 1 tick
- soft run budget = 4 ticks = 8 minutes
- stale threshold = 8 ticks = 16 minutes
- overlap suppression uses `.pap.json` runtime flags
- if prior run is still healthy, cron silently exits
- if prior run is stale, recover flags and continue

## Steering rule

At the start of every cron cycle, read `User-Steer.md` first.
Select the first numbered steer that is not marked `[Done]`.

Then classify it by impact:
- product-level -> `prd -> design -> plan`, then exit
- design-level -> `design -> plan`, then exit
- planning-level -> `plan`, then exit
- task-level -> update `TODO.md`, do Build work, then exit

Steer-triggered PRD / Design / Planning flows are non-interactive.
They should update files and continue the downstream phase flow without asking the user more questions.

## File ownership

### Build owns
- `TODO.md` maintenance
- `progress.md` updates
- `Lessons.md`
- QA-facing `test` tasks in `TODO.md`
- end-of-run `summary.md` append

### QA owns
- consuming `test` tasks only
- strengthening weak test definitions before testing
- writing `BugRepro.md` on failed tests
- converting failed `test` tasks into `fix` tasks for the next Build cycle
- marking passed tests as passed/completed
- end-of-run `summary.md` append

### Design always reads
- `PRD.md`
- `Lessons.md` when present

## TODO task model

`TODO.md` uses Markdown with YAML task blocks.
Task kinds are strict:
- `build` -> Build mode
- `fix` -> Build mode
- `test` -> QA mode

Internal engineer validation and smoke tests still belong inside `build` work.
Independent QA uses `kind: test` tasks.

## Summary log

`summary.md` is user-facing only.
Cron should append one short readable summary after every run.
Cron must never read `summary.md` as an input.
Optionally route the same summary to a configured message channel.
Ask for that preference during `/pap2 init`.

## Helper scripts

All helper scripts are bundled inside the skill:
- `scripts/pap2.py` — init, validate/status, task queue mutation, steer, mark steer done, acquire/finish runs, runtime state changes, and structured append helpers for progress/lessons/summary
- `scripts/build_cron_prompt.py` — render cron prompt template
- `scripts/build_cron_job.py` — build the OpenClaw cron payload
- `scripts/build_start_manifest.py` — generate the desired start/channel/cron/runtime plan from project state
- `scripts/build_stop_manifest.py` — generate the desired stop/disable/preserve-runtime plan from project state
- `cron_config.py` — shared LLM model config for cron jobs (bundled for standalone operation)

## Bundled specialists

The skill bundles the specialist profiles it needs for each phase. These live in `specialists/`:

| Phase | Specialist |
|-------|------------|
| PRD | `product-manager.md` |
| Design | `software-architect.md` |
| Planning | `project-manager-senior.md` |
| Build | `frontend-developer.md`, `backend-architect.md`, `rapid-prototyper.md` |
| QA | `evidence-collector.md`, `reality-checker.md` |

Read the relevant specialist file when executing that phase.

## References

Read these as needed:
- `references/state-schema.md`
- `references/file-templates.md`
- `references/phase-model.md`
- `references/runtime-model.md`
- `references/command-behavior.md`
- `references/cron-run-template.md`
- `references/start-stop-plumbing.md`
- `references/live-tool-orchestration.md` when performing real `/pap2 init|start|stop` actions with OpenClaw tools

## Quality bar

Keep PAP2 separate from legacy PAP.
Prefer deterministic file/state transitions over vague prose.
Do not start autopilot on inconsistent docs.
Keep user-facing summaries readable and short.
