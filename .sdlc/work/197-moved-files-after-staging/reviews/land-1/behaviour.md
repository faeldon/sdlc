VERDICT: PASS

The two targeted test files pass, and the gate records are green. The change's tests exercise the order a real landing runs: the resolver, then staging, then `--continue`. I didn't run a live landing of 194. That needs a train, which I can't run read-only.

## Notes
- The change is Tier 1, so there is no `spec.md`. I checked the Approach in `intent.md` and the `landing.py` diff against it:
  - `--continue` now works out what the deleting commit added or changed, even when the deletion is already staged. `deleted_sides()` reads from the commits, and `_neither_side()` compares the carried file's text against `HEAD` and `REBASE_HEAD`. This covers the bug.
  - A conflicted file that is gone is accepted only if `deleted_sides()` names it. A deleted `UU` file is refused with a plain message (nit -20).
  - The two evidence nits are covered by the changes in `factory.py` and `tests/test_evidence_headings.py`.
- `checks.md` does not exist in the change folder, so there are no acceptance checks to read.
- I did not read `factory.py`'s diff in full, or the new tests' bodies, beyond the pass result.
- The first pytest call went to the background on its timeout. I waited for that same run to finish and did not start a second copy.

## Evidence
$ head -5 .sdlc/work/197-moved-files-after-staging/build/land-1.gate.md; head -8 .sdlc/work/197-moved-files-after-staging/build/round-1.gate.md
GATE: PASS
(the first lines of each record)
Verdict: PASS
Command: ./check.sh
Build: fb7abc339941f1c6
Exit: 0
exit: 0

$ uv run --group dev pytest tests/test_train.py tests/test_evidence_headings.py -q -n auto
156 passed, 1 skipped in 131.32s (0:02:11)
exit: 0

$ git diff b9fe72092516239dcb12d726b949bb4bf0cfa845...HEAD -- plugins/factory/scripts/landing.py | head -150
(the diff read above)
exit: 0
