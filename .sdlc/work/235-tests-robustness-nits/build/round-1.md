## Report: 235 tests-robustness-nits, build round 1

I've built every requirement, and the full gate passes: 4145 passed, 29 skipped, plus ruff and `plugin validate`. Nothing is committed.

One fix went beyond the spec: `scripts/retro.py`. R15's new test showed that a host both listed and `!`-excluded in `hosts.local` was still read. That goes against 208 R3, which says an excluded host is never read. `_read_hosts()` now skips such a path, and it still shows under `excluded:`. I raised this as a default below.

**plan.md:** written from the code before building. It now also names the `retro.py` fix and a change to one existing preflight test (see R6).

**Code fixes, each test seen to fail first:**
- **R1:** `run_state.uncarried()` now says when an open default is SETTLED but was never ticked. A new `settled` case covers it. The plain "no `- CONFIRM:` line" reason is unchanged, and so is `mend-confirm.txt`.
- **R2:** `fix_trailers()` and `origin_trailer()` in `closing.py` now catch only `(OSError, ValueError)`, and their docstrings say so. New test: `test_trailer_builders_swallow_only_git_and_read_failures`. This is the sensitive path, so the change is held for the person.
- **R4:** `cmd_intake()` flags `from_host` only when the issue body opens with the marker. The intake test gains a body with the marker on its second line.
- **R6:** `preflight --preview` now refuses the clause flags. New test: `test_preview_refuses_the_question_s_flags_rather_than_ignoring_them`.
  - The older `test_preflight_preview_lists_findings_paths_and_stamp` passed `--context --closing 12` with `--preview`, which 210 R7 allowed. It now calls `--preview` alone.
  - No skill passes those flags with `--preview`.
- **R7:** autopilot's Steps 1 and 3 now say to single-quote a goal written in the person's own words. Its bash blocks and rules are unchanged. New test: `test_autopilot_single_quotes_the_goal`.
- **R10:** `unused_fixtures()` now also reads positional-only and keyword-only arguments. The `test_three(*, capsys)` case failed before the fix. A comment now says why `BUILT_IN` is kept by hand.
- **R15:** the `retro.py` fix above. New test: `test_an_excluded_host_is_never_read`.

**Test-only nits:**
- **R8:** the `mv` case now renames `.sdlc/work/inbox.md`, not `.gitignore`, and asserts `notes.txt` isn't named.
- **R9:** the closes case uses `_closing()` and asserts `intent_closes()`.
- **R11:** core's `_vouch` and the factory's write at the same time, 50 lines each, 100 in all.
- **R12, R18:** `ORIGIN_VALUE_RE` checks that every `Origin:` value is `host`. New test: `test_triage_files_a_host_issue_with_origin_host`.
- **R13:** the fake `claude` opens its files as UTF-8, with a portable test for it.
- **R14:** the worktree path counts as `own`. The listed count goes from 5 to 6, in the report too.
- **R16:** the `## Indicators` block is compared with rows present.
- **R17:** the drift stand-in now also raises `UnicodeDecodeError`.
- **R19:** new refusal case `grep -n dereference-recurse README.md`.
- **R20:** preview words are matched whole (`_names()`), with a portable matcher test. No skill text had to change.
- **R21, R23:** a portable body pin for `_hand_digests` and `_hand_hash`, plus fallback tests for a path with a newline in it and for a failed `hash-object`, each run against both copies.
- **R22:** all four combinations of bind and TIME_WAIT for `_lost()`, portable.
- **R24, R25:** `base_ci()` outside a repo writes nothing, and the cache is written through a temp file.
- **R26:** a `RECOMMENDED` constant, with assertions on `factory.DECIDED_AUTOPILOT` and `factory.DECIDED`.
- **R27:** the restart is made through `_restart()` (`cmd_restart`), never set by hand.
- **R28, R29:** cases for an empty WAVE or LEAVE reason, and for a LEAVE line before any group.

