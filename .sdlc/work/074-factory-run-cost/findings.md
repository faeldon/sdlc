# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

Skill evals: skipped, the diff touches no skill with a case (`cases`' scope is empty).

## F1. [important] [correctness] A landing's conflict resolution aborts on the builder's own cost line

`/sdlc-factory:land` commits the change, `runs/costs.jsonl` included, then rebases it. On a
conflict, the builder's `resolve` run goes through `cmd_agent()`, which now appends its cost line
to that tracked file mid-rebase. `resolve --continue` stages only the conflicted files, so `git
rebase --continue` refuses on the unstaged `costs.jsonl`, and `cmd_resolve()` aborts the rebase
reporting "a second conflict … ship it by hand": a wrong diagnosis, and the change doesn't land.
A scratch-repo probe reproduced the refusal (exit 1); the same steps without the cost line
continue (exit 0).

Evidence: plugins/factory/scripts/factory.py:1334-1335 (record_cost in cmd_agent), against plugins/factory/scripts/factory.py:1728-1731 (cmd_resolve stages only the conflicted files before rebase --continue)
Class: a new write reaching a path an earlier change assumed clean; 072's mid-rebase writes were all new untracked files
Disposition: fixed
Fix: in cmd_resolve's continue path, before `git rebase --continue`, stage the change's own `runs/costs.jsonl` when it exists (`_git(root, "add", "--", (folder / COSTS).relative_to(root).as_posix())`); add a test in tests/test_factory.py that builds a rebase conflict from `_from_main`, appends a cost line mid-rebase, and asserts `resolve --continue` reaches `resolved` with the line in the rebased commit
