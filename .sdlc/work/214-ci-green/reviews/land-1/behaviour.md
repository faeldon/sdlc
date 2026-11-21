VERDICT: PASS

The spec's end-to-end path is the CI fix. CI itself isn't runnable here, so I ran the tests behind each fix. All four test files passed (200 tests). The gate record for the round is green.

## Notes
- **The workflow's comment claims nothing about setup-uv's cache token** (the one check in `checks.md`): I expect it to pass. The diff removes the "cache token" wording from `.github/workflows/check.yml`, and `grep -c "cache token"` on the file prints 0. I read the check but did not run it.
- **Not run here:** CI itself on Linux and Windows. That is the landing's `gh run list` look, not mine.
- **Windows `UnicodeDecodeError` fixes (reading the diff, not run on Windows):** `_hand_digests` and `_only_time_wait` pass `encoding="utf-8"`. `tests/test_windows.py` was extended with new tests, and they passed on macOS.
- **Linux port race:** the fix is `_only_time_wait()` in `plugins/factory/scripts/factory.py`. It reads `/proc/net/tcp` and `/proc/net/tcp6`, and where those files don't exist (macOS) it returns False, so the bind's own answer stands.

## Evidence
$ cat .sdlc/work/214-ci-green/build/round-1.gate.md | tail -3
    ✔ Validation passed
exit: 0

$ tail -5 .sdlc/work/214-ci-green/build/land-1.gate.md
    ✔ Validation passed
exit: 0

$ grep -c "cache token" .github/workflows/check.yml
0
exit: 1

$ uv run --group dev pytest -q tests/test_hand_gate.py tests/test_factory_ui.py tests/test_windows.py tests/test_upstream.py | tail -4
200 passed in 68.06s (0:01:08)
exit: 0
