# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry` writes its agents' findings
> into it; `By:` names who raised one: `fresh` for ship's fresh-context reviewer, a factory role
> (`code`, `test`, …) for an agent, and no line on ship's own. A rerun keeps each id, marks one the
> diff no longer shows `fixed`, and never raises again one the person answered `wrong`,
> `intentional` or `minor`; an agent's `wrong` is its verifier's, never the person's, and the same
> fault worded differently is one more. `sdlc.py` reads each heading and its `Evidence:`, `Class:`,
> `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts ship's own alone into the
> `Sdlc-Findings` trailer (its `agents=` says how many it left out), words ship's question from
> the ones proposed `fix`, and `ship` refuses while one is still `open` or `fix`. On a diff that
> touches a sensitive path, this note also says `Fresh review: ran`, or `Fresh review: skipped,
> <why>`.

Skill evals: ran, 2 of 2, on the skill text before this ship's rebase onto main, which brought 129's edits to skills/ship/

## F1. [nit] [correctness] the new *Closing* lines and the *The register* paragraph (around line 166) run past the file's ~100-column wrap, so reflow them

AGENTS.md:118-119: the new *Closing* lines and the *The register* paragraph (around line 166) run past the file's ~100-column wrap, so reflow them

Evidence: AGENTS.md:118-119
Class: code review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F2. [nit] [correctness] scripts/sdlc.py:~3490: the register-edit check in `cmd_ship` does `ideas.resolve().relative_to(tree.resolve())`.

scripts/sdlc.py:~3490: the register-edit check in `cmd_ship` does `ideas.resolve().relative_to(tree.resolve())`. That raises `ValueError` if the register path sits outside the tree, and only an `ideas.parent.is_dir()` guard stands between that and a crash. Use `try/except` or compare against `_shown()`

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [nit] [correctness] scripts/sdlc.py `register_plan()`: an id named in both `fixes:` and a `Retire` line is processed once through `dict.fromkeys`, which is correct.

scripts/sdlc.py `register_plan()`: an id named in both `fixes:` and a `Retire` line is processed once through `dict.fromkeys`, which is correct. A one-line test would pin that

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F4. [important] [contract] The branch's own register edit: three entries an earlier landing appended to inbox.md

.sdlc/work/inbox.md, as this branch has it uncommitted, holds three entries main doesn't: the two seeds the notes carried (2026-11-18-23, 2026-11-18-24) and the code reviewer's nit (2026-11-18-25). An earlier landing attempt wrote them with main's old `_dispose()`, before this change's code ran. That is the register edit R1 forbids. `sdlc.py ship`, now this change's own code, refuses it (R11), and the entries would ride the commit and conflict on the next rebase.

Evidence: .sdlc/work/inbox.md:297-318
Class: a register edit on a change's branch
Disposition: fixed
Fix: Move the three entries, whole and unchanged, into .sdlc/work/134-register-never-conflicts/entries.md under a `# 134-register-never-conflicts — entries` title, in id order. Then `git restore .sdlc/work/inbox.md`, so close files them in the `Close` commit.

## F5. [nit] [cost] New lines in the ship and land skills and REFERENCE.md run past the 100-column wrap

Eight lines the diff adds run past the wrap: in skills/ship/SKILL.md (Step 6's `ship` paragraph and the `Write is for those files only` line), plugins/factory/skills/land/SKILL.md (the register sentence) and docs/REFERENCE.md (its new register lines). This is the same reflow as F1's, in files F1 doesn't name.

Evidence: skills/ship/SKILL.md, plugins/factory/skills/land/SKILL.md, docs/REFERENCE.md
Class: style
Disposition: minor
Reason: the reflow F1's nit (2026-11-18-25) records takes these lines too; a second nit would split one tidy-up
