# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- [x] pre-existing: plugins/factory/scripts/factory.py:2497: `_free_port()` has the same pick-then-bind window this change closed in the board tests. It serves the UI review's dev server, which is given `{port}` and can't bind 0 itself. The builder's decision D1 defaults to a seed of its own, but no such seed is in `inbox.md` yet. Carried to 2026-11-17-19.
