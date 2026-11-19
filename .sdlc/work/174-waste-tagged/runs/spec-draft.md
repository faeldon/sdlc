---
id: 174
slug: waste-tagged
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 174 — The retrospective says what a change cost, and what was wasted · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Rows and records (`plugins/factory/scripts/factory.py`, `landing.py`):

1. **R1. Every row says what it was for.** Each row `record_cost()` appends to `runs/costs.jsonl` carries `purpose`, one of `PURPOSES = ("spec", "build", "rework", "gate-fix", "mend", "rerun", "land")`, and `task`. A loop task's row also carries `round` (the round `loop_state` named). A landing task's row also carries `land` (`land_round(folder)`, 0 allowed). The row is still numbers and names only. Test: `test_every_task_has_a_purpose` fails if any name in `TASKS` has no purpose, or maps to a word outside `PURPOSES`. `test_a_row_names_its_purpose_task_and_round` fails if a `cmd_agent` run (with `claude` faked) writes a row without these fields.
2. **R2. The purpose comes from the task and the round, fixed when the row is written.**
   - `spec` is `spec`, including `--revise` and `--recheck`.
   - `build`, `review`, `verify`, `decided` and `approve` are `build` in the run's first round (`first` as `run_state.loop_state` counts it, after a restart or an upgrade) and `rework` after it. `approve` is always `build`.
   - `rework` is `rework`. `fix` is `gate-fix`. `mend` and `land-mend` are `mend`.
   - `resolve`, `train-resolve`, `land-fix`, `land-review` and `land-verify` are `land`.

   Test: `test_purpose_by_task_and_round` uses a table of (task, role, round, first) → purpose, and fails on any mismatch.
3. **R3. A second run of the same step is a `rerun`.** A row is `rerun` when an earlier row in the same file has the same `task`, `role` and `round` (or `land`), and the task is one of `RERUNNABLE = ("build", "rework", "review", "verify", "approve", "mend", "land-review", "land-verify", "land-mend")`. A second `fix`, `decided`, `resolve`, `train-resolve` or `land-fix` in one round is real work and keeps its own purpose. Test: `test_a_second_run_of_a_step_is_a_rerun` fails if a repeated `review` for `code` in round 2 is tagged anything but `rerun`, or if a second `fix` in round 2 is.
4. **R4. An ejection leaves a durable record.** `train --eject` (`_train_eject()`) and `train --stop` (`_train_stop()`) each append one row to a new `runs/ejections.jsonl` (`EJECTIONS`, defined in `factory.py`) in each change they put back: `{"at": <_utc_now()>, "land": <land_round>, "cause": "gate"|"review"|"refusal"|"stop"}`. They write it before `_amend_record()`, so the record survives the `reset --keep` with the rest of the folder. No existing row of `costs.jsonl` is rewritten. Test: `test_an_ejection_is_recorded_and_amended_in` (in `tests/test_train.py`) fails if the file is missing from the ejected change's commit, or if `costs.jsonl` there differs from before the ejection.

Reading (`scripts/factory_records.py`, `scripts/retro.py`):

5. **R5. Per-row dollars come from the change between a session's running totals.** `factory_records.spend_rows(show)` reads `costs.jsonl` and `ejections.jsonl` through the caller's `show`. For each row it gives `usd`: the row's `cost_usd` minus the highest `cost_usd` an earlier row of the same session reported, floored at 0. `cost_usd` is a session's running total across `--resume` (`_figures()`). It also gives `minutes` (`duration_ms` / 60000), `role`, `model` and `part`. A row reporting no cost has `usd: null` and is counted in `unknown`; the next row that reports one carries its spend. Test: `test_row_dollars_sum_to_the_changes_cost` fails if a fixture's rows don't sum to `factory_records.cost(folder)["usd"]` (to 4 places). The fixture is a builder session resumed three times, one row without a cost, and two reviewers.
6. **R6. Each row lands in exactly one part.** The parts are `spec`, `build`, `land`, `rework`, `gate-fix`, `mend`, `rerun`, `ejected`, `dropped` and `untagged`. They are applied in this order:
   - a row with no `purpose` is `untagged`;
   - every row of a dropped change is `dropped`;
   - a row with a `land` value that ended (`ended`) at or before an ejection's `at` is `ejected`;
   - every other row takes its own purpose.

   `WASTE = ("rework", "gate-fix", "mend", "rerun", "ejected", "dropped")`. `untagged` is never waste. Test: `test_each_row_counts_in_one_part` fails if the parts' dollars don't sum to the total, or if an untagged row of a dropped change counts as waste.
