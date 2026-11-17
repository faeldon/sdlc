DECISION: ESCALATE

**Why:** The build covers R1–R14 and the gate passed (`./check.sh`, 2008 tests). Round 1's only CHANGE was dropped by the verifier, and the code confirms the drop was right. It is escalated anyway for two reasons. D1 is still an unconfirmed default, and it is the reason the build adds a `resolve` fix the spec doesn't name. And the change widens what one landing yes approves: running acceptance checks and paid skills' cases, writing to the register and ticking decisions. A person should look at that before it reaches `main`.

**Open items**
- None open. The code reviewer's C1 (a rerun is refused because the register changes `accept_build`'s digest) was dropped by the verifier, correctly: `_changed_paths()` leaves out everything under `work_rel()`, which covers the default register `.sdlc/work/inbox.md`. One residual gap the verifier also raised: if a host's `work.register` points outside `.sdlc/work/`, `_dispose()`'s append would change the digest, and a rerun after a `ship` refusal would need `accept` again. No test pins this either way.
- The reviewer's optional note, not a CHANGE: `unrecovered()` accepts a glob or a comma-separated list of subjects. That is lenient, and no test pins a `RECOVER` line whose glob covers a different directory.

**Decisions to confirm**
- D1: keep the `resolve` counter-only conflict fix in this change rather than splitting it out. The build assumed **keep**. It sits in `cmd_resolve` and splits the land skill's Step 3 into two blocks. `plan.md` records it as found while building R13.

**For the person at ship**
1. `cmd_resolve` in `factory.py` (D1). It now continues a rebase when `.sdlc/last-id` is the only conflict, for at most `RESOLVE_STEPS` commits. Check that it can't continue past a real conflict.
2. The landing's Step 3 in `plugins/factory/skills/land/SKILL.md`. `factory.py accept` and `factory.py cases` should appear only in prose, never in `allowed-tools` or a bash block. Also check the new `clean` branch next to `rebased`.
3. `cmd_land`. Every refusal (R7 and the missing-`RECOVER` exclusion) should come before `_dispose()`, and `_dispose()` should write nothing twice on a rerun.
4. `accept_build()` and `_accept_state()`. Decide whether the out-of-folder register case above needs a guard now or can become a seed.
5. `land_question()`'s wording. This is the one question the person answers for a whole batch, so it is what the yes now approves.

- IMPACT: minor — someone using sdlc-factory can now land a change that has acceptance checks, skills' cases, undone notes or assumed decisions through `/sdlc-factory:land`, behind one yes, instead of shipping it by hand. The new `factory.py accept` and `factory.py cases` commands and the approver's `UNDONE`/`RECOVER` lines are additions, and nothing existing stops working.
