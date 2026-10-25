# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `work/ideas.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Deviations from the plan

`after_bump()` took its `untracked` list before `restore()` ran, so a new file the command had
staged was unstaged into an untracked file the report never named. The test for a staged new file
caught it, and the list is now taken after `restore()`. The same gap after a later step fails
(prepare or commit) is left as nit 022-1.
