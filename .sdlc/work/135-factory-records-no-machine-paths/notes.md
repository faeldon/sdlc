# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- [x] pre-existing: plugins/factory/scripts/factory.py:1348: the same tokenisation makes `git -C <path-to-clone> status` a non-read, since `CLONE_MARK` already has `<`/`>` in it. The fix above covers both marks, so it can be filed with this change or on its own. → dropped: fixed by this change: `is_read()` now swaps both `<home>` and `<path-to-clone>` before tokenising, and `test_a_read_naming_a_mark_is_still_a_read` covers both marks.
