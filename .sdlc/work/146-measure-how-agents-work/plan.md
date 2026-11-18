---
id: 146
slug: measure-how-agents-work
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 146 — Measure how factory agents work, not only how long · plan

> Written by the builder after reading `scripts/metrics.py`, `measure_change()` in
> `scripts/sdlc.py`, `_spend()`/`_spend_text()`/`cmd_retro()` in `scripts/retro.py`, and the
> fixtures in `tests/test_metrics.py`, `tests/test_archive.py` and `tests/test_retro.py`.

## Files to change

- `scripts/metrics.py`: `_segments()` pulled out of `_prompt_name()` (same output); new pure
  `_shell(command, check)` → `(writes, bg, test)`, `_model_word()`, `TEST_RUNNERS`, `BROKE_RE`;
  `_behaviour()`, the per-entry counter `_run()` calls inside its one loop (under a `try`);
  `_run()` and `_subagent()` take `check` and `model`; `read_events(..., models=None)`;
  `summarize()` folds `behaviour`, `calls` and `model` into `roles` (or `behaviour=failed`);
  `trailers()` adds `model=`, the six counts and `Sdlc-Calls`; `parse_trailers()` reads
  `Sdlc-Calls` into `calls`. Docstring: the extended contract (R16).
- `scripts/sdlc.py`: `measure_change()` reads `runs/costs.jsonl` from the branch (`_agent_models()`,
  beside `_agent_sessions()`), passes `models=`.
- `scripts/retro.py`: `_agents(changes)`; `_spend()` sets `spend["agents"]`; `_spend_text()` adds
  the "Agents by role and model" table; `cmd_retro()` drops `spend.agents.changes` without
  `--metrics`.
- `docs/REFERENCE.md` *Metrics*: one paragraph on the new fields (R16).
- `tests/test_metrics.py`: R1–R8, R10–R12.
- `tests/test_archive.py`: R9 (needs a git repo with a factory change's branch, which its
  `_factory_shipped()` fixture builds; `test_metrics.py` loads `metrics.py` alone), and the
  `costs.jsonl` → `model=` path end to end.
- `tests/test_retro.py`: R13–R15.

Reused, not re-derived: `_prompt_name()`/`_word()` for names, `_entry_text()` for a result's text,
`HAND_GATE_RE` and the check-prefix rule `read_events()` already uses for `check` events,
`EDIT_TOOLS`, `_close(..., trailers=)` in the retro tests, `sdlc._lean()`'s rule.

## Work order

1. **Shell shapes.** `_segments()` extracted (existing `_prompt_name` tests stay green), `_shell()`
   with its parametrised tests (R3, R4's `&`, R5).
2. **Counting in `_run()`.** `_behaviour()` per entry; the `subagent` event gains `behaviour`,
   `calls`, `model`; `summarize()` and `trailers()` write them; `parse_trailers()` reads
   `Sdlc-Calls`. Tests R1, R2, R4 (result shape), R6, R7, R8 (with `models=`), R10, R11, R12.
3. **`measure_change()` reads `costs.jsonl`.** R9 test (one read per transcript) plus `model=`
   on the close's trailer, in `tests/test_archive.py`.
4. **Retro.** `_agents()`, the table, `--metrics` lean. Tests R13–R15.
5. **Docs.** metrics docstring and REFERENCE.md (R16).

## Tests

- R1 `test_a_role_s_behaviours_are_counted_from_its_transcript`; R2 inside it (plus an
  interrupted call).
- R3 `test_a_shell_edit_is_known_by_its_command` (parametrised).
- R4 `test_a_backgrounded_command_is_known_by_its_result`.
- R5 `test_a_test_run_is_known_by_its_program`.
- R6 `test_a_broken_build_is_a_failed_parse_after_an_edit`.
- R7 `test_a_role_s_tools_are_listed_by_name`.
- R8 `test_a_role_s_model_comes_from_its_costs`.
- R9 `test_measuring_reads_each_transcript_once` (`tests/test_archive.py`).
- R10 `test_a_behaviour_count_that_fails_drops_only_its_fields` (monkeypatches `_behaviour`).
- R11 `test_behaviour_trailers_carry_no_text`.
- R12 `test_a_close_from_before_behaviours_parses_as_before`.
- R13 `test_retro_compares_agents_by_model`; R14 `test_retro_leaves_agents_from_before_behaviours_out`;
  R15 `test_retro_prints_a_change_s_agent_counts_only_with_metrics`.
- R16: review only, as the spec says.

## As built

- `measure_change()` passes `models` to `read_events()` positionally, not by keyword: a stand-in
  that takes `*_` (`test_a_reader_that_fails_never_stops_the_close`) keeps working.
- `test_retro_prints_each_change_s_numbers_only_when_asked` now also pops
  `spend.agents.changes` from the `--metrics` output: R15 makes that the one other difference.
- R2's interrupted call and R4's `&` are each covered both by `_shell()`'s own parametrised
  test and by the transcript fixtures.

## Rollback

`git revert` undoes it all. What it doesn't: `Close` commits made while it was in, which carry the
new fields. They stay in history and stay readable: an older `parse_trailers()` reads
`Sdlc-Calls` as an unnamed key and the new role fields as plain values, and retro before this
change ignores both. Nothing is written outside the repo.
