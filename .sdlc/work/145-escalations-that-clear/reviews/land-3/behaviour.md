VERDICT: PASS

The change's test files all pass on this rebased tree (1529 passed, 28 skipped). I didn't run `factory.py ask`, `sdlc.py gate` or the `decide` dialog by hand against a scratch repo, and the paid case run can't run in a read-only session.

## Notes
- **checks.md:** there is none for this change, so there were no acceptance checks to read.
- **Gate record:** `build/land-1.gate.md` and `build/land-2.gate.md` both read `GATE: FAIL`. Each failed in `test_nothing_in_the_repo_is_forbidden`. That test flagged text inside `land-1.gate.md` itself, a record of an earlier failure. Run now against the rebased tree, `tests/test_nothing_local.py` passes (8 passed), so the failure no longer reproduces. The script owns the gate for this round, and I didn't rerun it.
- **End-to-end paths:** the tests cover each one the spec names:
  - an escalation cleared by a green gate;
  - Ready and Landing columns for hand-built and factory changes;
  - landing progress and the train of three;
  - `recheck` after a post-commit `accept`;
  - the rebasing and `resolve` card line;
  - `decision.md` never being rewritten.
  
  All pass.
- **Working tree:** it shows `runs/land-step.md` and `reviewer-behaviour.sessions` modified. These are run-state files the factory writes, not code, and I didn't touch them.

## Evidence
$ cd .sdlc/work/145-escalations-that-clear && ls . build; sed -n 1,80p intent.md; git diff --stat a8f4a80592077f128f30ed252fd5de10699c08e0...HEAD
(listing showed `build/land-1.gate.md` and `build/land-2.gate.md`; the diff touched 56 files, 3113 insertions and 228 deletions, covering `board.py`, `board.html`, `sdlc.py`, `factory.py`, the docs and tests)
exit: 0

$ sed -n 80,230p spec.md; cat decisions.md; tail -15 build/land-2.gate.md; head -30 reviews/round-2/behaviour.md; ls checks.md
(the spec and ledger were read; D1 and D2 are settled; the land-2 gate tail showed `1 failed, 2749 passed` with the failure in `test_nothing_in_the_repo_is_forbidden`; `checks.md` was not found)
exit: 1

$ head -12 build/land-2.gate.md; head -12 build/land-1.gate.md; cat runs/land-step.md; uv run --group dev pytest -q tests/test_nothing_local.py | tail -8
(both gate records read `GATE: FAIL`, attempt 1, exit 1; `land-step.md` read `STEP: review`, `ROUND: 3`, `TRAIN: 1 of 2`; `test_nothing_local.py` gave 8 passed in 7.17s)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_board.py tests/test_land.py tests/test_train.py tests/test_hand_gate.py tests/test_factory.py tests/test_sdlc.py tests/test_metrics.py tests/test_skills.py | tail -5; git status --short | head
(1529 passed, 28 skipped in 175.36s; `git status` listed only `runs/land-step.md` and `runs/reviewer-behaviour.sessions` as modified)
exit: 0
