DECISION: ESCALATE

**Why.** The build looks sound. All 14 requirements have code and a named test, both round-1 reviewers returned `VERDICT: PASS` with no CHANGE findings, the gate passed (`./check.sh`, 2189 passed), and D-ledger item R1 is ticked by you. I'm escalating for one reason. The change alters what gets deleted from the register, and one part of that is a widening you never approved. `drop_entries()` now ends an entry only at a level-1 or level-2 heading, and `retire_nits()` became a call to it. So ship's own nit retirement now deletes a `###` block inside a nit that it used to keep. `plan.md` doesn't mention this. It appears only in `notes.md`, and the code reviewer raised it as Optional. Separately, nobody ran the two manual scratch-landing checks from the spec.

**Open items**
- None open as CHANGE. Two Optional notes from code: the resume branch's `_git(root, "show", f"HEAD:{INBOX}")` may return empty or None, and should use an explicit `or ""`. The `###` behaviour change in `retire_nits()`/`drop_entries()` isn't documented in their docstring.
- The test reviewer didn't run `./check.sh` itself, and read only four of the new tests in full. The gate record covers the first point.

**Decisions to confirm**
- None. R1 is ticked: you approved dropping retired nits in R13, id-only matching, and widening mends to the approver, the verifier and landing rounds.

**For the person at ship**
1. In `plugins/factory/scripts/factory.py`, look at `drop_entries()` and `ENTRY_END_RE` first. Confirm you want ship's nit retirement to delete through a `###` up to the next `## ` heading. That is R13's wording, but it now applies to `retire_nits()` too.
2. Look at `cmd_land()`'s new resume branch (`_commit_failed()` / `_land_commit()`). It reruns `sdlc.py ship` and commits. Check that it can only fire when `HEAD` has no `Sdlc-Landed:` line and `HEAD:intent.md` isn't `stage: shipped`. Also check what `nits` becomes when `HEAD` has no register.
3. Look at `cmd_resolve(cont=True)`'s register drop: it should act only when `inbox.md` conflicted, and match by id only.
4. Look at the `AGENTS.md` factory paragraph. Its contract widens: the approver's and verifier's replies can now be mended, and so can replies in landing rounds.

- IMPACT: minor — factory users can newly run `agent --task land-mend` and get approver and verifier mends, and a landing now mends instead of stopping on a missing `exit:` or a preamble. A failed landing commit can now resume. Nothing anyone already relies on has to change.

- UNDONE: `_resolve()`'s problems still say "round <n>" for a landing round's answer ("C3, which no change of round 1 is"); only the file named before them says which kind of round it is. → seed: Name the landing round in `_resolve()`'s problems

**How to recover**
- No irreversible paths named. `plan.md`'s Rollback applies: `git revert` undoes all of it, and the `<role> land-<n>` lines in `runs/mended` are already skipped by the old `mended()`.
