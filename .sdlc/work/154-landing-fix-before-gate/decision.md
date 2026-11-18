DECISION: ESCALATE

**Why**

Both round-1 reviewers passed this change, and the gate is green on the current build: `./check.sh` ran 2832 tests, 28 skipped, with validation passed. Every outcome in the intent has code and a test. The new test, `test_a_fix_the_gate_needs_is_made_before_the_gate`, failed before the code change and passes after it. The only thing holding the change back is D2: whether you should be able to ask for a fix after the gate. You raised that yourself as an open question in the intent, and it's a question about scope and about how you answer at landing, so only you can settle it.

**Open items**

- None. No reviewer asked for a change. The one remaining finding, F1 from `code`, is a nit and is recorded in `findings.md`.

**Decisions to confirm**

- SETTLED: D1: the fix comes after a conflict's resolution. The intent's Approach puts the fix "right after `stack`", and its Constraints keep the re-stack unchanged. `plan.md` (step 2: "or its conflict resolved") and `_train_reading()` take the resolution first, so the fix is gated on the commit that will actually land. Both reviewers confirm this order.
- ESCALATED: D2: the intent asks, as your own open question, whether you should be able to say a fix is meant for after the gate. Adding a second answer to `yes, with a fix` is a scope and policy call about the landing question you answer, not something the code can decide. The default (always before the gate, one rule) matches the intent's Approach, which drops the before-close placement. Confirm it, or ask for the choice.

**For the person at ship**

- Read the change to `_train_reading()` in `plugins/factory/scripts/factory.py`. Check that `fix` is now named inside the stacking loop, and that the old step-5 placement before close is gone.
- Read `cmd_land_fix()` at about lines 5879–5886. These are the new rules for when an open round takes the fix:
  - An open round that no reviewer has answered and that has no ask yet takes the fix itself.
  - An answered round still refuses the fix until it passes.
  - On line 5881, `iterdir()` has no `.is_dir()` guard (that is F1).
- The behaviour reviewer's `git diff main --stat` listed `.sdlc/work/inbox.md`, but `build/round-1.files` doesn't. That is probably `main` having moved on since the branch was cut. Confirm the register isn't riding on this branch.

**The release impact you propose**

- IMPACT: patch — a landing's `yes, with a fix` now takes effect before the gate it was meant to fix, instead of being skipped when the change is ejected. The words you give and the landing commands stay the same; landing just works better.

**Each undone item's disposition**

- `notes.md` doesn't exist and the builder left nothing over, so there are no undone items.

**How to recover**

- The prompt names no irreversible paths. `plan.md`'s Rollback is `git revert`, and nothing outside git changes.
