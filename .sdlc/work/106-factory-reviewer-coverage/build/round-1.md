I've built all 14 requirements, left uncommitted. The full gate passes with 2006 tests, and the change's one acceptance check passes. One requirement couldn't be met as written: R2 said the existing light-depth tests would stay unchanged, but they build a Tier 2 change. Two of them had to move to Tier 1, which is the first decision below.

**What I built, in five slices:**
1. **Test reviewer at the light depth (R1–R8).** With `[light] reviewers` unset, a Tier 2 change's light rounds now expect `code` and `test`, but only when the full depth also runs `test`. A Tier 1, or a change whose tier can't be read, keeps `code` alone. A list the host set is used as written at both tiers. The tier only changes which reviewers the light depth expects, never which depth a run gets, so a Tier 2's own `test` review can't make a run full. `start` reports the reviewers for the change's tier, so the run's one question names `code, test` for a Tier 2.
2. **New `[ui] fixture` key (R9, R11).** It must be a path inside the checkout; a non-string, absolute, drive or `..` path gives a warning and is ignored. A `serve` that names `{fixture}` with no fixture set is a config warning.
3. **Screenshots serve a fresh copy (R10, R11).** Before each shot, the fixture is copied fresh under `.sdlc/reports/shots/<change>/<label>/fixture/`, and `{fixture}` is filled with that copy's relative path. A fixture the checkout lacks blocks the UI review and starts no server. With `fixture` unset, `serve` runs exactly as before.
4. **The board fixture (R12, R13).** `tests/fixtures/board/` has 11 neutral changes (`001-draft-labels` … `011-draft-preview`), plus `build.sh` and `serve.sh`. `.sdlc/factory.toml` now serves it and counts `tests/fixtures/board/` as a UI path. I ran the real `shots()` with this repo's `[ui]` and looked at both screenshots: all seven columns, the step track, `was ESCALATE`, and the green and red gate badges all show.
5. **Docs (R14).** The factory README and the build skill describe `fixture` and the Tier 2 light default.

**Tests added:**
- `test_a_tier_2_light_round_includes_the_test_reviewer` (R1, R2, R3, R7)
- `test_a_set_light_list_is_kept_at_either_tier` (R4, R5)
- `test_the_test_reviewer_never_deepens_a_tier_2_light_run` (R6)
- `test_the_landing_review_judges_a_tier_2_light_run_with_its_test_reviewer` (R8)
- `test_ui_fixture_is_checked_like_the_other_keys` (R9)
- `test_shots_serve_a_fresh_copy_of_the_fixture` (R10)
- `test_a_missing_fixture_refuses_the_ui_review` (R11)
- `test_the_board_fixture_shows_every_card_state` (R13, in `test_board.py`)

I saw each one fail for the expected reason before it passed. R12 is proved by an acceptance check in `checks.md` instead of a test.

**Existing tests I edited:**
- `test_a_diff_touching_no_sensitive_path_runs_light` and `test_the_ui_reviewers_join_on_a_ui_path_at_either_depth` now build a Tier 1 change.
- The two config tests expect the new `light.chosen` key.
- `test_a_ui_review_never_runs_blind` no longer writes a TOML `null` for an unset key.

**`plan.md`:** written before any code. It now has an "As built" section for where the build departed from the spec's design:
- `build.sh` takes the data and the target as separate arguments.
- The scratch repo is built inside the copy, so replacing the copy clears it.
- Which changes get a hand gate, and whether it passes, is data in `changes/gates`.
- The step record has no `SINCE:` line, so the card doesn't show a time that grows as the fixture ages.

**Left in `notes.md`:**
- The build skill's summary of `ui` doesn't mention `fixture` yet.
- The board fixture test takes about 30s on a cold `uv` cache.

`.sdlc/work/inbox.md` was already modified before I started; I didn't touch it.

- DECISION: [default] Spec R2 said `test_a_diff_touching_no_sensitive_path_runs_light` would stay unchanged, but it builds a Tier 2 change, as does `test_the_ui_reviewers_join_on_a_ui_path_at_either_depth`. Under R1 both now expect `test`. Options: move them to Tier 1; or keep them at Tier 2 and expect `["code", "test"]`. Going ahead with Tier 1: what they test is today's light run, which R2 keeps for Tier 1, and R1's new test covers Tier 2.
- DECISION: [default] A `[light] reviewers` with no known reviewer falls back to the default, so it is not treated as set (`chosen: false`), and a Tier 2 still gets `test`. Going ahead with that unless told otherwise.
- DECISION: [default] A fixture that is a single file is copied into `fixture/` under its own name, and `{fixture}` names the file. Going ahead with that unless told otherwise.

## Evidence

```
$ uv run --group dev pytest tests/test_factory.py -q -k "light or tier or fixture or shots or depth"
31 passed, 134 deselected in 4.85s
exit: 0

$ uv run --group dev pytest tests/test_board.py -q -k fixture
1 passed, 48 deselected in 1.39s
exit: 0

$ uv run --group dev pytest tests/test_skills.py -q -k depths
1 passed, 343 deselected in 0.04s
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 106
  "passed": true,
exit: 0

$ ./check.sh
All checks passed!
248 files already formatted
2006 passed in 44.23s
✔ Validation passed
✔ Validation passed
exit: 0
```
