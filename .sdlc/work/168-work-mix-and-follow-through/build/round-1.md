I've built all 14 requirements of 168 and left them uncommitted. HEAD is still `09e3a63`. I re-ran every command my claims rest on, and they are all below with their exit codes. The full gate passes: 3087 passed, 28 skipped.

**Slices built**
1. **The three nits (R11–R13), in `scripts/metrics.py`:**
   - `bg` now counts a lone `&` anywhere outside quotes and heredoc bodies. `&&`, `>&`, `<&`, `&>`, `|&` and `\&` don't count.
   - `_program()` now reads `uvx` and `npx` commands from the first word that isn't a flag.
   - `HAND_GATE_RE` accepts a quote after `.py`, as `FACTORY_CHECK_RE` already did.
   - The module docstring says what `bg=` counts, and that before 168 it counted less.
2. **`fixes` on closed records (R4):** `_change_record()` in `scripts/sdlc.py` reads the `fixes:` line as text.
3. **Work mix (R1–R3), in `scripts/retro.py`:** `_register_at()` is factored out of `_none_themes()`. New: `WORK_CLASSES`, `DEBT_THEMES`, `_is_process()`, `_work_class()` and `_work_mix()`. Each closed change's record now carries `work`.
4. **Time to users (R5, R6):** `_tag_times()` and `_time_to_users()`.
5. **Follow-through (R7–R9):** `_seed_follow()`, `_milestone_follow()`, `_retired_ids()` and `_follow_through()`.
6. **The report (R10):** `value_band()` is the one function both `retro()` and `retro_report()` call. `render_report(value=)` adds three sentences under `## Window`. The template is unchanged.
7. **Docs (R14):** a paragraph in `docs/REFERENCE.md` *Retrospectives*, a bullet in Step 0 of `skills/retro/SKILL.md`, and S2, S12 and S13 marked captured in `docs/RETRO-SCORECARD.md`.

**Tests added**, each seen failing for the expected reason before its code was written (those first runs aren't re-run below):
- **`tests/test_retro.py`:** every test R1–R10 names. Two more cover R2's null shares and R10's caller with no figures: `test_work_mix_shares_are_null_with_nothing_classed` and `test_without_a_value_band_the_window_is_as_before`. `test_retro_and_its_report_show_the_same_figures` is extended to compare the report with the JSON.
- **R3's test** also failed while `_unquote` was stubbed out, so it does exercise the non-ASCII path.
- **`tests/test_metrics.py`:** the R11–R13 cases.

**`plan.md`** now lists the two extra tests, puts R4's test in `test_retro.py`, and records that the scorecard's wave lists were left alone.

**`notes.md`** holds two unticked items:
- The scorecard still lists throughput "by impact" as needing S2; breaking throughput down by work class is a later change.
- A milestone's seed retired with `inbox-commit` reads `vanished` in `_milestone_verdicts()`, so the milestone reads `carried`. Scored as a seed, the same entry reads `dropped`. Changing that would change `direction.milestones`, which the spec says to ask about first.

Run against this repo's own history, the report's three sentences are consistent: 14 + 0 changes classed, 0 + 14 released, and the working tree is unchanged.

## Evidence

$ uv run --group dev pytest -q -n auto tests/test_retro.py tests/test_metrics.py
354 passed in 26.37s
exit: 0

$ uv run --group dev ruff check scripts tests
All checks passed!
exit: 0

$ uv run --group dev ruff format --check scripts tests
101 files already formatted
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro --report
Work mix: debt 8 (57%), fix 2 (14%), capability 2 (14%), process 2 (14%), of 14 classed changes; 0 not classed.
Time to users: no change in the window was released; 14 not yet released. 0 releases in the window.
Follow-through on the retrospective of 2026-11-18: 5 of 11 done or dropped (45%), seeds 1 of 6 and milestones 4 of 5; intent titles aren't recorded.
exit: 0

$ git status --porcelain
 M docs/REFERENCE.md
 M docs/RETRO-SCORECARD.md
 M scripts/metrics.py
 M scripts/retro.py
 M scripts/sdlc.py
 M skills/retro/SKILL.md
 M tests/test_metrics.py
 M tests/test_retro.py
?? .sdlc/work/168-work-mix-and-follow-through/

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 168
All checks passed!
311 files already formatted
3087 passed, 28 skipped in 132.14s (0:02:12)
✔ Validation passed
exit: 0