**entries.md:** all 31 ids as `Retire` lines. `held_entries()` reports no problems, and every id is open in the register. 2026-11-21-8 is `wontfix` and 2026-11-21-20 is `stale`, each with its reason.

**notes.md:** nothing left.

- DECISION: [default] Should a host that `hosts.local` both lists and `!`-excludes go unread? Going ahead with yes: `_read_hosts()` skips it, it gets no row, and `listed` doesn't count it.
  - OPTION: skip it — matches 208 R3 ("never read"), and R15's test can pass; `listed` drops by one for such a line
  - OPTION: leave the code and drop R15's read assertion — no code change; an excluded host is still read, against 208 R3
  - WHY: R15 asks for exactly this, and 208 R3 already says an excluded repo is never read

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "uncarried_default_is_mended" (before the R1 fix)
FAILED tests/test_factory_decisions.py::test_ready_with_an_uncarried_default_is_mended[settled]
1 failed, 4 passed, 103 deselected in 1.32s
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py -k "intake_flags or trailer_builders" (before the R2/R4 fixes)
E       At index 2 diff: (54, True) != (54, False)
E       Failed: DID NOT RAISE TypeError
2 failed, 174 deselected in 0.74s
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py
176 passed in 93.19s (0:01:33)
exit: 0

$ uv run --group dev pytest -q tests/test_preflight.py -k "preview_refuses" (before the R6 fix)
1 failed, 1 passed, 65 deselected in 0.26s
exit: 1

$ uv run --group dev pytest -q tests/test_preflight.py
67 passed in 5.83s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -k single_quotes (before the R7 edit)
E           assert 'single-quoted' in "1 — The bounds (writes nothing) ...
1 failed, 497 deselected in 0.17s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py
498 passed in 0.69s
exit: 0

$ uv run --group dev pytest -q tests/test_suite_shape.py (before `kwonlyargs`)
1 failed, 1 passed in 0.42s
exit: 1

$ uv run --group dev pytest -q tests/test_suite_shape.py
2 passed in 0.40s
exit: 0

$ uv run --group dev pytest -q tests/test_update.py -k fake_claude_opens (before the encoding fix)
1 failed, 27 deselected in 0.05s
exit: 1

$ uv run --group dev pytest -q -n 4 tests/test_retro_hosts.py (before the retro.py fix)
E       assert (2, 1) == (1, 1)
FAILED tests/test_retro_hosts.py::test_an_excluded_host_is_never_read - Asser...
1 failed, 18 passed in 5.30s
exit: 1

$ uv run --group dev pytest -q -n 4 tests/test_retro_hosts.py tests/test_retro.py
310 passed in 45.44s
exit: 0

$ uv run --group dev pytest -q tests/test_factory_loop.py
93 passed in 18.19s
exit: 0

$ uv run --group dev python - (held_entries over entries.md; ids missing from the register)
31 [] []
[]
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory_decisions.py tests/test_archive.py tests/test_preflight.py tests/test_skills.py tests/test_train.py tests/test_suite_shape.py tests/test_records_ledger.py tests/test_update.py tests/test_retro_hosts.py tests/test_setup_lifecycle.py tests/test_hand_gate.py tests/test_factory_ui.py tests/test_base_ci.py tests/test_autopilot.py tests/test_factory_loop.py tests/test_prompts.py tests/test_windows.py tests/test_retro.py 2>&1 | tail -2
1912 passed, 1 skipped in 178.17s (0:02:58)
exit: 0

$ git diff --quiet -- tests/prompts/mend-confirm.txt
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 235 2>&1 | grep -E "passed|failed|All checks|formatted"
All checks passed!
352 files already formatted
4145 passed, 29 skipped in 221.02s (0:03:41)
✔ Validation passed
✔ Validation passed
exit: 0

(The `exit: 0` on the 18-file run is `tail`'s code, not pytest's; the pass count above it is pytest's. I ran `check 235` twice, because the first run's `tail` cut off the pytest line; that run also ended `✔ Validation passed`, exit 0.)
