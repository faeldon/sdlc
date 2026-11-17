I've built change 112 (a Tier 1 change upgraded to Tier 2 mid-run) and left it uncommitted on its branch; HEAD is still `175ad83`. `./check.sh` passes (2287 tests), `sdlc.py check --strict` reports no problems, and I raised no decisions.

The command, step and docs all say "upgrade", not "promote", as you asked in R1.

## What was built, slice by slice (plan.md first)

1. **`sdlc.py upgrade <NNN>`** (R1, R2). Run in the change's own checkout, it sets `tier: 2`, `stage: plan` and `updated:` by editing those lines in place, so `id: 012` and the key order survive. It creates `spec.md` and `plan.md` from the templates only where they are missing. It refuses, writing nothing, on the base branch, for an id that isn't this checkout's change, on a change already at Tier 2, or at any stage but plan or build. To share the template filling, I moved `new`'s substitutions into `render_template()`, which both commands call.
2. **The answer, the record and `factory.py upgrade`** (R3–R5).
   - `verdicts` names `upgrade` only for a ticked blocking answer that starts `upgrade to Tier 2` (any case), and only on a Tier 1 change.
   - `factory.py upgrade` writes `build/round-<P>.upgraded.md` first, then runs `sdlc.py upgrade`. If a run stops between the two, a rerun finishes it without a second record.
   - A change is upgraded once. A record that doesn't read is a stop with way `rerun`.
3. **Spec, then round P** (R6–R10).
   - `verdicts` names `spec` at round P, with `written`, until the change reaches `stage: build`. It then names `build` at P.
   - The round limit, `exhausted` and the light-depth count all start again from P, as after a restart.
   - The round-P build resumes the builder's own session and writes a new `build/round-P.md`. Without this, the existing code would have written over `round-1.md`.
   - The spec-writer, round P's reviewers and the approver are each told about the upgrade.
   - `decided` refuses for the upgrading decision, and refuses any decision while the upgrade is under way.
4. **`start` and `fresh`** (R11). `start` reports `upgraded`, and `fresh` leaves an upgraded run where it is (`held`).
5. **`check` during round P** (R12). While round P's build is live, a template `plan.md` is not flagged, the same exemption a first factory build already gets. `sdlc.py` reads the record's filename with its own copy of the factory's pattern, and a test keeps the two equal.
6. **The pause on the board** (R13). `upgrade` and `spec` now record the step they paused at, as `decide` does, and the board's step track shows them paused instead of dropping the track.
7. **Skill and docs** (R14, R15).
   - The build skill gains a permission line for `factory.py upgrade`, an `upgrade` bullet and a `spec` bullet, a note at `decide` about upgrade answers, a fourth wording of the approval question, and which stage moves Step 3 still owes.
   - `agents/builder.md` says how a Tier 1 builder asks for an upgrade.
   - The factory README, `factory.py`'s docstrings, AGENTS.md's factory paragraph and `docs/REFERENCE.md` describe it.

## Tests added
- **`tests/test_sdlc.py`**: R1 (lines edited in place, scaffolds only where missing, `check --strict` clean), R2 (four refusals, each leaving the folder unchanged), R12 (the scaffold is allowed while round P is live, and flagged again in seven not-live cases).
- **`tests/test_factory.py`**:
  - R3: what counts as an upgrade answer and what doesn't; a Tier 2 never upgrades.
  - R4: the record is written before the tier, `HEAD` doesn't move, and a run cut short finishes on rerun. A bad record stops the run.
  - R5: no second upgrade.
  - R6: spec then build at P, with the rounds counted from P.
  - R7–R10: each prompt, the resume, and the `decided` refusal.
  - R11, R13, and the test that keeps the two filename patterns equal.
- **`tests/test_board.py`**: R13's paused track, and that the board's copy of the paused steps matches the factory's.
- **`tests/test_skills.py`**: R14 — every step `loop_state()` can name must have a bullet in the build skill. It failed on `spec` and `upgrade` before the skill had them.

R15 is prose only, so it is covered by an acceptance check in `checks.md` instead of a test: each doc must mention the upgrade, and none of the factory's docs may say "promot". It passes now.

## plan.md, and what's left
- `plan.md` was updated where the build departed from it: an extra R3 test, and R15 covered by `checks.md`.
- Nothing is left in `notes.md`.
- `upgrade` writes before the spec's approval question. I didn't treat that as a fifth exception to confirm-before-writing, because it only runs on the person's own answer inside a run they already approved. The spec asks ship's review to check that reading.

## Evidence

$ uv run --group dev pytest -q tests/test_sdlc.py -k upgrade   (first run, before the code)
7 failed, 220 deselected in 1.83s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "upgrad"   (before the code)
11 failed, 1 passed, 210 deselected in 8.10s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py -k every_step_verdicts   (before the skill edit)
E       AssertionError: steps verdicts names with no bullet in the build skill: ['spec', 'upgrade']
exit: 1

$ ./check.sh
All checks passed!
2287 passed, 13 skipped in 195.04s (0:03:15)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py check --strict
■ Problems: 0
    none ✅
exit: 0

$ uv run --group dev pytest -q tests/test_sdlc.py -k "upgrade or upgraded_build"
15 passed, 220 deselected in 3.40s
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py -k "upgrad or decided_refuses or fresh_holds or start_reports or spec_prompt_names or told_of or pinned_copy"
25 passed, 209 deselected in 15.34s
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -k upgrade
2 passed, 141 deselected in 1.34s
exit: 0

$ uv run --group dev pytest -q -m portable -n auto
370 passed, 13 skipped in 25.63s
exit: 0

$ sh -c "<checks.md's one sh block>"
exit: 0

$ git log --oneline -1
175ad83 Close 111-factory-loose-ends
exit: 0
