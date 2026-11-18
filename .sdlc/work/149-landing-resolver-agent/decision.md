DECISION: ESCALATE

**Why.** The build is ready: in round 2 all five reviewers (code, test, behaviour, ui, ux) passed. Round 1's one kept change (ux: the board card said "its builder is resolving a conflict") is fixed. The gate is green: `./check.sh` ran 2838 tests, all passed (28 skipped), plugin validation passed, and the tree was unchanged. In round 1 the code and test reviewers each matched R1–R14 to code and a test that would fail without it. I'm escalating for one reason only: the change touches published interfaces, which is the person's call even though the spec named these changes and was approved.

**Open items**
- None. Every round-2 verdict is PASS. F1–F3 in `findings.md` are nits recorded as minor: a long line in AGENTS.md (code), `.sdlc/last-id` possibly counted as stray (code), and a fence test with no case labels (test).

**Decisions to confirm**
- None. D1/R1 ("fold -73 into 149") was decided by the person and the build follows it (spec R14, tested in both `factory.py` and `sdlc.py`). No default is open.

**Every other reason I escalate for**
- ESCALATED: look: the change touches published interfaces that every factory host sees. It adds a new `[models] resolver` config key (sonnet by default), adds a new value, `resolver`, to the `Sdlc-Role` metrics trailer, and changes the AGENTS.md rule that only the builder edits. It also adds a new refusal in `resolve --continue`: any resolution that edits outside its conflicted files is refused. That covers the builder's single-change `resolve` and a person's hand resolution too, and a host whose tests leave untracked files behind. All of it adds to existing contracts and the approved spec names each one, but the build itself should get a look before it reaches `main`.

**For the person at ship**
- First, `factory.py`'s `cmd_resolve --continue` fence (`_status_entries()`, `_stray()`, around line 6966). It reads one `git status --porcelain -z` listing, splits it into conflicted and changed paths, and refuses before anything is staged. Check F2: a `.sdlc/last-id` left modified after `_rebase_settling()` would be counted as stray.
- Then the `cmd_agent` guard that makes `train-resolve` refuse any role but `resolver`, and the new `plugins/factory/agents/resolver.md`: its tools, the never-run wording and its merge-only rules.
- Last, the `-z` readers in `_conflicted()` and `sdlc.py`'s `_unmerged()` (R14), and the reworded AGENTS.md paragraph (F1's long line).

- IMPACT: minor — factory hosts can now set `[models] resolver`, and a landing's conflict work shows as its own `Sdlc-Role: resolver`. Nothing they already do has to change, though a resolution that edits outside its conflicted files is now refused at `--continue` instead of being carried along.

There is no `notes.md` and no undone item, so there are no UNDONE lines. The prompt names no irreversible paths, so there are no RECOVER lines either. `plan.md`'s Rollback is a plain `git revert`.
