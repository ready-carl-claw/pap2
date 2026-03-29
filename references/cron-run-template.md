# PAP2 cron run template

```text
You are executing one PAP2 cron cycle for project `{{PROJECT_NAME}}` at `{{PROJECT_ROOT}}`.

Core rules:
- First, use the deterministic helper: `python3 scripts/pap2.py acquire-run --project-root "{{PROJECT_ROOT}}" --require-autopilot-enabled`
- If acquire-run reports skipped because a healthy run is already active, stop immediately without producing extra output.
- Respect the current/next run type recorded in `.pap.json`.
- PAP2 tick = {{TICK_MINUTES}} minutes.
- Soft execution budget = {{EXECUTION_MINUTES}} minutes.
- Stale threshold = {{STALE_MINUTES}} minutes.

Read order:
1. `User-Steer.md`
2. `.pap.json`
3. `PRD.md`
4. `Spec.md`
5. `Plan.md`
6. `TODO.md`
7. `progress.md`
8. `Lessons.md` when relevant

Steering-first rule:
- If there is an unfinished numbered steer in `User-Steer.md`, classify it before normal execution.
- product-level steer -> update `PRD.md`, then `Spec.md`, then `Plan.md`, mark steer `[Done]`, finish run, exit
- design-level steer -> update `Spec.md`, then `Plan.md`, mark steer `[Done]`, finish run, exit
- planning-level steer -> update `Plan.md`, mark steer `[Done]`, finish run, exit
- task-level steer -> update `TODO.md`, do Build work, mark steer `[Done]`, finish run, exit

Run-type rule:
- `build` run: maintain TODO, work `build`/`fix` tasks, do internal validation, update `progress.md`, write `Lessons.md` when meaningful, generate QA-facing `test` tasks when appropriate
- `qa` run: only consume `test` tasks, read PRD/Spec/Plan for context, strengthen weak test definitions if needed, create `BugRepro.md` + convert to `fix` on failure
- `plan` run: revise `Plan.md` from PRD+Spec and recent reality, then finish and exit
- `design` run: read PRD + Lessons, revise `Spec.md`, then update `Plan.md`, then finish and exit

Summary rule:
- After the run, append a short user-facing summary to `summary.md`
- Never read `summary.md` as an input
- If summary routing is configured, send the same summary to the configured channel

Before exiting:
- Persist the next run type when needed
- Use `python3 scripts/pap2.py finish-run ...` to clear runtime flags, update counters, and append summary.md
- **CRITICAL SAFETY RULE**: If you are blocked on user feedback, blocked on an external issue, or find no meaningful tasks to work on, you MUST pass `--idle` to the `finish-run` command. After 10 consecutive idle cycles, PAP2 will shut down autopilot to prevent token burn.
- If `finish-run` outputs `"instruction": "CRON_MUST_SHUTDOWN"`, you MUST disable your own cron job via the OpenClaw `cron` tool (`action="update"`, `jobId` from the `cronJobId` field in `.pap.json`, `patch={"enabled": false}`), then exit.
```
