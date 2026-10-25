# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `work/ideas.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Deviations from the plan

- `templates/nits.md` is a title and a note only, like `templates/ideas.md`, not a `## How an
  entry reads` section with a fenced example. Ship `Write`s the template as it is, and a `## `
  heading there would be read as a malformed entry. The note carries the format. `nit_entries()`
  still skips fenced lines.
- `test_this_repos_register_reads_clean` asserts no problems and that each entry names its change
  and date, not exactly nine entries: the count drops as later ships retire them, and a pinned nine
  is a test only a revert could fail.
- R12's details (paths, pass, what's wrong) came from each change's `Sdlc-Findings` trailer and
  the code; 003-1's wording follows the seed's, since its notes didn't say more.