7. **R7. `retro`'s JSON gains a `cost` block.** It is read from each closed change's own commit, and each dropped change's tip, through `_records_at()` and `factory_records.spend_rows()` only. It holds:
   - `per_change`: for each tier, `n`, `usd` `{median, total}` and `minutes` `{median, total}`, over the landed changes that have a cost.
   - `waste`: `usd`, `of_usd`, `share`, `minutes`, `of_minutes` and `minutes_share`, `n` (the changes it rests on, landed and dropped), and `parts`, each `{usd, minutes, runs}`. `share` is null when `of_usd` is 0.
   - `by_role` and `by_model`: each `{usd, minutes, runs, changes}`.
   - `unknown`: rows with no cost.
   - `untagged`: `{runs, usd, changes}`.
   - `changes`: each change's own rows, printed only with `--metrics`, as `spend.changes` is (`cmd_retro()`).

   Test: `test_retro_reports_cost_per_landed_change_and_waste` builds fixture runs in a scratch repo: a landed Tier 2 factory change with a rework round and a mend, a landed change ejected once and then landed, a dropped factory change, a hand-built change and an old change whose rows carry no `purpose`. It fails on any figure that differs from the values worked out by hand.
8. **R8. A change with no dollars is missing, never $0.** A closed change whose commit has no `costs.jsonl` rows, or whose rows report no `cost_usd`, is in no `per_change` figure. It is counted in `cost.coverage` / `missing_because` (`_coverage()`), under `built by hand` (no rows, and no `Sdlc-Mode: factory`), `no agent runs recorded` (factory, no rows) or `no cost reported`. Test: the hand-built fixture in R7's test fails it if it appears in `per_change` or adds 0 to a median.
9. **R9. The trust band says how far cost and waste rest.** `waste` carries its own coverage: a change is measured only when it has a cost and no untagged row, and the rest go under `runs recorded before purposes` or R8's reasons. The report's *Coverage* lines (`_coverage_lines()`) gain `cost per landed change` and `waste share`, greyed under half. Test: `test_the_report_says_how_far_cost_and_waste_rest` fails if either line is missing from `retro --report`, or doesn't name the untagged count.

Nits (`scripts/metrics.py`):

10. **R10. A URL's unquoted `&` is pinned as a background `&`** (nit 2026-11-19-16). `curl x?a=1&b=2` reads `bg=True` and `curl 'x?a=1&b=2'` reads `bg=False`. These cases are added to `test_a_command_ending_in_a_lone_ampersand_goes_to_the_background`'s table, with no code change.
11. **R11. `Sdlc-Runtime`'s values are capped at 64 characters each** (nit 2026-11-19-22). The cap is applied in `runtime_trailer()`'s `words()` after `_model_word()`, so the trailer's format is unchanged. Test: `test_runtime_values_are_capped` fails if a 200-character version or model yields a value over 64.

Docs:

12. **R12. The docs say it.**
    - `docs/REFERENCE.md` *Retrospectives* describes `cost`, its parts and the coverage reasons.
    - `plugins/factory/README.md`'s file list gains `runs/ejections.jsonl` and the row's new fields.
    - `docs/RETRO-SCORECARD.md`'s Cost statuses (headline, waste share, spend by role and model) become *captured (S4, 174)*, and its wave 3 marks S4 done.

    Checked by review. `./check.sh` covers the shape.

## Design

**What I took as given, checked in the code:**

