DECISION: ESCALATE

**Why.** The build is finished and reviewed. Round 3's code review is `VERDICT: PASS`, the gate recorded a pass on the current build (`./check.sh`, 2199 passed, 9 skipped), and the acceptance checks pass. What you asked for in the restart (R1, "wire unmark") is done: `sync` now calls `unmark()`. It escalates on two defaults, D2 and D3, which the builder assumed without you. It also now changes issues on GitHub: `sync` takes the `triaged` label off, clears the parent and posts a comment. A `git revert` doesn't undo that, and the intent's "comments only, no behaviour change" limit for `sdlc.py` was dropped because of R1.

**Open items**
- No CHANGE is open. In round 3, the code reviewer left one nit: reflow the short line mid-paragraph near `docs/CONTRIBUTING.md:199`.

**Decisions to confirm**
- D2: `unmark()` is called only from `sync`. It only touches an issue that this change marked, that still has `triaged`, that has left its `closes:` line and that nothing else records. Close's and `mark-triaged`'s marking pass are left alone, because close's pass would send just-fixed issues back to triage before the push closes them. The code reviewer accepted this.
- D3: every `sync` lists all open issues with their comments, even for a change with no `closes:` line. The listing is capped at 1000 issues. The code reviewer called it a fair trade-off. If it ever gets slow, the fix is to record which issues each change marked, not to skip the listing.

**For the person at ship**
- Read `withdraw_issues()` first (`scripts/sdlc.py` ~7543) and its call in `cmd_sync()` (~2258–2266). It is the one new behaviour that reaches GitHub. Check that `recorded_issues(home)` sees every record you expect, especially the `closes:` lines of other open changes that live only on their own branches. If it misses one, an issue those changes hold could go back to triage.
- Next, `closes_texts()`'s new `withdrawn` text (~5224), and `test_sync_sends_an_issue_that_left_the_closes_line_back_to_triage` in `tests/test_archive.py`.
- Then `docs/CONTRIBUTING.md` around line 193: the list of intake methods, with `unmark()` now marked optional.
- Then the intake paragraph in `docs/REFERENCE.md`, and the `--themes` paragraph in `skills/idea/SKILL.md` with its new rule for `sdlc.py status`.
- Last, check that the other `scripts/sdlc.py` edits are `#` comments only.

- IMPACT: minor — `sync` now sends an issue that left a change's `closes:` line back to triage, which it never did before, and `/sdlc:idea --themes` no longer proposes a theme for a seed that is being built. A host using the GitHub tracker will see labels and comments change on `sync`.

**Undone items**
- UNDONE: A full marking pass (close, `mark-triaged`) still leaves a core-marked issue whose record went (an entry's `Issue:` line removed by hand) as `dangling` for triage, not unmarked: close's pass runs between its Close commit and the push that closes the change's issues, so it would need `closed_by()` on the unpushed commits to tell a just-fixed issue from a withdrawn one. → seed: Unmark withdrawn issues in the full marking pass, using closed_by() on the unpushed commits

**How to recover**
- RECOVER: GitHub issues that `sync` sent back to triage: `gh issue edit N --add-label triaged`, delete the `<!-- sdlc:withdrawn:<name> -->` comment, and set the parent again. Or put the issue back on a change's `closes:` line and run `sync` again. `git revert` of the change undoes the repo's side (`plan.md`, Rollback).
