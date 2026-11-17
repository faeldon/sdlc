VERDICT: PASS

PREEXISTING: scripts/sdlc.py:3926: the `_drop_record` docstring breaks off mid-sentence ("Why not, or" / "None; a failure leaves main as it was"). It predates this change (HEAD:3920) and isn't in the diff, so it's filed for later.

## Notes

This is Tier 1, so there is no `spec.md`. I took the requirements from `intent.md`'s Outcome and Constraints.

What I checked against the outcome:

- **Length and map.** AGENTS.md went from 517 to 293 lines. The Invariants section is byte-identical to HEAD.
- **No rule lost.** I went through the old Architecture's "never" and "only" rules and checked each against the new text, the docs, the docstrings and the tests. Every one I checked lives somewhere. Examples: the nit-never-a-seed rule (`scripts/sdlc.py:1544`), red-is-a-stop (`factory.py:2299`), the shim refusal (`sdlc.py:5002`), the manifest-widens-scan rule (`tests/test_skills.py`, `test_sdlc_loads_nothing_from_plugins`), and the own-script crash fallback (`_run_own`'s docstring).
- **Pointers resolve.** All 184 backticked identifiers in the new AGENTS.md exist in the repo. The 54 `name()` pointers are all defined in code (only `as_posix()` and `open()` are not, and those are stdlib calls the unchanged Invariants section names). Every italic pointer matches a real heading in REFERENCE.md, CONTRIBUTING.md or the factory README.
- **Ship's context pass.** The new question is in `skills/ship/SKILL.md` and mirrored in REFERENCE.md. The skill is at 475 lines, exactly its budget, so the next change to it will hit the ceiling.

Optional, for the person to judge:

1. The Architecture section is about half its old size, but it is still long: Factory, Setup and Closing each run 10 to 20 lines and still restate mechanics that REFERENCE or the docstrings hold. The outcome says "a map, not a manual", and nothing measures that. Whether to cut further is a judgment call.
2. `.sdlc/work/inbox.md` is modified in the worktree: `[idea]` became `[building]` for 2026-11-17-3. AGENTS.md says the register is committed only by `inbox-commit`, on the base branch, so an entry never rides on a change's branch. Please confirm that the `[building]` status line is the intended build flow and that ship won't commit it onto this branch.

Nits:

- REFERENCE.md:234 is a new 121-character line in a paragraph wrapped at about 100. Rewrap it.

## What is done well

- The cut was done in the order the plan set: each *Moved* rule went into its docstring before its paragraph was cut, so nothing was lost in between.
- The plan's "said elsewhere" table is accurate for every rule I spot-checked, and the cut keeps every boundary that a local edit would break.
- The `cmd_base`, `cmd_resolve`, `cmd_close` and `retro.py` docstring additions match the code: `resolvable` is in the output, `skills/ship/conflict.md` exists, the close steps run in the order the docstring gives, and the tests really do use `sdlc.retro.<name>`.

## Tests and commands run

- `uv run --group dev pytest -q -n auto` on `test_skills`, `test_nothing_local`, `test_defaults`, `test_retro`, `test_findings` and `test_board`: 654 passed.
- `ruff check` on `scripts`, `plugins/factory/scripts` and `tests`: clean. `ruff format --check scripts`: clean.
- Not run: the full suite, `./check.sh` (it includes `claude plugin validate`), and the acceptance checks in `checks.md`. I did not confirm the "fails on the old text" claims in `checks.md`.
- The lost-rule sweep was grep-based and concept-level. I did not read every line of the factory README's Mechanism and What-it-leaves sections against the old factory paragraph, so a rule could be missed there.