- `cost_usd` is a session's running total, not a run's own figure. `_figures()` takes the last result's `total_cost_usd`, and `run_cost()` / `factory_records.cost()` sum each session's last total. So any split by purpose must use the change in the total, or the builder's resumed sessions would be counted several times.
- `duration_ms` is each run's own figure (summed over that call's results), so minutes add up directly.
- `record_cost()` is called once, in `cmd_agent()`, after `_claude()` returns. At that point the task, role, `state["round"]` and `land_round(folder)` are all known.
- `_put_back()` checks the folder out from the stacked commit after `reset --keep`, and the caller amends it in. So a file written in `runs/` before `_amend_record()` is kept on the change's branch.
- `land-step.md` is overwritten by the next landing, and an `eject` never reaches `land-times.jsonl` (`_record_land()` skips stops). No durable ejection record exists today, which is why R4 adds one.
- `dropped_changes()` records carry `name` and `sha` (the branch tip), so `_records_at()` reads a dropped change's folder as it reads a closed one's.
- `test_every_shared_name_is_the_factorys` pins any name `factory_records.py` shares with `factory.py`. So `PURPOSES`, `WASTE`, `RERUNNABLE` and `EJECTIONS`, defined in both, are pinned with no new pin test. They join `RECORD_NAMES`, and `ejections.jsonl` joins `RECORD_FILES`, so no other core file names the file (`test_no_factory_record_is_named_outside_its_reader`).

**Writing (factory).** `factory.py` gains these, beside `COSTS`:

- `PURPOSES`, `WASTE`, `RERUNNABLE` and `EJECTIONS`.
- `TASK_PURPOSE`, the task-to-purpose table for every task but those whose purpose depends on the round.
- `purpose_of(task, round, first, earlier_rows)`, a pure function implementing R2 and R3.

`cmd_agent()` works out the purpose before calling `claude`. It needs the run's first round, which `loop_state` already computes (`first`), so `run_state` adds `first` to its output. It reads the change's existing `costs.jsonl` rows to spot a rerun, then passes `purpose`, `task` and `round` or `land` to `record_cost()`, which gains those keyword arguments. Rows stay one JSON object a line, so the board (`timed_rows()`), close (`session_models()`) and `run_cost()` read them unchanged.

`landing.py` gets a helper, `_record_ejection(folder, cause)`. It is called from `_train_eject()` and `_train_stop()` right after `_record_land(..., "eject"|"stop", ...)`, and appends to `factory.EJECTIONS` with `newline="\n"` and `encoding="utf-8"`.

**Reading (core).** `factory_records.py` gains:

- copies of `PURPOSES`, `WASTE` and `EJECTIONS`;
- `spend_rows(show, dropped=False)`. It is pure and takes text through `show`. It returns `{"rows": [...], "unknown": n, "untagged": n}`, each row `{usd, minutes, role, model, part, session}`, with R5's deltas and R6's order of parts. It parses `costs.jsonl` the way `cost()` does, skipping lines that don't parse in the same way.

`retro.py` gains `_cost(home, changes, dropped)`, which builds R7's block using the existing `_coverage()` and `_share()`. `retro()` adds `"cost": _cost(...)`, and `cmd_retro()` drops `cost.changes` without `--metrics`. `render_report()` takes `cost` and passes it to `_coverage_lines()` for R9's two lines. Nothing else in the report changes: S14 lays out the scorecard. `templates/retro.md` is untouched, so `TEMPLATE_READS`, `drift` and `setup.json` don't move.

**Edge cases.**

- An empty or missing `costs.jsonl` gives no rows (R8).
- A session's total that falls gives a delta of 0 for that row (R5's floor). Then that change's parts sum to the session's highest total rather than `cost()`'s last one. The test pins it.
- A row with a `land` value but no `ended` is never `ejected`. It keeps its purpose, because the code can't place it.
- A change ejected twice sends both landing attempts' rows to `ejected`: each row compares against every ejection's `at`.
- A restart's earlier rounds keep the purposes they were written with. A restart isn't counted as waste here; it shows as an escalation in `autonomy`.

**Boundaries.**

- Always: rows are only appended, never rewritten. `retro` stays read-only. Every figure carries its `n`, and a figure with nothing to divide by is null.
- Ask first: changing which parts are waste (the open questions below), and putting these figures in the report's body.
- Never: a prompt or a reply in a row; a $0 for a change that reports no dollars; a new trailer or a change to the `Sdlc-*` format; a change to `run_cost()`, `factory.py ready` or the board's cost card.

