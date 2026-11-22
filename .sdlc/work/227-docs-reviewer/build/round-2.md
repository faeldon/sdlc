I reran what round 1's claims rest on, and the full gate now finishes with an exit code: 0, with 4071 passed and 29 skipped. The earlier run was stopped at its time limit without ever reporting one.

**Kept change (C1):** `skills/ship/docs.md:27` now says `sdlc.py ship` refuses a diff this pass applies to whose note says neither "when the change has a `findings.md`", which matches the code. I also added a `docs` bullet to `docs/REFERENCE.md`'s list of ship's passes. After its "ship refuses a note that says neither" sentence I added one saying the docs pass is asked of a `findings.md` that exists, never of a change with none (line 162). D1 is still open; if you answer it the other way, these two sentences and the `cmd_ship` check change together.

**Nit:** `test_ship_and_the_factory_join_by_the_same_rule` in `tests/test_factory_docs.py` runs both copies of the join rule over the same seven fixtures. The copies are `factory.py`'s `docs_review()` and `sdlc.py`'s `_docs_applies()`, and the fixtures cover clauses (a), (b), (c) and (e). It passes; I never broke one copy on purpose to watch it fail.

No `plan.md` changes and nothing in `notes.md` this round. I raised no new decisions; D1 (whether ship asks for the `Docs review:` line only when `findings.md` exists) stays open for you.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_factory_docs.py tests/test_findings.py tests/test_feature_map.py
97 passed in 55.93s
exit: 0

$ grep -n 'when the change has a `findings.md`' skills/ship/docs.md
27:refuses, when the change has a `findings.md`, a diff this applies to whose note says neither.
exit: 0

$ grep -n 'never of a change with none' docs/REFERENCE.md
162:to nearly every diff, is asked of a `findings.md` that exists, never of a change with none.
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
358 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 227 > /tmp/227-check3.log 2>&1; echo "exit: $?" >> /tmp/227-check3.log
(run in the background; completed, exit code 0)
exit: 0

$ grep -E 'All checks|[0-9]+ passed|FAILED|Validation|^exit: ' /tmp/227-check3.log | tail -6
All checks passed!
4071 passed, 29 skipped in 465.14s (0:07:45)
✔ Validation passed
✔ Validation passed
exit: 0
