# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

Skill evals: ran, 2 of 2 (ship 1.0, ship-open-finding 1.0, $0.85, .sdlc/reports/cases-2026-11-17-3)

## F1. [important] [correctness] Ship's Step 3 still calls findings.md the one write besides base

Step 0 now says `base`, a conflict's resolution and `findings.md` are three writes before the
WAIT, but Step 3's paragraph on writing `findings.md` still says it is "the one write besides
`base` this skill makes before its WAIT". The skill contradicts itself on the rule that names what
may write before the gate.

Evidence: skills/ship/SKILL.md:234, against skills/ship/SKILL.md:71-73
Class: a rule changed in one place and left as it was in another; Step 0 and Step 3 both restate the named exception
Disposition: fixed
Fix: in skills/ship/SKILL.md:234, "This is the one write besides `base` this skill makes before its WAIT" becomes "This is one of the writes beside `base` and `resolve` this skill makes before its WAIT", on the same line, so the 475-line budget holds

## F2. [nit] [cost] A Step 0 line runs to 162 columns

The edit that brought ship's `SKILL.md` back under its line budget left one Step 0 line at 162
columns.

Evidence: skills/ship/SKILL.md:74
Class: a reflow traded for the line budget
Disposition: minor
Reason: the file already holds 20 lines over 100 columns and nothing checks its width, and rewrapping this one would put it past the 475-line budget its test enforces

## F3. [nit] [correctness] Spec R7 aborts on any failing gate; conflict.md only on one in a resolved file

R7 says a gate failing after a resolution stops with `resolve --abort` run. `conflict.md`'s Step 1
aborts only when the failure sits in a file the resolution merged, and reports any other failure
as a failing gate. The narrower rule is the right one (an unrelated failing test shouldn't undo a
good merge), so the spec is what's wrong.

Evidence: .sdlc/work/077-ship-resolves-conflicts/spec.md R7, against skills/ship/conflict.md "## Step 1"
Class: the build refined a requirement and the spec wasn't updated
Disposition: fixed
Fix: in spec.md R7, "or the gate failing after a resolution" becomes "or the gate failing in a file the resolution merged (any other failure is reported as a failing gate is)"

## F4. [nit] [correctness] A merge that empties one of the branch's commits stops the resolution

If merging a conflict leaves a commit with no changes of its own (the change made an edit the base
also made), `git rebase --continue` refuses with "No changes", `resolve --continue` reports "the
rebase won't go on", and conflict.md's second-refusal rule has ship abort and stop. Nothing is
lost, but ship stops for nothing. The fix is `git rebase --skip` on that one answer, which needs
care: the skipped commit may be the aside commit, which finish() then mustn't reset.

Evidence: scripts/sdlc.py cmd_resolve's continue branch ("the rebase won't go on")
Class: an edge of git's rebase the tests don't reach
Disposition: recorded
