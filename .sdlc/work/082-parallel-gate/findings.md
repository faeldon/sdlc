# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.
>
> Fresh review: ran. It raised the same three findings as this review's own passes, and added
> that notes.md misstates the cause of F1, which F1's fix corrects.
>
> Skill evals: skipped, the diff touches no skill (`cases`' scope is empty).

## F1. [important] [contract] The change folder holds this machine's home path, so the gate is red

Six lines of the factory run's records, which commit with the folder, hold the absolute path of
the clone, and `test_nothing_in_the_repo_is_forbidden` fails on them: `round-1.gate.md`'s Attempt
2 copied `claude plugin validate`'s output, which prints absolute paths, after the builder's hand
redaction of Attempt 1, and two reviewers quoted it. notes.md's second undone line blames a red
gate's xdist worker line alone, but a green record carries the path too.

Evidence: .sdlc/work/082-parallel-gate/build/round-1.gate.md:104, :106, :122, :124; .sdlc/work/082-parallel-gate/reviews/round-1/test.md:3; .sdlc/work/082-parallel-gate/reviews/round-1/behaviour.md:43; tests/test_nothing_local.py:29; .sdlc/work/082-parallel-gate/notes.md:36
Class: a workspace path leaked into committed artifacts; the three files above are every instance in the diff (F2 is its source)
Disposition: fixed
Fix: replace the clone's absolute path with `<path-to-clone>` in round-1.gate.md lines 104, 106, 122 and 124 and in test.md:3, write `<path-to-clone>/...` for the elided home path in behaviour.md:43, and reword notes.md's second undone line to say every gate record carries the path, green or red, from `claude plugin validate`'s output as well as xdist's worker line

## F2. [pre-existing] [correctness] `factory.py gate` records check.sh's output without redacting the checkout or home path

The gate copies the output's last lines verbatim into `build/round-<N>.gate.md`, which commits
with the change, so every gate record on this repo carries the machine's home path and turns the
next gate red. 083's records already put it in `a17dd91` and `90d71b9`, both on `main`.

Evidence: plugins/factory/scripts/factory.py:1210
Class: command output copied into a committed record without redaction; this is the one writer
Disposition: recorded

## F3. [nit] [context] CONTRIBUTING's new sentence claims every test makes its own scratch repo, and runs past the wrap

Some tests read the real checkout (`test_nothing_in_the_repo_is_forbidden` on `ROOT`), and the
board tests share a port race; the line also runs to about 125 characters where the file wraps at
100.

Evidence: docs/CONTRIBUTING.md:81-82; tests/test_nothing_local.py:112; tests/test_board.py:293
Class: a doc claiming more than the code ensures; the only instance (AGENTS.md's lines are accurate)
Disposition: fixed
Fix: write "The tests run in parallel (`pytest-xdist`), so none may depend on running alone or in order." and rewrap the paragraph at 100 characters
