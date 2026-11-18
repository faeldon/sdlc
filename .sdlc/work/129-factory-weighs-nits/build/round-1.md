I've built change 129 (all six slices, R1–R13) and left it uncommitted. The full gate passes: 2351 passed, 13 skipped, plugin validation passes, and `HEAD` is still `6d8905f`.

**What changed in behaviour**
- **Reviewers weigh their nits (R1).** The code, security and test reviewers now end each `- NIT:` with `{<theme> <cost> <value>}`, using the process doc's rubric. The script takes the weights off the text. A line without weights, or with words the rubric doesn't have (e.g. `XL`), stays unweighed.
- **The script decides what happens to each nit, never a model (R2, R3, R5–R7).**
  - `S` + `med` is handed to a rework that runs anyway. It ends `fixed` only if a later round by the same reviewer doesn't raise it again; otherwise it is `recorded` and filed.
  - Any other `S`/`M` with `med`/`low` is `recorded` and filed at landing. Its `findings.md` section gets `Theme:`, `Cost:` and `Value:` lines.
  - `high` value becomes an `important` finding and `L` cost an idea; both are carried to `notes.md` for the approver.
  - A nit with no weights stays `minor`, as before.
  - A nit naming no path is `minor` ("names no path"), and filing stops at 5 per change; the rest are `minor` ("past the cap of 5 nits a change files").
  - No agent finding ends up `fix` or `open` in `findings.md`, so `sdlc.py ship` won't refuse because of one.
- **Hand-off to the builder (R4).** The rework prompt lists the round's cheap nits after the kept changes. The next round's review tells each reviewer which of its nits were handed on, and to raise again any the rework didn't make. A round with only nits goes to `approve`, never `rework`. A restart's or upgrade's first round is handed nothing.
- **Landing (R8–R11).**
  - `land-check` shows a `nits` part per change and adds the signal `nits to file: <n>[, <m> past the cap of 5]`, so `land --by auto` refuses.
  - The question gains the clause `its agents' nits filed as shown`.
  - On the person's yes, each nit is filed as a `[nit]` entry, with ids from the same single `next-entry` call as seeds and bugs. `land` returns them as `filed_nits`.
  - A rerun files nothing twice: a nit counts as already filed only when its `Raised by:` names the change and the entry holds its text, never by title alone.
- **Words (R12, R13).** Ship's `factory.md` now proposes a hand-shipped factory change's weighed nits as `[nit]` entries. The land skill (text and description), the factory README, `docs/REFERENCE.md`, the `nits` row in `guide/review.md`, the register table in `guide/process.md` and `templates/inbox.md` are updated. `.sdlc/setup.json` is re-recorded and `sdlc.py drift` reports nothing.

**Tests added**
- **Weights:** `test_a_nit_is_read_with_its_weights`, and `test_the_nit_words_are_sdlcs`, which pins the copied cost and value words to `sdlc.py`'s.
- **Dispositions:**
  - `test_carry_disposes_each_nit_by_its_weights`
  - `test_carry_never_leaves_a_fix_for_ship_to_refuse`
  - `test_a_nit_not_raised_again_is_still_filed`
  - `test_carry_caps_the_nits_it_files_at_five`
  - `test_carry_writes_each_agent_finding_once_by_its_role`, extended to check the weight lines
- **Hand-off:** `test_rework_hands_the_builder_its_cheap_nits`, `test_a_round_with_only_nits_is_never_reworked`.
- **Landing:**
  - `test_land_check_shows_the_nits_it_would_file`
  - `test_land_question_names_the_nits`
  - `test_nits_to_file_keep_the_gate_the_persons`
  - `test_a_landing_files_the_nits_sdlc_reads`, which checks `sdlc.nit_entries()` reads the entry back with no problem and the ids differ from the seed's and the bug's
  - `test_a_landing_rerun_files_each_nit_once`
- **Text:** `test_ship_files_the_agents_recorded_nits` (also covers the land skill's text) and `test_the_factory_reviewers_weigh_their_nits`.
- **`checks.md`:** one acceptance check for the guide and template wording, which only a revert could break. It passes under `sdlc.py accept`.

Each test was run and seen failing before its code went in.

**Where the build differs from the spec**
- `_dispose()` now returns `(filed ids, why)` so `cmd_land()` can report the ids.
- `land_parts()` takes `root`/`cfg` as optional arguments, so existing tests that call it on a folder outside any repo still work (they get an empty `nits`).
- Filed nits store `Paths:` as the path alone, without the line number.

All three are written into `plan.md`. Nothing was left in `notes.md`.

**Decisions:**
- DECISION: [default] Only a nit that will be filed gets `Theme:`/`Cost:`/`Value:` lines in `findings.md`; `L` and `high` nits, which are also `recorded`, get a `Reason:` instead. Options: lines on filed nits only; lines on every recorded nit. Recommend filed only: ship's side file proposes any section with those lines as a `[nit]`, which would wrongly file an `L` or `high` one. Going ahead unless told otherwise.
- DECISION: [default] A cheap nit counts as handed when its round kept a change and the next round's build isn't a restart's or upgrade's first round, including the case where a blocking decision's answer built that round instead of the rework. Options: count it as handed; don't. Recommend counting it: that build stands in for the rework, and its reviewer is still asked to raise the nit again. Going ahead unless told otherwise.

## Evidence

$ ./check.sh 2>&1 | grep -E "passed|failed|All checks|already formatted"
All checks passed!
249 files already formatted
2351 passed, 13 skipped in 157.29s (0:02:37)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_land.py tests/test_skills.py -k "nit or carry or rework or landing_commits"
70 passed in 9.96s
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py -k "nit"   (before the slice 1 code)
3 failed, 252 deselected in 1.11s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py -k "agents_recorded_nits or weigh_their_nits"   (before the docs)
2 failed, 354 deselected in 0.18s
exit: 1

$ uv run --quiet --script scripts/sdlc.py drift
{'base': 'manifest', 'version': 2, 'breaking': 0, 'refresh': 0, 'report': 0, 'docs': 3}
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 129
"passed": true,
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
exit: 0

$ git rev-parse --short HEAD
6d8905f
