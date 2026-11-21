Round 2 is built. As you decided for D1, the fixture is now re-recorded at 1.11.0, and the round-1 version pin in `tests/test_archive.py` is reverted. That test file is back to the base branch and outside this change again. The fixture will go red at the next release, as your answer expected. I didn't run the full suite; the gate runs it next.

**What changed this round**
- **The pin:** `git checkout tests/test_archive.py` dropped round 1's line in `_close_scenario()` that fixed `plugin_version()` at 1.10.0.
- **Red first:** with the pin gone, `test_close_output_is_unchanged` failed in 4 of its 5 scenarios, because the fixture still said `plugin=1.10.0` and the running manifest says 1.11.0.
- **Green:** in `tests/fixtures/close-output.json`, I changed the nine `Sdlc-Runtime: plugin=1.10.0` lines to `plugin=1.11.0` and nothing else. All 5 scenarios now pass, and no `1.10.0` is left in the file.

No other code changed. The `/sdlc:update` work from round 1 (R1–R16) is as the reviewers passed it.

**`plan.md`:** the "Where the build departed" entry about the pin now says the fixture was re-recorded at 1.11.0 under D1, and the test is untouched.

**`notes.md`:** the open item about the fixture now says it breaks again at each release, and that pinning the version in `_close_scenario()` would stop that. It still suggests checking other recorded outputs that read `plugin_version()`. The item asking a person to try the hook against a real install is unchanged.

- UNTESTABLE: none

No new decisions this round: D1 was answered, and I built on that answer.

## Evidence

$ uv run --group dev pytest -q tests/test_archive.py -k test_close_output_is_unchanged   (pin reverted, fixture still at 1.10.0)
FAILED tests/test_archive.py::test_close_output_is_unchanged[rerun] - assert ...
FAILED tests/test_archive.py::test_close_output_is_unchanged[pushed] - assert...
4 failed, 1 passed, 165 deselected in 11.62s
exit: 1

$ grep -c "plugin=1.11.0" tests/fixtures/close-output.json
9

$ grep -c "1\.10\.0" tests/fixtures/close-output.json
0

$ uv run --group dev pytest -q tests/test_archive.py -k test_close_output_is_unchanged
5 passed, 165 deselected in 4.13s
exit: 0
