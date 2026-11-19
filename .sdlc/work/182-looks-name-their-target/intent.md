---
id: 182
slug: looks-name-their-target
tier: 1
impact: patch
stage: shipped
created: 2026-11-19
opened: 2026-11-19T10:26Z
updated: 2026-11-19
shipped: 2026-11-19
idea:
depends_on:
serves: [O3, O6]
---

# 182 — A look says what to look at, and is raised only for what the person hasn't approved

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

An approver's look reaches the person in `/sdlc-factory:decide` as "Have you looked?", answered
`seen` or `checked something`. That doesn't say what looking involves (read the code, run
something, or just acknowledge), or what `seen` commits the person to. Seen while deciding 177:
both its looks were things the person had already approved in the spec (R7's relaxed "report runs
no host command" rule, and the published row shape and impact), so each cost a stop the
retrospective counts for nothing new. The cause is in `plugins/factory/agents/approver.md`: it
escalates "anything that touches a destructive operation, a secret or a published interface", and
files each reason as `- ESCALATED: look: <why>`, whether or not the approved spec's *Contracts
touched* already named it and the person said yes to it.

## Outcome

- The decide skill's look question names what the approver wants seen (the file, function or
  contract, from the look's own line), and says that `seen` means acknowledged and accepted, with
  `checked something` for what the person actually verified.
- The approver raises a look only for what the approved spec (or a Tier 1's Approach), the
  person's answers and the rounds don't already cover; what they do cover it names in its
  decision under *For the person at ship*, with no ledger line and no ESCALATE on that ground
  alone.
- A test pins both: the decide skill's look wording and the approver prompt's rule.
- **Moves O3:** a change whose only escalation was already approved in its spec lands without a
  stop.
- **Moves O6:** each remaining look tells the person what to check, so acknowledging one means
  something.

## Affected

- **Area:** the factory's approver and decide skill.
- **Files & components:** `plugins/factory/agents/approver.md` (when to ESCALATE, the
  `- ESCALATED: look:` form), `plugins/factory/prompts/approve.md` if it words the rule,
  `plugins/factory/skills/decide/SKILL.md` (Step 1's look item), `plugins/factory/README.md`, and
  their tests in `tests/test_skills.py` and `tests/test_prompts.py`.
- **Downstream:** every factory run's decision; the autonomy figures, where looks count as stops;
  `/sdlc:ship` and land, which show the decision.
- **Contracts:** the `- ESCALATED: <kind>: <why>` line stays as `REASON_RE` reads it, and `look`
  and `gate` stay the only kinds; the decide skill's WAIT and its answers (`seen` / `checked
  something`) are unchanged.

## Constraints

- When in doubt the approver still escalates; only a reason the approved spec or the person's
  answers already cover moves out of the ledger.
- A Critical or High finding still open, a disagreement, a departure from the spec, a requirement
  with no test, a destructive operation and a secret stay looks whatever the spec says.
- No change to how `factory.py` parses decisions or ledgers.

## Open questions

- How does the approver tell "covered by the spec": the reason appearing in the spec's *Contracts
  touched*, or the person's own words in `decisions.md`?
- Should a look carry its target in a fixed form the decide skill can quote, or is the reason's
  text enough?

## Approach

Change the approver's ESCALATE rule and its `- ESCALATED: look:` guidance: a published interface
the approved spec's *Contracts touched* names, and the person approved, is named under *For the
person at ship* rather than filed as a look; each look's reason starts with what to look at.
Reword the decide skill's look item so its dialog names that target and says what `seen` and
`checked something` record. Pin both wordings with tests.
