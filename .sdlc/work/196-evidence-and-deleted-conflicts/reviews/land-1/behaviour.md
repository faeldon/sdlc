VERDICT: PASS

The change does what its intent says. The new tests for the evidence headings, the train's modify/delete conflict and the prompt pass.

## Notes
- **End to end, evidence headings:** `tests/test_evidence_headings.py` passes. It covers 189's report shape, where a read's output begins with a `## ` heading.
- **End to end, modify/delete conflict:** `tests/test_train.py` passes. It covers a second change that deletes a file the first edited, and that conflict now reaches the resolver. `tests/test_prompts.py` and `tests/test_decision_alternatives.py` also pass.
- **Not run:** `/sdlc-factory:build 189` and `/sdlc-factory:land 194` themselves. They are real, paid factory runs. The tests stand in for them.
- **Gate:** the round-1 record (`build/round-1.gate.md`) shows `3470 passed, 29 skipped`. I did not run the whole suite again.
- **Check "The resolver is told how to resolve a file one side deleted":** I expect it to pass. `resolver.md:30` starts with `- **A file one side deleted** (a modify/delete conflict)`.
- **Check "grep's long-option threshold counts the characters after its `--`":** I expect it to pass. `landing.py` has `GREP_FOLLOWS_MIN = 3` at line 797 and `len(name) - 2 >= GREP_FOLLOWS_MIN` at line 885.
- **Security F2 (D2):** settled as "seen", so I did not raise it again. `--continue` still accepts any conflicted path that is gone, via the `(root / f).is_file()` skip.

## Evidence
$ uv run --group dev pytest -q tests/test_evidence_headings.py tests/test_decision_alternatives.py tests/test_train.py tests/test_prompts.py
214 passed, 1 skipped in 505.52s (0:08:25)
exit: 0

$ grep -n "GREP_FOLLOWS_MIN" plugins/factory/scripts/landing.py
794:# characters after its `--` (`GREP_FOLLOWS_MIN`) that begins this one is refused (`--der` on),
797:GREP_FOLLOWS_MIN = 3
885:                (len(name) - 2 >= GREP_FOLLOWS_MIN and GREP_FOLLOWS_LONG.startswith(name))
exit: 0

$ grep -n 'A file one side deleted' plugins/factory/agents/resolver.md
30:- **A file one side deleted** (a modify/delete conflict): the prompt says which side deleted it,
exit: 0

$ git diff 4a874fa...HEAD -- plugins/factory/scripts/landing.py
(the diff showed the `GREP_FOLLOWS_MIN` change, and `cmd_resolve` now reads `factory.deleted_sides()`, skips a deleted file's marker check, and stages the `moved` and `carried` files)
exit: 0

$ grep -n 'passed\|exit' .sdlc/work/196-evidence-and-deleted-conflicts/build/round-1.gate.md
62:    3470 passed, 29 skipped in 168.38s (0:02:48)
80:    ✔ Validation passed
94:    ✔ Validation passed
exit: 0
