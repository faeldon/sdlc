VERDICT: PASS

Every requirement has a test that would fail without it. The gate record shows a green run (`4042 passed, 29 skipped`). I found nothing that blocks the change.

## Notes

How each requirement is covered:

- **R1 and R2:** `test_autopilot_run_lands_a_seed_through_real_subprocesses` runs `autopilot --begin` and `--run` as real children, with nothing patched. It asserts the `landed` place, `Close` on the first-parent line, `Sdlc-Landed: by=autopilot`, `opened_by: autopilot`, and `→ decided by autopilot:` with no ` → decided: `. It also asserts at least two check environments with `PATH=` and no marker, and that no agent session logged a marker. `test_fake_claudes_marker_names_are_the_factorys` pins the fake's hard-coded marker names. If the loop dropped the markers from a child, the real `land --by autopilot` would be refused and the run would not land.
- **R3:** The `take_markers` test has both-set and neither-set cases and is marked `portable`.
- **R4:** The refused half now goes through `_claude()` and the stand-in. It asserts `BY_AUTOPILOT_REFUSED` in the output. The test would fail if `_claude()` stopped passing `agent_env()`.
- **R5:** `InFlight` flags any `answer` or `decisions` that starts beside another command of the same change, and any other command that starts while one is running. The test uses two seeds with three review roles each. It asserts that `answer` ran at least three times and that six roles ran.
- **R6:** The refused-agent test is in `test_land.py` and runs `land-fix`, so the session is resumed. It would fail on the old order, because `land-step.md` would already exist. Its sessions-file check only proves the file is unchanged for a resumed task. The fresh-session case, where the reorder also moves the append, is not tested.
- **R7:** The test pins two reads, not the spec's one. The plan raised this as a default and it is documented in the docstring. This is acceptable.
- **R8:** The four parametrized cases cover a backtick fence, a tilde fence, a fence that never closes, and the line after a closed fence. Each would fail with the old `BUILT_RE` scan. The `hold_causes` test also checks that the same line outside the fence clears the hold.

I re-ran 8 named tests in the foreground, covering R1 to R8: `uv run --group dev pytest -q tests/test_autopilot.py -k "real_subprocesses or take_markers or real_step or ledger_writer or fenced_built or reads_the_closes or marker_names" tests/test_land.py::test_an_agent_refused_on_its_closes_leaves_nothing_recorded`. All 8 passed in about 63 seconds. `checks.md` does not exist, so there are no acceptance checks to review.

- NIT: tests/test_land.py:2780: the refused-agent test only exercises a resumed task, so "the sessions file is as it was" holds trivially; seed a fresh task with no sessions file and assert it is not created {tests S S med}
