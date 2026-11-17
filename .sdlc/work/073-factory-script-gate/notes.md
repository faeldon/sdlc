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

R12: 072-factory-land reached `main` while this was built, so this change wired the gate into
land itself, after rebasing onto it. `factory.py gate <NNN> --land` gates the change as rebased (its
`Build:` is the commit, `HEAD`, not a report and snapshot), into `build/land-<n>.gate.md`, kept out
of `reviews/land-<n>/`, which `_land_task`'s verify reads file by file as reviews. `land-verdicts`
names `gate` before any landing reviewer, and a red gate there is a `stop` with no fix: a landing
has no builder round, so the person ships the change by hand. The land skill runs it before the
behaviour check after a clean rebase, and before the reviewers after a resolved conflict.
