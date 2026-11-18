DECISION: ESCALATE

**Why.** The build looks complete. The code and test reviewers both gave `VERDICT: PASS` in round 1 and each matched all 14 requirements to a test. The gate passed `./check.sh` with 2428 passed and 13 skipped. I am still escalating for two reasons. Two builder decisions, D1 and D2, are unticked defaults that the build rests on. The change also rewrites two contracts the spec itself marks "⚠ … Your call": what a `Close` commit holds, and who commits the register. That changes the host-facing behaviour of ship, close and drop.

**Open items**
- None blocking. Three nits were recorded or set to minor in `findings.md`, all from the code reviewer:
  - F1: AGENTS.md lines run past the wrap.
  - F2: `relative_to` in `cmd_ship` has no `try`.
  - F3: no test for an id named in both `fixes:` and a `Retire` line.
- No reviewer and builder disagreed, and no Critical or High finding is open.

**Decisions to confirm**
- D1: `drop` refuses only when `entries.md` holds entries. A file with only `Retire` lines does not block a drop; those retirements are simply lost with the dropped change.
- D2: `held_entries()` accepts `>` note lines and the `# ` title before the first entry. Any other stray line is refused, and the refusal names the line.

**For the person at ship**
- Look first at `_close_commit()` and `cmd_close()` in `scripts/sdlc.py`. Check three things:
  - The register write and the folder's `git rm -r` go into one `Close` commit under `_main_lock()`.
  - The register is put back when a step fails.
  - The check before the merge (`register_plan()` from the branch) refuses what R6 says it should.
- Then read the reworded *The register* and *Closing* paragraphs in AGENTS.md, which carry the two policy edits. Then ship's Step 6 in `skills/ship/SKILL.md`, which now writes `entries.md`.
- Ship still needs a `Skill evals:` note, because `skills/ship/` changed.
- This change's own close runs the new code through `_handoff()`. Its folder holds no `entries.md`, so any seed it deleted the old way should be reported `gone`, not refused.

- IMPACT: minor — In a host, a landing no longer conflicts on the register, and entries now reach the register at close inside the `Close` commit. Ship now refuses an uncommitted hand edit to the register, and drop refuses while held entries exist. Branches shipped the old way still land as before.

**Undone items**
- UNDONE: Close takes `_main_lock()` only around its register write and `Close` commit, not from its merge: an `inbox-commit` that lands between the two puts a `File` commit between the change's commit and its `Close`, where `closed_changes()` reads the `Close`'s first parent as the change. That hazard predates this change (the folder's removal had it too); holding the lock from the merge would close it, at the cost of blocking `/sdlc:idea` through the archive step. → seed: Close holds the main lock from its merge to its Close commit
- UNDONE: `test_close_and_inbox_commit_keep_both_entries` (R7) files the idea between close's check and its locked write, so it proves the reread under the lock, not two processes racing for it. A threaded test, like `claim()`'s, would prove the lock itself. → seed: A threaded test that close and inbox-commit contend for the register lock
