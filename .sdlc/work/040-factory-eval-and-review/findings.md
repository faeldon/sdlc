# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.
>
> Fresh review: not run: this diff touches no `[review] sensitive` path.

## F1. [nit] [correctness] The review proposes severities it may not be able to read

`/sdlc-factory:review` proposes each bug's `Severity:` from the process doc's words, but a host
whose own process doc has no bugs section takes them from `sdlc`'s guide, which the factory's
cached copy can't read. `/sdlc:bug` checks the word before filing, so nothing wrong lands; the
review could leave `Severity:` for `/sdlc:bug` to ask when the host's doc has no words.

Evidence: plugins/factory/skills/review/SKILL.md:75
Class: the factory reaching for what only `sdlc`'s copy holds; the pinned copies are the other case, handled
Disposition: recorded
