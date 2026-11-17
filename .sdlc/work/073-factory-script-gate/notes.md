# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

The gate's output is kept indented in `build/round-<N>.gate.md`, not fenced as the plan said: a line
of a host's output that opened or closed a fence, or read `## Attempt`, could otherwise be read as
part of the record. `read_gate()` reads only lines at the margin.

`cmd_gate` doesn't refuse when `verdicts` names another step, unlike `agent`: a step outside the
loop (072's land, after a rebase) has to be able to run it. Only an attempt on the current build
moves the loop.

- [ ] R12: `plugins/factory/skills/land/` isn't on `main` while this is built, so 072-factory-land
  has to make land's post-rebase step run `factory.py gate <NNN>` when it rebases over this change.
  Its R5 still says "one `reviewer-behaviour` round … which runs the gate", and that reviewer no
  longer runs the gate.
