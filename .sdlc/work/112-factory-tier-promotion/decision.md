DECISION: ESCALATE

**Why.** I found nothing wrong with the build. All four round-1 reviewers returned `VERDICT: PASS` with no Critical or Required findings. Every requirement from R1 to R15 has a named test, or for R15 a `checks.md` check. The gate passed (`./check.sh`, 2287 passed). The person's one decision, to rename "promote" to "upgrade", is followed throughout. I'm escalating anyway, for two reasons:
- The change adds a command to a published interface: `sdlc.py upgrade`, listed in `docs/REFERENCE.md`, the contract hosts rely on. It also changes AGENTS.md's map so the factory runs `sdlc.py` in a third place.
- The spec itself asks ship's review to settle a policy question. `factory.py upgrade` writes the tier, the stage and two blank `spec.md`/`plan.md` templates before the spec's question is asked, and the spec argues this is not a fifth "writes before a WAIT" exception. That is the person's call, not mine.

Two parts of the diff were also only skimmed by every reviewer: the `sdlc.py` changes and the build skill's new question.

**Open items**
- None. No reviewer asked for a change in round 1.
- Optional, from code: `cmd_upgrade` only recomputes the round number `P` when no record exists yet. That is correct but uncommented.
- Optional, from code: the `upgrade` branch in `loop_state()` is skipped when `not decision` is false. A leftover `decision.md` on a Tier 1 change would therefore skip the upgrade, and no test covers that.

**Decisions to confirm**
- None. R1 in `decisions.md` is ticked: the person chose the name "upgrade" and the answer prefix `upgrade to Tier 2`, and the build follows it.

**For the person at ship**, in this order:
1. **`scripts/sdlc.py`.** Check three things:
   - `new`'s template filling, moved into `render_template()`. Every host's `new` now goes through it.
   - `cmd_upgrade()`'s in-place edits to the frontmatter and its four refusals.
   - `factory_upgraded_build()`, which widens the "live build" exemption in `check`.
2. **`plugins/factory/skills/build/SKILL.md`.** Check the fourth wording of the approval question, the stage moves Step 3 still owes, and that it still has exactly one `WAIT` heading. No reviewer read this closely, and ux did not read it at all.
3. **Whether writing the tier, the stage and the blank templates before the spec's question needs to be named as an exception.** The rule is the "Writes before a WAIT" paragraph in AGENTS.md.
4. **`plugins/factory/scripts/factory.py`.** Check the `--resume` condition in `cmd_agent()`, and that `decided` refuses while an upgrade is under way.

- IMPACT: minor — `sdlc.py upgrade` is a new command, and a factory run can now upgrade a Tier 1 change to Tier 2 mid-run on the person's answer; nothing that already exists changes.

**Undone items**
- None. There is no `notes.md`, and the builder reports nothing left over.

**How to recover**
- The prompt names no irreversible paths. `plan.md`'s Rollback applies as written: `git revert` undoes all of it, and nothing is published outside the repo.
