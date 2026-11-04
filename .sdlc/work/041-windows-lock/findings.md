# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.

## F1. [important] [correctness] R3 and R10 are unproven: no Windows run has happened

R3 says the lock tests pass "in the Windows CI job" and R10 is the job itself, but the workflow has
never run: nothing in this change pushes, so its first run would be at `/sdlc:publish`, after the
release reaches users. Every claim about Windows rests on macOS runs with `fcntl` blocked and a fake
`msvcrt`, and README.md:36 already says the plugin runs on Windows.

Evidence: .github/workflows/check.yml:8 (`on: push`); spec.md Verification ("both jobs green is the
only proof this change has from Windows itself"); README.md:36
Class: a requirement met by tests on the wrong platform only; a support claim made before its proof
Disposition: fixed
Reason: pushed to a throwaway `ci/041-windows-lock` branch; run 41807320548 is green on both jobs,
Windows 60 passed and 1 skipped (after run 41806452244 failed five tests, F5)

## F2. [nit] [correctness] The LF test checks write_text only, not a write-mode open

R8's test walks `write_text` calls, but the spec names `open(..., "w")` too. No script opens a file
for writing today, so nothing slips now, but a later `open(p, "w")` would write CRLF on Windows
unnoticed.

Evidence: tests/test_windows.py:189
Class: a guard narrower than the rule it pins
Disposition: recorded

## F3. [nit] [cost] The workflow runs twice on every publish

`on: push` with no filter fires for the branch push and again for the tag push that
`/sdlc:publish` makes, so each release runs both jobs twice.

Evidence: .github/workflows/check.yml:8
Class: an event filter left at its default
Disposition: recorded

## F4. [nit] [contract] The factory's `_utf8_streams` copy isn't pinned to sdlc.py's

The factory keeps copies of `sdlc.py` code pinned by tests (`risk_paths()`, its regexes), and this
change pins `trackers/command.py`'s `_sh` the same way, but leaves the factory's new
`_utf8_streams` unpinned, so the two can drift.

Evidence: plugins/factory/scripts/factory.py:121
Class: a copied helper without the test the repo pins copies with
Disposition: recorded

## F5. [important] [correctness] Two tests marked portable couldn't pass on Windows

`test_with_no_tracker_a_change_runs_where_gh_doesnt_exist` links `git` alone onto PATH, which Git
for Windows can't run from, and `test_uninstall_leaves_the_pre_setup_tree`'s `_files()` keyed paths
with backslashes. The Windows run confirmed both, and three more of the same kind: test writes with
no encoding (cp1252 `—`, twice) and `pwd`'s `/c/...` form in the accept test.

Evidence: tests/test_adoption.py:363; tests/test_setup_lifecycle.py:432; run 41806452244
Class: the R9 and R6 mistakes made in test helpers, in tests newly marked portable
Disposition: fixed
By: fresh

## F6. [important] [correctness] Uninstall still compares `str(SETTINGS)` with POSIX paths

R9 names uninstall, and the diff fixes `left`, but `touched` matches `str(SETTINGS)` against git's
dirty paths and `created` matches it against the manifest's `as_posix()` list. On Windows an
uncommitted `.claude/settings.json` no longer refuses uninstall, which then rewrites it, and a
settings file setup created is left behind instead of removed.

Evidence: scripts/sdlc.py:7162, scripts/sdlc.py:7196, against scripts/sdlc.py:6766
Class: a `str()` of a Path compared with a POSIX string, the class R9 covers; shown-only at
scripts/sdlc.py:6613 and :7199 too
Disposition: fixed
By: fresh

## F7. [nit] [correctness] `_msvcrt_lock` retries forever on any OSError, not only a held lock

A lock that fails for another reason (a filesystem without byte-range locks, a bad descriptor)
spins silently, hanging `new` or `inbox-commit`, where `flock` would raise. Retry only `EACCES` and
`EDEADLOCK`, and raise the rest.

Evidence: scripts/sdlc.py:1799
Class: an error swallowed by a retry loop; only here
Disposition: fixed
By: fresh

## F8. [nit] [correctness] A suite test only a revert of the config line can fail

`test_this_repo_s_ci_workflow_is_sensitive` asserts this repo's own config names
`.github/workflows/`: only undoing R11 fails it, which the guide puts in a change's `checks.md`.

Evidence: tests/test_risk.py:176
Class: a test only a revert can fail; only here
Disposition: fixed
By: fresh

## F9. [nit] [cost] The command tracker's `_sh` docstring calls itself the copy it is

The pin compares the whole function, docstring included, so `trackers/command.py`'s copy says
"`trackers/command.py` keeps a copy" and can't be corrected without breaking the pin. Compare the
bodies without their docstrings.

Evidence: scripts/trackers/command.py:22; tests/test_windows.py:231
Class: a pin stricter than what it guards; only here
Disposition: fixed
By: fresh