## Contracts touched

- **Core reads a run's records only through `factory_records.py`, under `factory.py`'s names.** The new constants have the same names and values in both files, pinned by `test_every_shared_name_is_the_factorys`. `ejections.jsonl` is added to `RECORD_FILES`, so `retro.py` can't name it. `spend_rows` joins `RECORD_NAMES`. `factory.py` still never imports `sdlc.py`.
- **`metrics.py`, `indicators.py` and `factory_records.py` are pure.** `spend_rows` reads only through `show`, and runs no git.
- **Metrics' trailers are extended, never redefined.** No trailer is added. R11 bounds a value's length inside the existing `Sdlc-Runtime` format, and `test_runtime_trailer_round_trips` still passes.
- **`retro` writes nothing but its report**, and runs only the host's three commands. `_cost` reads git objects only.
- **A change's own numbers are printed only with `--metrics`.** `cost.changes` is dropped as `spend.changes` is, and every summary is built from the full rows first.
- **Agents that judge have no Write; no agent commits.** The new writes are the script's (`cmd_agent`, `_train_eject`, `_train_stop`), committed by the landing's existing `_amend_record()`.
- **The board writes nothing and reads `costs.jsonl` for step seconds.** Rows keep `session`, `role`, `model`, `started` and `ended` unchanged, and `test_board.py`'s `cost()`/`run_cost()` pin still holds.
- **The scripts run on Windows.** The new write passes `encoding="utf-8"` and `newline="\n"`, and the pure tests (R2, R3, R5, R6, R11) are marked `portable`.
- **Nothing local.** Fixture data uses neutral names (`reopen-drafts`).

No invariant needs to change.

## Alternatives rejected

- **Deriving every purpose in `retro` from the task and the run's later records, with nothing written.** `costs.jsonl` rows today don't name their task or round. Rebuilding them from `reviews/` and `build/` timestamps would be guessing, and a guess is the thing the trust band exists to flag. The run knows its task when it starts, so the purpose is written then, and only what happens later (an ejection or a drop) is derived.
- **Rewriting a row's purpose when its change is ejected or dropped.** The intent rules this out, and appended records are what close and the board rely on.
- **Splitting dollars by each row's own `cost_usd`.** That is a running total, so it would count a resumed builder session once per resume.
- **Recording an ejection in `land-step.md` or `land-times.jsonl`.** The first is overwritten by the next landing, and the second never records a stop, by design (`_record_land()`).
- **Counting a hand-built change's tokens as dollars.** That would be a price made up by the plugin. Hand-built changes are reported missing (the intent's constraint).
- **A `{{cost}}` section in `templates/retro.md` now.** It would be a template read change (`TEMPLATE_READS`, a breaking drift for hosts' overrides), and it is S14's job.
- **A `failed` flag on a row instead of `rerun`.** It would tag the run that bought nothing, which is accurate, but a person-started rerun after a `rerun` stop has no failed row. Tagging the second run covers both cases with one rule, and the waste share is the same either way.

## Verification

```bash
uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_train.py tests/test_retro.py \
  tests/test_metrics.py tests/test_modules.py tests/test_board.py   # every new test passes; none skipped
uv run --group dev pytest -q -m portable                            # the pure ones pass as on Windows
uv run --quiet --script scripts/sdlc.py retro | python -c 'import json,sys; c=json.load(sys.stdin)["cost"]; print(sorted(c), c["coverage"])'
# healthy: keys include per_change, waste, by_role, by_model, untagged, coverage; no "changes"
uv run --quiet --script scripts/sdlc.py retro --metrics | python -c 'import json,sys; print(len(json.load(sys.stdin)["cost"]["changes"]))'
# healthy: a count, with each change's rows present only here
uv run --quiet --script scripts/sdlc.py retro --report | grep -E 'Coverage, (cost per landed change|waste share)'
# healthy: two lines; in this repo the waste line names the untagged runs (every row before 174)
./check.sh                                                          # ruff, format, full suite, plugin validate: all green
```

