# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.
> Skill evals: skipped, declined at ship

## F1. [important] [correctness] Ship runs `run-cases` through main's script, which lacks it

Ship names `sdlc.py run-cases <NNN>` from the change's worktree, through the installed plugin's
script. `OWN_SCRIPT_CMDS` lists the commands that hand off to the change's own `scripts/sdlc.py`,
and `run-cases` isn't one, so a change that adds or edits it (this one, the first to ship with
cases) runs main's copy, which refuses an unknown command.

Evidence: scripts/sdlc.py:3935
Class: a command ship runs left off the own-script list; `cases` is read by no skill, so only `run-cases` needs it.
Disposition: fixed

## F2. [nit] [correctness] A run that writes no result exits 1, which ship's text doesn't cover

`cmd_run_cases` reports `problems: ["no result written"]` and exits 1 when `claude plugin eval`
ends without a `result.json` (a case that failed to load, a run that couldn't start), but ship's
Step 1 knows only `skipped` and `failed`, so the session has to guess. It is a run that didn't
happen, the same as an unavailable eval.

Evidence: scripts/sdlc.py:2678
Class: an outcome the caller's text doesn't name; R14's other no-run outcomes are `skipped`.
Disposition: fixed

## F3. [nit] [context] CONTRIBUTING sends tracker authors to the fake gh's old home

The tracker section says to drive a tracker's tests through a fake on `PATH` "as
`tests/test_archive.py` does for `gh`"; the fake and its fixture now live in `tests/conftest.py`.

Evidence: docs/CONTRIBUTING.md:191
Class: a doc naming a file the diff moved code out of; the gate's paragraph at line 74 was updated.
Disposition: fixed
