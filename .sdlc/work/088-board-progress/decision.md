DECISION: ESCALATE

**Why:** Every requirement R1–R16 has code and a named test by the reviewers' account. Round 2 passed from the code, ui and ux reviewers, and the gate passed with 1902 tests, so this is close to READY. It escalates because decision D1 is still unticked: the plan hint was built on a default the person hasn't confirmed, and the builder says that default is wrong in practice. Also, the new `TEMPLATE_READS` entry changes what `drift` reports to hosts, which is a published interface.

**Open items:** none. Round 1's two ux changes (C1: a step's state shown only by colour; C2: a progress bar inside a `<button>`) were kept by the verifier and fixed in round 2, and all three reviewers confirmed the fixes. There is no `notes.md`. Three optional notes from the code reviewer in round 1 are still undone and are minor:
- `_progress()` returns `null` for a `decide` record that has no `AFTER:` line, where R4 says that step should keep its position.
- The stopped check is partly redundant with `_stopped()`.
- The bar's percentage is computed twice.

**Decisions to confirm:**
- D1: the build reads every line of `plan.md`'s `## Files to change` as a possible file, as the spec says. The builder recommends reading list items only. On this change's own plan the current reading counts 14 "files", because wrapped lines pick up dotted names like `progress.fraction`. So the hint is unreliable as built. Either confirm it as a follow-up or have it fixed before landing.

**For the person at ship:**
1. **D1's effect:** `_plan_named()` in `scripts/board.py`. Check whether `plan: T of N files touched` is worth showing as it stands.
2. **Host-facing change:** the `"plan.md": {"headings": ("Files to change",)}` entry in `scripts/sdlc.py`'s `TEMPLATE_READS`. A host whose `.sdlc/templates/plan.md` override drops that heading will now see it under `drift`'s `breaking`, and `readiness` will stop reporting `complete`. That's what AGENTS.md requires, but it's the part that reaches other repos.
3. **The factory's new file:** `cmd_verdicts(record=True)` in `plugins/factory/scripts/factory.py` now writes `runs/step.md` on every `--record`. Confirm `loop_state()` never opens it; `test_the_step_record_never_reaches_the_loop` covers this. The build also departs from the spec in three ways, all reasonable but none listed in `plan.md`'s Files to change:
   - an `AFTER:` line on a `decide` record (the work order explains it);
   - a named `SECONDS_RE` in the factory;
   - the bar's label leads with the elapsed time.
4. **Never seen on screen:** both ui and ux reviewers said no screenshot had a factory card with a step track on it. The track, the bar and the "waiting on you:" wording at 390px were judged from the code only. The spec's manual walk-through on the board is worth doing once.
5. **Overlap with 086-board-signals-by-stage:** both edit `_factory()` and `tests/test_board.py`, so whichever lands second will need a rebase.

- IMPACT: minor — a factory card now shows a step track, a time estimate and a plan hint, and `verdicts --record` writes `runs/step.md`. A host whose plan template override lacks `## Files to change` will now see a `drift` report it has to act on.
