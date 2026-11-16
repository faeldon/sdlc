# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Checked by hand

What only GitHub can show, after the next `/sdlc:publish`: `gh run list --workflow check.yml -L 3`
lists one run for the release commit and none for its tag. The trigger itself is pinned by
`checks.md`; ship's fresh review moved it there from the suite, as a test only a revert could fail.
