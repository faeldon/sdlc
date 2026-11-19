I resolved the one conflict in `scripts/closing.py`. The conflict-touching tests pass, but `tests/test_archive.py::test_close_output_is_unchanged` now fails for 4 of its 5 scenarios.

## What I did

The conflict was in `measure_change()`'s inner `finish()`, where both sides changed the lines after `_lead_line`.

- **From 172 (this change):** `_lead_line` now takes an `errors` list. When `errors` is non-empty, `finish()` puts it in `summary["errors"]`, inside the `if stage != dropped` block. I kept that as built.
- **From the earlier changes in the train:** the `runtime_trailer` block, with its `runtime=failed` coverage fallback. It builds `tail = [lead, ran]` and returns `trailers + extra + tail`. I kept it as built.
- **Combined:** the `errors` check sits right after the `lead` call, followed by the runtime block and the combined return. I left everything else as built.

## What the failing test means

The failing tests are `shipped`, `dropped`, `rerun` and `pushed`; `check` passes. 172's snapshot `tests/fixtures/close-output.json` was recorded before the runtime trailer existed. `runtime_trailer` always has the plugin version, so every `Close` commit now gains a `Sdlc-Runtime: plugin=…` line that the snapshot doesn't have. I did not confirm this by diffing the output, because the pytest diff was truncated, so it is my best reading, not a checked fact.

The fix is to re-record the fixture, and probably to normalise the plugin version in `_normal`. Both `tests/fixtures/close-output.json` and `tests/test_archive.py` are outside the files I may edit, so I left them. This needs a follow-up from the person or the gate.

I noticed nothing else worth reporting.

## Evidence

$ grep -c '^<<<<<<<\|^>>>>>>>' scripts/closing.py
0
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_metrics.py tests/test_modules.py
227 passed in 1.33s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_archive.py tests/test_cleanup.py tests/test_push.py tests/test_register_lands.py tests/test_nits.py
FAILED tests/test_archive.py::test_close_output_is_unchanged[pushed]
FAILED tests/test_archive.py::test_close_output_is_unchanged[dropped]
FAILED tests/test_archive.py::test_close_output_is_unchanged[shipped]
FAILED tests/test_archive.py::test_close_output_is_unchanged[rerun]
4 failed, 218 passed in 42.88s
exit: 1
