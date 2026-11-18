DECISION: ESCALATE

**Why.** Every reviewer passed round 2. All of R1–R19 have code and a named test. The two changes the test reviewer kept in round 1 (R14's handoff test, R8's other two ejection causes) were made, and one of the new tests caught a real bug: `cmd_close()` cleared `LOCK_HELD_ENV` too late, so the first git call still saw it. The builder's round-2 gate passed (2569 tests, both validators). This still goes to you because default D1 is a cost trade-off and a reading of R3's "holds", which only you can confirm. The spec also says the change gives up a gate guarantee and that this "needs your yes". And every factory host's landing changes shape, which is a published interface.

**Open items**
- None. No change is still being asked for; round 2 is all `VERDICT: PASS`.
- Two nits from round 1 were marked minor in `findings.md` and left as they are:
  - F1 (code): an over-long line in AGENTS.md's factory paragraph.
  - F4 (test): a weak "no merge in the reflog" assert in the stacking test.

**Decisions to confirm**
- No unticked blocking decisions.
- ESCALATED: D1: the `train-resolve` prompt names each change's spec and diff (`git show`) instead of including them. R3 says the prompt "holds" them, and the builder chose naming partly to keep the prompt cost bounded. A reading of the spec chosen for cost is your call, not mine.
- SETTLED: D2: R18 lists `eject` as one of the new steps in `runs/land-step.md` and asks the board to show it as a stop. The build does exactly that: `LAND_STEPS` gains `stack` and `eject`, the board shows `eject` as a stop, and `test_a_train_member_shows_its_place_and_an_ejection` pins it. The record's problem line carries R7's `ejected from the train: <reason>`, so R7's "records a stop" is met in substance.

**For the person at ship**
- **The trade you're accepting.** In a train only the tip is gated, so the base passes through prefixes (changes 1..k with their `Close` commits) that were never gated alone. The spec states this under *Contracts touched*.
- **`scripts/sdlc.py`.** Look at:
  - `cmd_close()`'s lock span, from before `merge --ff-only` to the end of `_close_commit()`.
  - The reentrant `_main_lock()` and `_inherit_lock()`.
  - The `LOCK_HELD_ENV` pop as the function's first act.
  - `_handoff()` setting the variable only while it holds the lock.
  - `_carries_others()` refusing before any write.

  Hand `/sdlc:close` in every host runs this code.
- **`factory.py`.** Look at:
  - `cmd_train()`'s bisection and ejection (`reset --keep` to the pre-train commit).
  - `cmd_land_close()`'s expected-tip check and its `rebase --onto <trunk> <on[k]>`.

  The code reviewer only sampled `factory.py`'s roughly 940 changed lines and did not trace stack, bisect, eject or move line by line. Those paths rest on `tests/test_train.py`.
- **`cmd_land()`.** It now stops at `state: committed`. Four tests were removed from `test_land.py` as made obsolete. `plan.md` says R2's and R10's tests cover what they proved.
- **The land skill's new question wording** (R16).

- IMPACT: minor — a factory host's `/sdlc-factory:land` can now land a batch as one train: stacked, gated once at the tip and bisected when red. Hand ship and close keep their behaviour, apart from close's longer lock and its new refusal of a branch carrying another change's commits.

**Each undone item's disposition**
- UNDONE: `factory.py resolve` without `--onto` still rebases onto the base branch: no skill runs it that way now (the land skill always stacks with `--onto`), and only the register-conflict tests in `tests/test_land.py` exercise it. Fold it into `--onto <base>` or drop it once those tests are rewritten over a train. → seed: Fold `factory.py resolve`'s base-branch rebase into `--onto <base>`
- UNDONE: After `resolve --continue`, the landing agent's reply (`build/land-<n>.md`) and the `runs/land-resolved` marker stay uncommitted until the close amends them, as before the train; staging them with the other mid-rebase records (`RESOLVE_RECORDS`) would leave the tree clean after every stack. → seed: Stage the landing agent's reply and `land-resolved` with `RESOLVE_RECORDS`
- UNDONE: `tests/test_train.py`'s `_drive()` and `tests/test_land.py`'s `_land_train()` both drive a train as the skill does; one helper in a shared test module would do. → seed: One shared test helper that drives a landing train

The prompt names no irreversible paths, so there are no recovery lines.
