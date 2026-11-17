---
id: 074
slug: factory-run-cost
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 074 — What a factory run cost, by role and model, while it runs · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `_claude()` returns the run's figures beside its reply;
  `cmd_agent()` appends them to `runs/costs.jsonl`; a new `run_cost(folder)` sums them;
  `cmd_ready()` and `cmd_stage(…, "test")` print the sum as `cost`.
- `plugins/factory/skills/build/SKILL.md`: Step 4's "ready to ship" report and the `ready` listing
  say the cost, labelled as the API-equivalent figure.
- `plugins/factory/README.md`: `runs/costs.jsonl` in "What it leaves in the change's folder".
- `tests/test_factory.py`: the fake `claude` reports figures; tests for recording, summing and
  output.

## Work order

1. A probe of `claude -p --output-format json` settled what's reported: on `--resume`, `usage` and
   `duration_ms` are the run's own, while `total_cost_usd` is the session's running total. So
   each line keeps the figures as reported, and summing takes a session's last cost and every
   run's tokens and duration.
2. `_claude()` returns `(code, reply, problem, figures)`, figures read from the JSON whenever it
   parses, failed runs included. Missing fields are `None`.
3. `cmd_agent()` appends `{"session", "role", "model", "cost_usd", "duration_ms", "turns", "in",
   "out", "cache_create", "cache_read"}` to `runs/costs.jsonl` after every run whose JSON parsed,
   before the reply is filed or refused. `runs/<agent>.sessions` is written exactly as today.
4. `run_cost(folder)`: `{"usd", "by_role", "by_model", "runs", "unknown", "tokens"}`, where `usd`
   sums each session's last `cost_usd` and `unknown` counts the sessions that reported none. A
   malformed line is skipped and counted in `unknown`, never raised.
5. `cmd_ready()` adds `cost` to each change; `cmd_stage()` adds it when the stage is `test`.
6. Skill and README text; `./check.sh`.

## Tests

- Recording: `agent` against the fake `claude` writes one line with the reported figures, the
  role and the model; `builder.sessions` keeps one id a line.
- Resume: a build then a mend of the same builder, reporting running totals 0.5 then 0.75, sums
  to 0.75, with tokens summed across both runs.
- Failure: a failed run's figures are still recorded, and nothing is filed.
- Unknown: a run whose JSON lacks `total_cost_usd` is counted in `unknown`, and the run files its
  reply as before.
- Output: `ready` and `stage … test` print `cost`, split by role and model.

## Rollback

`git revert <sha>`. `runs/costs.jsonl` files already committed with changes stay in history and
are read by nothing once reverted.
