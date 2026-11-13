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
> Skill evals: ran, 6 of 6 (`.sdlc/reports/cases-2026-11-13-7`, $1.69, after the rebase onto
> 054; `cases-2026-11-13-5` before it, 6 of 6 too). Every run ended at its literal text question,
> the fallback the `last_message` graders read; the result keeps no trace, so whether a run tried
> the dialog first is not recorded.

## F1. [important] [correctness] A dialog's wait is taken out of agent time the turn never held

`summarize()` subtracts each dialog's wait (`held`, `answering()`) from the turn it overlaps, but
Claude Code's `turn_duration` already leaves that wait out: this change's own intent run took 352 s
from the command, its two dialogs waited 86 s and 160 s, and the turn recorded 109 s. So the turn's
interval `[end - 109 s, end]` overlaps the last wait by about 46 s, and that much real agent time is
lost; a longer wait near a turn's end can zero it. R10's test passes only because its fake turn
includes the wait.

Evidence: scripts/metrics.py:855 (`answering()`, the `part`/`whole` lines); the session transcript's
`turn_duration` against its `AskUserQuestion` call and result timestamps
Class: an assumption about the harness's data taken from the spec, not read from a transcript;
nowhere else in the diff
Disposition: fixed

## F2. [nit] [cost] The dialog paragraph is repeated in all 17 gated skills

The same five lines sit in each WAIT step, so a wording change touches 17 files.

Evidence: skills/*/SKILL.md and plugins/factory/skills/*/SKILL.md, each WAIT step
Class: duplication across skills; the one-WAIT and allowed-tools rules are repeated the same way
Disposition: minor
Reason: each skill is loaded on its own and must carry its gate's rule; a pointer to a shared doc
would cost every gate a Read, and `test_every_wait_asks_in_a_dialog` keeps the 17 copies the same
