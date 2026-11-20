DECISION: READY

**Why.** The change moves the code into seven files without dropping anything. Both reviewers checked that the 279 test functions (396 test ids) and the 50 `portable` marks are the same before and after. The largest new file is 1,418 lines, and the full gate passed (`build/round-1.gate.md`: `GATE: PASS`, 3438 passed, 29 skipped). Round 1 is all `VERDICT: PASS`, and nothing in it suggests the intent was wrong. The only edit outside the tests is one comment in `factory.py`.

**Open items**
- None. No reviewer asked for any changes in round 1.

**Decisions to confirm**
- SETTLED: D1: The code already answers it. `tests/test_land.py::test_a_landing_records_each_step_it_takes` runs `factory.cmd_agent` for `land-review`, and at lines 2826–2829 asserts `(row["task"], row["purpose"], row["land"]) == ("land-review", "land", 1)` and that the row has no `round`. That is exactly what nit 2026-11-19-37 asks for, so the intent's outcome "The nit is fixed" holds, and a second copy of the test would add nothing.
- SETTLED: D2: The intent answers it. Its Outcome allows a split "per area within `factory.py` where a single file would still be large", and asks for no file past about 2,000 lines. `plan.md` shows the old file held only `factory.py`'s tests, because `landing.py`'s and `run_state.py`'s tests are already in `test_land.py` and `test_train.py`. One file per module would therefore have stayed at about 6,000 lines. Both round-1 reviewers called the area split sound.

**For the person at ship**
- **`tests/factory_helpers.py` first.** All seven files now share this one module, loaded once by path. Check that every monkeypatch still reaches the same `factory` module instance the old single file used.
- **The `claude` fixture.** It and `FAKE_CLAUDE` moved into `tests/conftest.py`. Check that no other test file defines its own `claude` fixture, which would now be shadowed.
- **`plugins/factory/scripts/factory.py`.** The only edit is the comment that now names `tests/test_factory_agent.py`.
- **Landing order.** The intent left open whether this should land before 191-tests-paydown and 193-ledger-and-landing-fixes, which also edit the factory's tests. Whichever lands second will have to rebase its test edits onto the new files.
- No published interface is touched.

- IMPACT: none — only the test layout and one code comment change; nothing a host or user receives behaves differently.

**Undone items**
- None. There is no `notes.md`, and the builder reports nothing left over.
