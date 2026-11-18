VERDICT: CHANGES

- CHANGE: [contract] .sdlc/work/inbox.md:196: the change's own commit (`b0be3da`, rebased to `bb7213e`) deletes seeds 2026-11-18-8, -9, -10, -11 and -12 (32 lines) from the base's register on the change's branch. AGENTS.md says an entry never rides on a change's branch, and that what ship and the factory's landing retire is held in the change's `entries.md` and retired by close inside the `Close` commit. Fix: restore the base's register on this branch (`git show f1a17ae:.sdlc/work/inbox.md > .sdlc/work/inbox.md`, then commit that alone), so this diff touches no register line. Close's `register_plan()` retires the seeds the intent's `idea:` and `fixes:` name.

## Notes

- Correctness of the rest holds. The drawer's `asking` counter drops a stale response in `show()` and is bumped by `openDrawer()`'s empty-folder branch. `paint()` decides "empty" once, from the trimmed text, and hides Raw for it. `spec_question()` is set by `cmd_start()` only with no refusals, and the skill quotes it. `FINDINGS_HEAD` matches the template's note, and `drift` is clean. The intake flag reads `unpushed_closes()` and gives `null` with `dangling_unread` when git can't say. The earlier F1 (a swallowed read) is fixed.
- The `test_board.py` conflict resolution keeps both sections, with no duplicate test names in `test_board.py`, `test_archive.py` or `test_factory.py`. The base's landing-track tests and this change's drawer tests both stay.
- NIT: scripts/sdlc.py:7787: when a tracker has no `closed_by`, `closing` is `None` and `dangling_unread` says git couldn't read the unpushed commits, which is the wrong reason. Say the tracker can't tell which issues a commit closes. This can't happen with GitHub today. {robustness S low}

**Done well:** the drawer tests drive the page's own `show()` and `paint()` under node, with fetches released out of order, so the stale-response test fails without the guard. The spec question is worded once, in the script, and pinned by an exact-text test. The intake test covers the unreadable-commits path, which the earlier round lacked.

**Ran (read-only):**
- `uv run --group dev pytest -q -n auto -p no:cacheprovider tests/test_board.py tests/test_archive.py tests/test_factory.py tests/test_defaults.py tests/test_skills.py`: 1090 passed, 14 skipped.
- `uv run --quiet --script scripts/sdlc.py drift`: no `breaking` or `refresh` entries.
- Searched for conflict markers and duplicate test definitions: none.

**Not run:** the full `./check.sh`, the `portable`-marked tests, and `sdlc.py accept`, which writes check results.
