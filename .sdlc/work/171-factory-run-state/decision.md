DECISION: READY

**Why.** All four reviewers passed in round 2, and the gate is green on the final build (`./check.sh` exited 0: 3079 passed, 29 skipped, plugin validation passed). Round 1 had one requested change: the kill test's 60 s wait was too tight. It was fixed to 120 s, and three separate reviewer runs then passed in 62–65 s. The security reviewer checked the move with an AST comparison: all nine moved functions match the base's code once the `factory.` prefix is stripped. That covers R5, and nothing in the reviews suggests the spec was wrong.

**Open items**
- None. No change is still open. The leftover nits are recorded in `findings.md`: F1 is marked minor, and F2, F4 and F5 are recorded.

**Decisions to confirm**
- SETTLED: D1: R1 says its list is "the named entry plus every function that only it calls today, by the rule in R3", and only `loop_state` calls `decision_preamble`. The R3 test asked for the move, and round 1's AST comparison (security) shows `decision_preamble` moved unchanged. The code, test, security and behaviour reviewers all raised nothing on it.
- SETTLED: D2: Round 1's behaviour review showed the 60 s deadline fails falsely: 71 s alone on this build, against 79 s at the merge base under the old 120 s wait. Round 2's code, test and behaviour reviewers each passed it at 62–65 s under 120 s. The test still exits as soon as `.started` appears, so a fast machine waits no longer. `plan.md` (R14 line) records why it departs from the spec.

**For the person at ship**
- Start with `landing.py`, which is on `[review] sensitive`. Only two things should differ there: the -80 guard in `cmd_land_fix` (`.is_dir() and any(...)`) and the -69 comment above `_run_loop()`.
- Then run `git diff --color-moved=zebra` on `plugins/factory/scripts/` to see the moved blocks yourself. The code reviewer didn't run it; only the security reviewer checked the move, by AST.
- The context check should probably add one clause to AGENTS.md's *Modules loaded by path* naming `run_state.py` beside `landing.py` (F1).
- The spec's R14 still says 60 s while the code uses 120 s (F4, F5). Either reword it at ship or leave it as recorded.

- IMPACT: patch — The run-state move is internal, and `verdicts`' JSON and every prompt are unchanged. The -80 guard turns a `FileNotFoundError` traceback in `land --fix` into a normal round, so factory users just get something slightly better.

`notes.md` has no unticked `- [ ]` items, so there is nothing to carry forward.
