# Ship — agents' verdicts

`preflight`'s `branches` names this file when the change's folder has a `decision.md`: it was built
by agents (the optional `sdlc-factory` plugin).

## Step 0

A change built by agents has `.sdlc/work/NNN-slug/decision.md`, opening `DECISION: READY` or
`DECISION: ESCALATE`, and its reviews in `.sdlc/work/NNN-slug/reviews/round-<N>/<role>.md`, each
opening `VERDICT: PASS` or `VERDICT: CHANGES`, each round's verifier answers in
`reviews/round-<N>/verified.md` (`- KEPT:` for the builder, `- DROPPED:` with why), and the person's
calls the agents raised in `.sdlc/work/NNN-slug/decisions.md` (`- [x]` decided, `- [ ]` assumed,
and `- [x] … → superseded by D<m>` a default a later one replaced, neither decided nor assumed).
Read the decision, the highest round's reviews, every `verified.md` and the ledger: they are
evidence for Step 3, never a substitute for it. A dropped change your own passes confirm is a
finding like any other. The builder's reports in `build/round-<N>.md` and the behaviour check's
`reviews/round-<N>/behaviour.md` end with a `## Evidence` section, each command with its output and
exit: what the agents say they ran. `build/round-<N>.gate.md`, where there is one, is the script's
own record of the base branch's gate on each build before its review, every attempt with its exit.
Step 1's gate and acceptance checks still run for themselves.

## Step 3

**The agents' findings.** `findings.md` may already hold sections whose `By:` names a factory role
(`code`, `security`, `test`, `behaviour`, `ui`, `ux`): the agents' record, written by the factory's
`carry`. Keep each exactly as written, never re-disposition or renumber it, and number your own
after the highest id in the file. An agent's `wrong` is its verifier's drop, never the person's
answer, so it never stops you raising the same fault as a finding of your own.

## Step 4

**Agent verdicts.** Show `decision.md` under the findings: the decision, its reasons and its open
items, first and plainly when it is `ESCALATE`. Then every decision in `decisions.md` still
unticked: each is an assumption the build rests on that the person hasn't confirmed, and the
approval below confirms it or sends the change back. A line marked `→ superseded by D<m>` is no
assumption the build rests on: show it as one line beside D<m>, the default that replaced it
(`D2, superseded by D4: …`), never as its own open item. Then each reviewer's verdict from the highest
round. A `CHANGES` your own passes confirm is a finding like any other; one they don't is said so,
with why. Then the agents' findings in `findings.md` (each section whose `By:` names a factory
role), under the verdicts and counted apart from ship's own: `findings`' `agents` count, never in
its `counts` or the trailer's keys. The decision informs the person's approval and never stands in
for it.

**The agents' nits.** An agent's section that is `recorded` and holds `Theme:`, `Cost:` and
`Value:` lines is a nit its reviewer weighed, which a factory landing would file. Propose each as
the `[nit]` entry they give, shown as **Nits** shows one: the section's title, its line, `Theme:`,
`Cost:` and `Value:` as written, `Paths:` the path its `Evidence:` names (without the line), and
`Raised by: <NNN-slug> (<pass>)` with its heading's pass. Its id comes in the same `next-entry`
call as every other entry, and the question is asked with `--nits`. The section itself stays as
written: filing it re-dispositions nothing.
