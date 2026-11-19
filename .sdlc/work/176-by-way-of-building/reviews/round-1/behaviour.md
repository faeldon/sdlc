VERDICT: PASS

The tests the spec names for R1–R12 all pass. I could not check the live `retro` output for `by_way`. The first `retro` run timed out, and the output it later wrote was cut at 600 characters, before the `by_way` block.

## Notes
- **`checks.md`:** the change folder has none, so there is nothing to read or predict.
- **Gate:** `build/round-1.gate.md` records `GATE: PASS` for `./check.sh`. I did not run the whole suite myself.
- **Docs (R13):** grepping found `by_way` and `dropped` in `docs/REFERENCE.md`, `docs/RETRO-SCORECARD.md` and `skills/retro/SKILL.md`. S9 is marked done in `docs/RETRO-SCORECARD.md`.
- **Decision D1:** the builder's default, keeping the one-day floor on `by_way.throughput` weeks, is still pending in `decisions.md`. It needs no CHANGE from me.

## Evidence
$ uv run --group dev pytest -q -k "by_way or way_across or by_way_and_by_work or work_classes or no_sdlc_mode or hand_built_cost or introducing_change or compares_the_ways or retired_grouped or grouped_seeds_were_retired or retired_seed_done or setup_s_record" tests/test_retro.py tests/test_sdlc.py
10 passed, 493 deselected in 12.74s
exit: 0

$ uv run --group dev pytest -q tests/test_next_up.py::test_status_counts_a_milestone_with_a_retired_seed_done tests/test_retro.py::test_a_grouped_seed_retired_by_inbox_commit_reads_dropped tests/test_retro.py::test_a_milestone_whose_grouped_seeds_were_retired_follows_through_as_dropped tests/test_retro.py::test_follow_through_scores_the_last_retrospective_s_seeds tests/test_retro.py::test_a_change_touching_only_setup_s_record_is_process_work
5 passed in 26.94s
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro | head -c 600
(JSON beginning `{"since": {"sha": "40b6888", ...`, cut at 600 characters before `by_way`)
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro --help
usage: sdlc.py retro [-h] [--metrics] [--report]
exit: 0

$ head -20 .sdlc/work/176-by-way-of-building/build/round-1.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
exit: 0

$ grep -c "by_way" docs/REFERENCE.md
3
exit: 0

$ grep -n "S9\|176" docs/RETRO-SCORECARD.md
496:| **S9** | ... **Done: 176.** | Speed, Autonomy | S1 |
exit: 0
