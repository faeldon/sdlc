The setup nudge now clears when a release changed nothing under a repo's setup, and the startup hook says it at session start when there's no release line to say instead. All 11 requirements are built, nothing is committed, and the full gate passed: 3686 tests passed, 29 skipped, exit 0.

**What changed:**
- **The nudge asks drift (R1–R5, R9).** A new `drift_pending(found)` in `scripts/sdlc.py` holds the rule that `readiness`'s `complete` and `setup_nudge()` now share. The nudge only runs `drift()` when the recorded version is older than the plugin, so a current record is still one file read. If drift can't be read (`OSError` or `ValueError`), the line stays and nothing crashes; I checked that the invalid-UTF-8 review doc really does raise `UnicodeDecodeError`.
- **The hook carries setup's line (R6–R8).** When `update_line()` gives nothing, `hook_line()` returns `sdlc setup: <nudge>`. That part has its own `try`, so a failure there prints nothing. The release line always wins, so a session never gets two lines.
- **The skills pass it on (R10).** `/sdlc:status` ends its report with the `■ Setup` line as printed. `/sdlc:intent`'s Step 0 says it once and carries on. Both are prose edits with no new commands.
- **The docs (R11).** REFERENCE.md *After an update*, both AGENTS.md entries (*Setup* and *Updates*, reflowed to 100 columns), FEATURES.md, the `hooks/hooks.json` description, and the three docstrings.

**Tests added**, one per requirement:
- **R1:** `test_a_release_that_changed_nothing_leaves_no_nudge`. It failed on the old code with the bug's exact line.
- **R2:** `test_a_release_that_changed_a_default_nudges_until_setup_records`, which replaces `test_status_nudges_on_old_manifest`.
- **R3:** `test_a_report_only_drift_keeps_the_nudge`. It failed first because `drift_pending` didn't exist yet.
- **R4:** `test_a_current_record_runs_no_drift`.
- **R5:** `test_a_doc_drift_cannot_read_keeps_the_nudge`.
- **R6:** `test_hook_says_setup_is_behind`. It failed first with empty output.
- **R7:** `test_hook_prefers_the_release_line`.
- **R8:** `test_hook_setup_half_never_fails_the_session`.
- **R9:** `test_check_strict_ignores_drift`, now given a stale record.
- **R10:** `test_status_and_intent_pass_the_setup_nudge_on`. It fails against the old skill files, which mention `■ Setup` zero times.
- **R11:** `test_reference_says_the_hook_carries_setup_s_line`. It failed before the REFERENCE.md edit.

The R4, R5, R7 and R8 tests already passed on the old code, because it never called drift or the setup part of the hook. They guard the new paths rather than reproduce a bug.

**Where plan.md changed from the original plan:**
- **R1** uses the setup eval case's `set-up` fixture with the real plugin. The lifecycle tests' fake-plugin repo never counts as `complete`: it has no process doc, permissions or attribution.
- **R6–R8** make setup "behind" with a config key that is new since the record, not a changed default, because the hook tests run against the real plugin's defaults.

**This repo:** `status` shows no `■ Setup` line, and `update --hook` prints nothing, because the copy here is read in place.

Nothing is left in `notes.md`.

- DECISION: [default] Accept that the hook runs drift's local file reads (plus one cached git call) at session start while a repo's setup record is behind, beyond the intent's "a file read". Going ahead with it unless told otherwise.
  - OPTION: accept it — no new write, the cost only applies until setup next records, and it's the same work `status` already does; a current record is still one file read
  - OPTION: have setup re-record on its `complete` stop — keeps the hook to one file read, but adds a write before a WAIT and a commit for every release that changed nothing
  - WHY: the spec's Contracts section flags this for the person to accept, and its Alternatives rejects re-recording

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_setup_lifecycle.py -k "nudge or drift_ or strict_ignores"   (before the code)
FAILED tests/test_setup_lifecycle.py::test_a_release_that_changed_nothing_leaves_no_nudge
FAILED tests/test_setup_lifecycle.py::test_a_report_only_drift_keeps_the_nudge
2 failed, 15 passed, 44 deselected in 3.30s
exit: 1

$ uv run --group dev pytest -q tests/test_setup_lifecycle.py -k "nudge or drift_ or strict_ignores or readiness"   (after)
17 passed, 44 deselected in 3.07s
exit: 0

$ uv run --group dev pytest -q tests/test_update.py -k "setup or hook or in_place"   (before the hook code)
E           json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
1 failed, 7 passed, 18 deselected in 5.58s
exit: 1

$ uv run --group dev pytest -q tests/test_update.py::test_reference_says_the_hook_carries_setup_s_line   (before the doc edits)
1 failed in 0.08s
exit: 1

$ for s in status intent; do git show HEAD:skills/$s/SKILL.md | grep -c "■ Setup"; done
0
0
exit: 1

$ uv run --group dev pytest -q tests/test_update.py tests/test_feature_map.py tests/test_setup_lifecycle.py tests/test_skills.py
546 passed in 38.03s
exit: 0

$ uv run --group dev ruff check . && uv run --group dev ruff format --check .
All checks passed!
333 files already formatted
exit: 0

$ uv run --quiet --script scripts/sdlc.py status | grep -c '■ Setup'
0
exit: 1

$ uv run --quiet --script scripts/sdlc.py update --hook

exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 213
All checks passed!
3686 passed, 29 skipped in 213.00s (0:03:32)
✔ Validation passed
✔ Validation passed
exit: 0
