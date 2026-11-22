I built the `docs` reviewer for 227 and left it uncommitted on the change's branch. The full gate passes: 4064 passed, 29 skipped, ruff clean, plugin validate passed. Two things need you: one default I chose that changes how `/sdlc:ship` behaves (below), and about 150 lines of existing tests I changed, because the new join rule calls `docs` into nearly every round.

**Slices built**
1. **Roster (R1–R3).** `docs` is in `REVIEWERS`, `ROLES` and `SCALED` (so it runs on sonnet), and in the two copies, `factory_records.REVIEWERS` and `sdlc.AGENT_ROLES`. An untagged docs finding is filed under `context`. A new `JOINING` list covers the reviewers that join on their own: naming `docs` in `reviewers` or `[light] reviewers` warns and drops it, and it never makes a run's depth full.
2. **The docs list (R5).** `_docs_at()` reads `[docs] context` and the new `[docs] reviewed` from the base branch only, so a change can't take its own docs out of review. `reviewed_docs()` expands folders and globs. The default list is a copy of `sdlc.py`'s, pinned by a test.
3. **Joining (R4, R8, R11).** `docs_review()` applies the five clauses (a)–(e). `_rounds_at_depth()` adds `docs` to the round's expected reviewers, and `max_runs()` counts it in every round, so the default bound goes from 26 to 29.
4. **Prompt and agents (R6, R7).** The new `reviewer-docs.md` agent's prompt lists the docs and the stale lines (doc lines naming a path the diff deletes or renames). The Context pass and the `[context]` tag are gone from `reviewer-code.md`.
5. **Ship (R9, R10).** A new core agent `agents/docs.md` (`sdlc:docs`) and side file `skills/ship/docs.md`, plus the `docs` pass in `preflight`, the `Docs review:` note line and `By: ship-docs`. Ship's Step 3 now hands "does it now say something false" to `sdlc:docs` when the side file is named.
6. **Docs (R12).** Edited `guide/review.md` (then ran `sdlc.py record`; `drift` reports nothing), `docs/REFERENCE.md`, `plugins/factory/README.md`, `docs/FEATURES.md`, the factory build skill and `AGENTS.md`. Each edit is pinned by a test.

**Tests added**
- `tests/test_factory_docs.py`, 20 tests:
  - R1–R3: the roster, the model and the warnings.
  - R5: the list, three tests.
  - R4: one test per clause (a)–(e), with the three (e) cases from the spec.
  - R11, R8, R6 and R7.
  - R12.2, R12.3, R12.5 and R12.6.
- Ship: 4 tests in `test_preflight.py` and 4 in `test_findings.py` (R9 and the default below), 1 in `test_skills.py` (R10).
- R12.1 in `test_defaults.py`, R12.4 in `test_feature_map.py`.

**Existing tests changed.** Any diff touching a path outside `tests/` now calls `docs` in, which covers nearly every fixture. In `test_land.py` and `test_train.py` I added a `REVIEWED` constant (the full depth plus `docs`). The depth, gate, loop and UI tests now expect `docs` in their lists, and their `max_runs` bounds go up by one per round. `test_findings.py` and `test_preflight.py` have the new `ship-docs` and `docs.md` entries. The agent-tool tables in `test_skills.py` name the two new agents.

**Where the build differs from the spec** (all recorded in `plan.md`)
- The docs reviewer's prompt is added in `cmd_agent()`, as the UI reviewers' screenshots are, not through a `prompts/` file.
- R12.2: the spec said REFERENCE already names every `[docs]` key as `docs.<key>`. Two of them (`read_before_design`, `explore`) only appear in the example block, so the test accepts either form and pins `docs.reviewed` both ways.
- R12.4: `test_feature_map.py` doesn't check config keys, so a new test asserts the `docs.reviewed` entry and a `ship-<name>` entry for each ship pass.
- To satisfy the test that every config key has a reader, the ship side file names `docs.reviewed` from `config`. That list is read from the checkout. Whether the pass applies is still decided from the base branch.

`notes.md`: nothing left. No `[default]` from a reviewer or the approver was open, so there are no `BUILT:` lines.

**Decisions**
- DECISION: [default] Ship asks for the `Docs review:` line only when the change has a `findings.md`. Going ahead with that unless told otherwise.
  - OPTION: only when `findings.md` exists — a change with none keeps shipping as today (the code already treats such a change as older than the file); a ship without the file never shows whether the docs review ran
  - OPTION: always, as the security and behaviour checks do — the same rule for every pass; any hand-built change with no `findings.md` is refused, since this pass applies to almost every diff (83 tests failed this way, the new-to-close adoption flow among them)
  - WHY: the docs pass applies to nearly every diff, unlike the other passes, so the same rule would make `findings.md` effectively required at every ship, which no requirement asks for

- UNTESTABLE: none

## Evidence

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 227 > /tmp/227-check.log 2>&1
✔ Validation passed
[exited with code 0]
exit: 0

$ grep -E '[0-9]+ passed|FAILED|All checks|ruff|exit' /tmp/227-check.log | tail -8
All checks passed!
4064 passed, 29 skipped in 360.49s (0:06:00)
exit: 0

$ uv run --group dev pytest -q tests/test_factory_docs.py
20 passed in 38.59s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_findings.py tests/test_sdlc.py tests/test_archive.py tests/test_cleanup.py tests/test_push.py tests/test_register_lands.py tests/test_resolve.py tests/test_surface.py
FAILED tests/test_surface.py::test_every_key_has_a_reader - AssertionError: a...
1 failed, 597 passed in 85.05s (0:01:25)
exit: 1

$ uv run --group dev pytest -q tests/test_surface.py tests/test_skills.py
516 passed in 41.85s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_land.py tests/test_train.py
283 passed, 1 skipped in 291.71s (0:04:51)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory_depth.py tests/test_factory_ui.py tests/test_factory_docs.py
93 passed in 16.07s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory_loop.py tests/test_factory_gate.py tests/test_factory_agent.py tests/test_skills.py
725 passed in 70.25s (0:01:10)
exit: 0

$ uv run --group dev pytest -q tests/test_preflight.py tests/test_findings.py
125 passed in 29.16s
exit: 0

$ uv run --quiet --script scripts/sdlc.py record
  wrote  .sdlc/setup.json  (plugin 1.11.0, 3 doc(s))
exit: 0

$ grep -n '\*\*Context\.\*\*\|\[docs\] context' plugins/factory/agents/reviewer-code.md
exit: 1

$ git log --oneline -1
6f1c1b0 Retire 2026-11-21-50
exit: 0
