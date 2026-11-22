VERDICT: PASS

The spec's path (the `docs` pass reaching ship, and the factory reviewer joining a round) behaves as specified. I ran ship's `preflight 227` against the built tree. Its `passes` part shows `docs` applying, and `branches` names `docs.md` beside `behaviour.md` and `cases.md`. I did not run a factory round, so I did not run that join rule end to end. The tests listed below cover it.

## Notes
- `checks.md` does not exist for this change, so there is no check to read.
- Gate record `build/round-1.gate.md` starts `GATE: PASS`. I did not rerun the gate.
- The spec names no single end-to-end command, so I ran the closest one: `preflight 227`. `docs` applies because the diff touches paths outside `tests/` (R9 clause e).
- `ux` is absent from `passes` in that output. I take it that `ux` doesn't apply to this diff; I did not check why.
- `CONFIG_KEYS["docs"]["reviewed"] = []` exists at `scripts/sdlc.py:269`.
- `reviewer-code.md` no longer contains `Context` or `[docs] context` (R7).
- The docs and preflight tests (24) pass. They cover the join clauses, the base-branch docs list and the ship pass note.
- Not run: a live factory round, because it spawns agents.

## Evidence
$ cat .sdlc/work/227-docs-reviewer/build/round-1.gate.md | head -5
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ uv run --group dev pytest -q tests/test_factory_docs.py tests/test_preflight.py -k "docs"
........................                                                 [100%]
24 passed, 62 deselected in 38.76s
exit: 0

$ uv run --quiet --script scripts/sdlc.py preflight 227
(passes) "docs": {"applies": true, "why": null}; "branches": ["behaviour.md", "docs.md", "cases.md"]
exit: 0

$ uv run --quiet --script scripts/sdlc.py preflight 227 --question
Commit this, with .sdlc/work/227-docs-reviewer/ stamped shipped, then update its issue? (yes / edit the message)
exit: 0

$ grep -n '"reviewed"' scripts/sdlc.py
269:        "reviewed": [],
7990:    for key in ("context", "reviewed"):
exit: 0

$ grep -c "Context\|docs\] context" plugins/factory/agents/reviewer-code.md
0
exit: 1
