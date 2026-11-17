DECISION: READY

**Why.** All ten requirements are built. Both round-1 reviewers returned `VERDICT: PASS` and found every requirement from R1 to R9 in the code, each with a test that fails without it. They checked R10's docs at review. The builder's `./check.sh` passed (2254 passed, 13 skipped, both plugins validated). The record in `build/round-1.gate.md` agrees: PASS on build `8609214be8501298`, tree unchanged. One design question needed the person: whether `sdlc.py` may read the base branch's `gate_jobs` and lock the factory's slot files, which widens AGENTS.md's factory contract. The intent records that the person approved it, and the 30-minute limit was settled the same way. The AGENTS.md edit as built says what was approved.

**Open items.** None. The reviewers left only nits, and none asks for a change:
- code reviewer: the waiting line's "(N of N in use)" always shows a full count. This matches the factory's own wording.
- code reviewer: `_try_lock` copies the factory's version and is pinned only by how it behaves. This is by design.

**Decisions to confirm.** None. There is no `decisions.md`, and the builder raised no decisions.

**For the person at ship.**
- **`cmd_gate()` in `scripts/sdlc.py`.** Building the hash and taking the `before`/`after` digests now happen inside the `with _hand_slot(...)` block. Check that the `SlotTimeout` refusal returns before any record is read or written (R4).
- **AGENTS.md, the factory paragraph.** Check the new clause ("the base branch's `gate_jobs` and the gate slots' lock files, for the hand gate (`_hand_slot()`)") against what you approved. This is the one contract this change widens.
- **R3's test in `tests/test_hand_gate.py`.** The test reviewer read only its tail and wasn't sure the checkout's `8` is set in every case. The code reviewer says it is. Confirming takes a minute.
- **Test flakiness.** The R2 test failed once on timing before the builder made it wait for the factory's waiting line, so look over R1 and R2 for anything else that depends on timing.

**Release impact.**
- IMPACT: minor — with `sdlc-factory` enabled, `sdlc.py gate` now waits for a gate slot and can refuse after 30 minutes, and its JSON summary gains `waited` and `slot`. Without the factory nothing changes, and nothing anyone already relies on breaks.

**Undone items.** None. There is no `notes.md`, and the builder reports none was written.

**How to recover.** The prompt names no irreversible paths. If needed, `plan.md`'s Rollback applies: `git revert` undoes the change, and while no gate runs, `rm "$(git rev-parse --git-common-dir)"/sdlc-factory-gate-*.lock` removes any lock files a hand gate created. These files are empty and harmless.
