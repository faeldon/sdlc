# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

A scratch host set up on `main`'s plugin (full `defaults/SDLC.md`, recorded by `main`'s
`record`), with one prompt filled and the `cost:` bullet edited, migrated through this change's
`answers process`: it kept those two blocks, cut the other 39, and `record --answers process`
then gave `layout: answers` with the guide's path, and `drift` nothing.

The kept block holding the filled prompt is the whole old `## The point of the process` section,
the plugin's paragraph and the second, unfilled prompt included: a block is kept or cut whole,
under the key it had. Setup's diff shows it for the person to tidy. This repo's own migration was
placed by hand into the new slots for the same reason.

- [x] `answers` moves a filled prompt's text into the guide slot that now asks for it (the old
  `## The point of the process` answer to `### The failure it stops`, and the rest), so a
  migrated host's answers sit where the template's would. → seed: 2026-10-27-10
