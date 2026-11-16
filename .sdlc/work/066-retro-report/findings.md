# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [nit] [correctness] A failed commit leaves the report behind, and the rerun refuses it

`retro-commit` writes `.sdlc/retros/<today>.md` before its `git add` and `git commit`; when either
fails, it returns with the file still on disk, and the next run refuses it as "already exists",
so the person must delete a file they never wrote before a retry works.

Evidence: scripts/sdlc.py:7096
Class: a write that a later failure leaves half-done
Disposition: fixed

## F2. [nit] [context] retro-commit's docstring and help still say it commits nothing else

`cmd_retro_commit`'s docstring says the commit holds the direction doc, the register and the
product doc "and nothing else", and its `--help` says "commit the direction doc and the inbox":
both now leave out the report it writes and commits.

Evidence: scripts/sdlc.py:7019
Class: a summary left behind its code
Disposition: fixed

## F3. [nit] [correctness] R5's "never runs the host's commands" has no test

`retro_report` skips `_evidence`, but `test_retro_and_its_report_show_the_same_figures` only says
so in its docstring: a later edit that routed the report through `retro()` would run
`retro.evidence` on every `retro-commit` unseen.

Evidence: tests/test_retro.py:1597
Class: a requirement only a docstring checks
Disposition: fixed
