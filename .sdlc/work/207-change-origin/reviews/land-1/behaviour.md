VERDICT: PASS

The change does what the spec says. The gate record is green and the origin tests pass. No checks.md exists, so there was nothing to read or run.

## Notes
- **`checks.md`:** this change has none.
- **Gate:** `build/round-1.gate.md` reads `GATE: PASS` with `Exit: 0`. I did not rerun it.
- **Origin tests:** I ran the 17 tests whose names contain "origin", across the archive, retro, sdlc, skills and metrics test files. They cover the `Sdlc-Origin` trailer on close, a change with no origin closing without one, and the retro counts. All 17 passed.
- **`load_change()` and `_change_record()`:** both read `origin:` as text. A missing line gives None, so a change with no origin is never read as `self`.
- **`load_change()` errors:** an invalid value, or more than one value, is reported as an error.
- **`origin_trailer()`:** it returns a trailer only for `host` or `self` and never raises. `_step_remove_folder()` appends it after the `Sdlc-Fixes` lines.
- **`parse_trailers()`:** a bare `origin` now reads as text, so the value is no longer lost.
- **`retro()` and its skill text:** `retro()` now returns `origins`, with `unknown` kept apart from `self`. The retro and intent skill text match the spec's wording on `origin:`.
- **Not run by hand:** I did not exercise the skill prompts (`/sdlc:intent`, `/sdlc:idea`, `/sdlc:bug`) in a live session. Only the tests cover them.

## Evidence
$ uv run --group dev pytest -q -k "origin" tests/test_archive.py tests/test_retro.py tests/test_sdlc.py tests/test_skills.py tests/test_metrics.py
17 passed, 1380 deselected in 14.06s
exit: 0

$ cat .sdlc/work/207-change-origin/checks.md
[bat error]: '.sdlc/work/207-change-origin/checks.md': No such file or directory (os error 2)
exit: 1

$ head -8 .sdlc/work/207-change-origin/build/round-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: d09da84289f37c71
Exit: 0
