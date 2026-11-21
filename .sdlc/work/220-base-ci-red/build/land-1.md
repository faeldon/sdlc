I resolved the conflict in `landing.py`. One autopilot test now fails, and I can't fix it, because I may only edit the conflicted file.

I kept 219's `add("issue", …)` line, including its `intent_closes(folder)` check. I kept 220's red-CI signal, but wrote it as `add("ci", …)` because 219 moved `land_signals` to `add(kind, text)`. I also added `"ci"` to `SIGNAL_KINDS`, since every signal needs a kind there. 221 touches nothing in this file.

`tests/test_autopilot.py::test_every_signal_has_a_kind` fails: it requires every kind to be reached, and its fixture never produces a red CI. The test file isn't one I may edit. The fix is a red-`ci` preflight case in that test, or a decision to reuse an existing kind instead of adding `"ci"`. The other 53 tests in that file pass.

## Evidence

$ grep -n '<<<<<<<\|>>>>>>>' plugins/factory/scripts/landing.py
exit: 1

$ uv run --group dev pytest -q tests/test_autopilot.py
FAILED tests/test_autopilot.py::test_every_signal_has_a_kind - AssertionError: every kind reached
1 failed, 53 passed in 19.10s
exit: 1
