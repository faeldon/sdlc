# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## D1, fixed by hand after the approver

The approver escalated on D1 alone (the plan hint read every line of `## Files to change`, which
counted 14 "files" on this change's own plan, wrapped lines' dotted names among them). At landing
the person decided "list items only, fixed before 088 lands". The factory couldn't take it back
once `decision.md` was written (`verdicts` reads `done`; 095 closes that gap), so the supervisor
made the fix in this worktree, outside the factory's rounds: `_plan_named()` reads only list items,
spec R11 says so, and `test_the_plan_hint_counts_named_files_the_branch_touched`'s plan gained a
wrapped line with a dotted name, red before the fix and green after. This plan now names 9 files.
No reviewer read the fix; the landing's gate and behaviour check run on it after its rebase.

- [x] The code reviewer's three optional notes from round 1 (`_progress()` null for a `decide`
  record without `AFTER:`, the stopped check partly repeating `_stopped()`, the bar's percentage
  computed twice): left as they are, minor, none affects what a card shows.
