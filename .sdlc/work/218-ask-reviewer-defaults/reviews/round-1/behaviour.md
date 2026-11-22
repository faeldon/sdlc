VERDICT: PASS

The new tests drive the case from bug 2026-11-21-46, and `ask` now sends a change to `rebuild` when a reviewer's default was confirmed and no later builder round says it built it.

## Notes
- The change has no `checks.md`, so there are no acceptance checks to read.
- **Reviewer's default, never built:** `unbuilt_defaults()` returns it, so `ask --answered` gives `rebuild`, with `then` naming `/sdlc-factory:build NNN`, or `/sdlc:ship NNN` on a READY.
- **Builder's own default, confirmed:** it is skipped by the `builder` source check, so it still reads as kept and goes to `ship`.
- **Reviewer's default, built later:** a `- BUILT: D<n>` line in a builder report of a later round clears it. The builder agent doc, the decide skill and the README all describe that line.
- This settles the intent's open question: the script reads a `- BUILT:` line, never a model's reading.
- I did not run the gate or the whole suite. The gate record `round-1.gate.md` says `GATE: PASS` with 3952 passed.
- I ran only the decisions tests that cover this change, and 25 passed.
- I did not drive `/sdlc-factory:decide` itself, since it needs a live factory run. The tests exercise `cmd_ask()` directly, which is the closest path.

## Evidence
$ cat .sdlc/work/218-ask-reviewer-defaults/build/round-1.files; git status --short; git diff HEAD -- plugins | head -300; head -5 .sdlc/work/218-ask-reviewer-defaults/build/round-1.gate.md; grep -n "exit\|passed" .sdlc/work/218-ask-reviewer-defaults/build/round-1.gate.md | head
(output tail) GATE: PASS / `62:    3952 passed, 29 skipped in 259.92s (0:04:19)`
exit: 0

$ git diff HEAD -- tests/test_factory_decisions.py | grep '^+def test'; uv run --group dev pytest tests/test_factory_decisions.py -q -k "unbuilt or built or reviewer or default" 2>&1 | tail -5
(output tail) `25 passed, 75 deselected in 27.96s`
exit: 0
