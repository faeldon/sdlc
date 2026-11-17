---
id: 074
slug: factory-run-cost
tier: 1
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-9
depends_on:
serves: [O5]
---

# 074 — What a factory run cost, by role and model, while it runs

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A factory run's cost is invisible until it's over. `/sdlc-factory:build`'s gate shows `max_runs`,
which counts agent runs, not what they cost. The supervisor's "ready to ship" line and
`factory.py ready` say nothing about cost. The first real figure is close's `measure` step, which
reads Claude Code's transcripts after the change has landed and records `Sdlc-Totals` on the
`Close` commit. By then the spend is history. With several changes in the supervisor at once, the
person can't tell which change, role or model is taking the tokens. They can't tell either whether
a reviewer at full depth or a builder stuck in rework is the one to rein in through
`.sdlc/factory.toml`'s `[models]` or `rounds`.

The data is already there and thrown away. `factory.py agent` (`cmd_agent()`) starts every agent
as `claude -p … --output-format json`, and `_claude()` parses that JSON for `result` alone. The
same object carries the session's cost, duration and token counts.

## Outcome

- Each agent run's cost, duration and token counts are kept in the change's `runs/`, beside its
  session id, with the role and model: numbers and names only, no prompt or reply text.
- `factory.py ready` gives each ready change its total and its split by role and by model, and the
  supervisor's "ready to ship" line says the total.
- The figure is labelled as the API-equivalent cost, as Claude Code reports it, so on a
  subscription it reads as where the spend goes, not a bill. The plugin carries no price table.
- A test runs `cmd_agent()` against a fake `claude` printing a known JSON object, and asserts what
  `runs/` records and what `ready` sums.
- **Moves O5:** a person running the factory can see, before shipping, which role and model a
  change's tokens went to, and trim `factory.toml` from that rather than from close's totals after
  the fact.

## Affected

- **Area:** the factory plugin's mechanism and its build skill.
- **Files & components:** `plugins/factory/scripts/factory.py` (`_claude()`, `cmd_agent()`,
  `cmd_ready()`), `plugins/factory/skills/build/SKILL.md` (Step 4's "ready to ship" line and the
  `ready` listing), `plugins/factory/README.md` (what `runs/` holds), the factory's tests.
- **Downstream:** the person running the supervisor, who reads the new figures. `sdlc.py`'s
  `_agent_sessions()` reads `runs/*.sessions` on the change's branch at close; whatever this writes
  must not change what it reads. Ship commits `runs/` with the change, so history keeps the
  figures.
- **Contracts:** the trailer format and close's measuring stay as they are: close's `Sdlc-*` lines
  remain the record history keeps, and this adds nothing to them. `sdlc` never reads the factory's
  new file unless a later change says so.

## Constraints

- `runs/<role>.sessions` keeps its format, one session id per line, which `_agent_sessions()`
  reads.
- No price table and no computed cost: only the figures Claude Code's JSON reports, passed through.
- A missing or unparseable cost field never fails a run. The run files its reply as today, and the
  figure reads as unknown.
- Windows rules hold: `newline="\n"` on every write, `encoding="utf-8"`.
- 073-factory-script-gate is also editing `cmd_agent()`, and whichever change lands second rebases
  over the other.

## Open questions

- ~~Where the figures live: a new `runs/<role>.costs` file, one line per session, or a single
  `runs/costs.jsonl`?~~ Resolved: `runs/costs.jsonl`, one JSON object per agent run, beside the
  `.sessions` files, which keep their format.
- ~~Which JSON fields to keep, and whether a renamed field should be read under both names?~~
  Resolved: `total_cost_usd`, `duration_ms`, `num_turns` and `usage`'s four token counts, under
  their current names; a missing one reads as unknown. A probe of a fresh and a resumed
  `claude -p` session showed `total_cost_usd` is the session's running total on a `--resume`,
  while `usage` and `duration_ms` are the run's own, so a session counts once, at its last cost.
- ~~Should the build skill's gate also show a running total for changes already in the
  supervisor, or only `ready` and the "ready to ship" line?~~ Resolved: only `ready` and the
  hand-back's report, from `stage <NNN> test`'s output, which needs no new command or rule.
- ~~Should close's `measure` later cross-check these against the transcripts' numbers?~~
  Resolved: out of scope here; a seed only if a real run shows they disagree.

## Approach

In `_claude()`, return the parsed JSON's cost, duration and usage fields alongside the reply. In
`cmd_agent()`, append one line per run to the change's `runs/` (the file decided in plan mode)
with the session id, role, model and those numbers, written even when the run's reply fails to
file. In `cmd_ready()`, sum each ready change's lines into `cost: {total, by_role, by_model}`.
Change the build skill's Step 4 to say the total in the "ready to ship" line, and document the
file in the factory README's "What it leaves in the change's folder". Tests use a fake `claude`
and pin that `.sessions` is unchanged. Run `./check.sh`.
