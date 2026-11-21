I rewrote outcome 4 (R4) so it can be checked inside the build, and made the workflow test read `*.yaml` files as well as `*.yml`. The change's tests pass (3 of 3), as does the acceptance check. I didn't run the full gate myself. The script runs it next and records the result in `build/round-2.gate.md`.

**Answering decision-1 / R1 (the person's answer in the ledger):**
- **R4 rewritten.** In `intent.md`, "CI is green on the change's commit" now reads: both of `check.yml`'s actions are SHA-pinned, `tests/test_ci.py` passes (reading `.yml` and `.yaml` workflows alike, since GitHub runs both), and the gate is green. The CI run on the pushed commit is now something to look at after ship, not a requirement of the build.
- **`*.yaml` too.** `tests/test_ci.py` has a new `workflow_files(folder)` that returns every `.yml` and `.yaml` file in sorted order. `test_every_action_is_pinned_to_a_commit` uses it instead of `glob("*.yml")`.

**Slice built (test first):**
- **New test:** `test_a_yaml_workflow_is_read_as_well` writes `a.yml`, `b.yaml` and `notes.md` into a temp folder and checks that only the first two are picked up.
- **Red:** I ran it before adding the function and it failed with `NameError`, as expected. So did the existing pin test once it called the missing function.
- **Green:** after adding `workflow_files()`, all 3 tests passed, and ruff check and ruff format are clean on the file.

**`plan.md` changes:** the file list now says `*.yml` and `*.yaml`, and the tests section lists the new test and the rewritten outcome 4, with the post-ship CI observation marked as not proved here.

**`notes.md`:** none written.

**Not done:** two low-severity reviewer notes from round 1 remain. `USES` doesn't match a quoted `uses: "a/b@v4"`, and `VERSION` requires `v` plus digits. Decision-1 didn't ask for either, and the security reviewer judged that a line the test can't read as a pin counts as a failure, so the test fails safe.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_ci.py   (before `workflow_files` existed)
FAILED tests/test_ci.py::test_a_yaml_workflow_is_read_as_well - NameError: na...
FAILED tests/test_ci.py::test_every_action_is_pinned_to_a_commit - NameError:...
2 failed, 1 passed in 18.47s
exit: 1

$ uv run --group dev pytest -q tests/test_ci.py
3 passed in 0.02s
exit: 0

$ uv run --group dev ruff check tests/test_ci.py && uv run --group dev ruff format --check tests/test_ci.py
All checks passed!
1 file already formatted
exit: 0

$ grep -n "uses:" .github/workflows/check.yml
24:      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
25:      - uses: astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0
39:      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
40:      - uses: astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0
exit: 0

$ uv run --group dev pytest -q tests/test_ci.py
3 passed in 0.39s
exit: 0

$ grep -q '^version: 2$' .github/dependabot.yml && grep -q 'package-ecosystem: github-actions' .github/dependabot.yml && grep -q 'directory: /$' .github/dependabot.yml
exit: 0
