# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## How it differs from the seed

Seed 2026-10-26-7 named five nits. One, 2026-10-25-18 (a change sized from an intent committed
early), had already left the register, and the theme had grown to eight by the time this was
built, so this change pays down all eight robustness nits open on 2026-11-13.

Marking a `closes:` issue at `sync` labels it `triaged`, so one taken off the line later lets go
of its parent like any triaged issue; `test_sync_makes_the_change_s_issue_the_parent_of_each_issue_it_closes`
now uses a sub-issue added by hand for the one that stays.

The branch was rebased onto main twice during ship (055 and 056 landed meanwhile), each time by a
WIP commit, `sdlc.py base`, and a soft reset, with no conflicts.
