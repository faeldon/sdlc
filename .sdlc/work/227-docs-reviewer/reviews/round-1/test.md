VERDICT: PASS

No requirement lacks a test that would fail without it, and I found no test that can't fail. The gate record (`build/round-1.gate.md`) is green: `4064 passed, 29 skipped`, validation passed. I ran only the new file, `tests/test_factory_docs.py`, in the foreground: 20 passed.

## Notes
- **R1–R3, R5, R8, R11 (factory side):** each has a named test in `tests/test_factory_docs.py`. The R1 test covers all three roster copies and the `sonnet` default, and also checks that a `models` override takes effect. The R3 tests cover warn-and-drop and a light run staying light. The R5 tests cover the default list and a changed checkout not affecting the list. The R8 and R11 tests cover the full-depth `max_runs` count and `reviewers = ["code"]` still expecting `docs`.
- **R4:** one test per clause (a) to (e). The (e) test covers all three cases the spec lists: change folder only, tests only, and `src/a.py`.
- **R6:** `docs_prompt` is asserted to list exactly the docs that exist, plus a renamed line, a deleted line, and `Stale lines: none.`.
- **R7:** the test asserts `**Context.**`, `[docs] context` and `[context]` are all absent from `reviewer-code.md`.
- **R9 (`tests/test_preflight.py`, `tests/test_findings.py`):** the tests cover:
  - the pass applying on `src/a.py` and naming the side file;
  - not applying on a tests-only diff;
  - applying on a test a base-branch doc names;
  - never applying on a factory run;
  - ship's question wording for a skipped pass;
  - `SHIP_PASSES` and the `By:` vocabulary.
- **R10:** a test in `tests/test_skills.py` checks that Step 3 names `docs.md` and hands the first Context question to `sdlc:docs`.
- **R12:** all six doc edits are pinned (`test_defaults.py`, REFERENCE, README table, `test_feature_map.py`, build skill, `AGENTS.md`).
- **D1:** the builder's open decision (ask for the `Docs review:` line only when `findings.md` exists) has a test, `test_a_change_with_no_findings_file_ships_without_a_docs_line`. D1 is still unanswered in `decisions.md`; the builder defaulted it and the arbiter should confirm. This is not a CHANGE from me.
- **checks.md:** there is none, and none is needed. Every requirement is covered by a suite test.
- **Nit:** the `SHIP_AGENTS` stand-in in `tests/test_skills.py` is hand-extended for `docs`. That is fine, since a missing entry fails the test.
