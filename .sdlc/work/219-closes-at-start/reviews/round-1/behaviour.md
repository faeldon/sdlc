VERDICT: PASS

The change does what the intent's Outcome says. `closes:` is recorded at `start`, and `intent_closes()` returns the union of the ledger's record and the working copy. `land-check`'s `issue` signal reads the same union.

I did not run `factory.py start` against a live change. I ran the three new tests for it instead, and they pass.

- PREEXISTING: none found.

Decision D1 (the builder's default) is not raised again. Recording in `factory.py agent` as well as `start` matches the intent's goal, because autopilot never runs `start`.

## Notes
- **`checks.md`:** the change has none, so there was nothing to read or expect.
- **Gate:** `round-1.gate.md` reads `GATE: PASS`. Attempt 1 failed and attempt 2 passed.
- **Ledger rows:** the new `{"change","closes"}` row has no `record` or `sha256`. `vouched()` compares whole parsed lines against the wanted record row, so the new row can never vouch for a record. Core only appends to the ledger; it does not read these rows back, so `factory_records.py` needs no pinned copy.
- **Intent's open questions:** a restart or upgrade runs `start` again, and the union covers every recorded row for the change, which is the safer choice. `record_closes()` skips a value the ledger already holds, so reruns add nothing.
- **Ledger append:** `record_closes()` goes through `_append_ledger()`, the same locked append `_vouch()` uses, and raises `OSError` when it can't, which `start` and `agent` both turn into a refusal.
- **No `closes:`:** `record_closes()` returns before appending, so a change with none writes nothing, and `test_a_change_closing_nothing_records_nothing` covers that.

## Evidence
$ cat .sdlc/work/219-closes-at-start/intent.md; cat .sdlc/work/219-closes-at-start/checks.md; cat .sdlc/work/219-closes-at-start/build/round-1.gate.md | tail -15
(intent printed; checks.md absent; gate tail ends "✔ Validation passed")
exit: 0

$ git diff $(git merge-base HEAD main) --stat | tail -15; git diff $(git merge-base HEAD main) -- plugins/factory/scripts | head -250
(5 files changed: factory.py, landing.py, README, two test files; diff read)
exit: 0

$ grep -n "RECORDS_LEDGER" -r plugins scripts | head; sed -n 3128,3160p plugins/factory/scripts/factory.py; uv run --group dev pytest tests/test_factory_decisions.py -q -k "closes" 2>&1 | tail -5
...  [100%]
3 passed, 96 deselected in 28.03s
exit: 0

$ grep -nE "^(GATE|## Attempt|Verdict)" .sdlc/work/219-closes-at-start/build/round-1.gate.md
1:GATE: PASS
3:## Attempt 1
5:Verdict: FAIL
96:## Attempt 2
98:Verdict: PASS
exit: 0
