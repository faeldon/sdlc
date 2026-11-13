# Ship — agents' verdicts

`preflight`'s `branches` names this file when the change's folder has a `decision.md`: it was built
by agents (the optional `sdlc-factory` plugin).

## Step 0

A change built by agents has `.sdlc/work/NNN-slug/decision.md`, opening `DECISION: READY` or
`DECISION: ESCALATE`, and its reviews in `.sdlc/work/NNN-slug/reviews/round-<N>/<role>.md`, each
opening `VERDICT: PASS` or `VERDICT: CHANGES`, each round's verifier answers in
`reviews/round-<N>/verified.md` (`- KEPT:` for the builder, `- DROPPED:` with why), and the person's
calls the agents raised in `.sdlc/work/NNN-slug/decisions.md` (`- [x]` decided, `- [ ]` assumed).
Read the decision, the highest round's reviews, every `verified.md` and the ledger: they are
evidence for Step 3, never a substitute for it. A dropped change your own passes confirm is a
finding like any other. The builder's reports in `build/round-<N>.md` and the behaviour check's
`reviews/round-<N>/behaviour.md` end with a `## Evidence` section, each command with its output and
exit: what the agents say they ran, which Step 1's gate and acceptance checks still run for
themselves.

## Step 4

**Agent verdicts.** Show `decision.md` under the findings: the decision, its reasons and its open
items, first and plainly when it is `ESCALATE`. Then every decision in `decisions.md` still
unticked: each is an assumption the build rests on that the person hasn't confirmed, and the
approval below confirms it or sends the change back. Then each reviewer's verdict from the highest
round. A `CHANGES` your own passes confirm is a finding like any other; one they don't is said so,
with why. The decision informs the person's approval and never stands in for it.
