# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.
>
> Fresh review: not run: this diff touches no `[review] sensitive` path.

## F1. [nit] [correctness] A report stopped for missing evidence has no way back but a hand edit

`verdicts` stops on a builder report without `## Evidence`, and the build skill's `stop` says
only to report and stop: rerunning the build hits the same report, and the skill forbids patching
an agent's reply. The stop could name the way on: resume the builder to report again with its
evidence, written by the usual rule.

Evidence: plugins/factory/skills/build/SKILL.md:176
Class: a new stop with no stated recovery; the no-verdict stop has the same shape, already on main
Disposition: fixed
