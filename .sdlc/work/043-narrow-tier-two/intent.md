---
id: 043
slug: narrow-tier-two
tier: 1
impact: none
stage: shipped
created: 2026-11-07
updated: 2026-11-07
shipped: 2026-11-07
idea: 2026-11-04-9
depends_on:
serves: [O3, O4]
---

# 043 — Narrow this repo's always-Tier-2 carve-outs to what can lose work

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Every change since 2026-10-26 whose intent could be read was Tier 2: 11 of 11 in the last window,
and 041 and 042 since. `.sdlc/SDLC.md` puts two kinds of change in Tier 2 whatever the size of their
diff, anything that changes what `sdlc.py` reads or writes in a host and any skill's WAIT step or
`allowed-tools`, and nearly every change here touches one of them.

But the two rules catch very different risks. "What `sdlc.py` reads or writes in a host" covers how
a number is handed out or a folder removed, where one line loses someone's work, and also a new
read-only field in `retro`'s JSON or a new trailer line beside the old ones. "A skill's
`allowed-tools`" covers a rule that lets a write run unasked, and also a rule added for a read-only
command the skill already runs, which `tests/test_skills.py` pins exactly. The small, additive kind
pays the full Tier 2 cost (a spec, a plan, two more gates) for a risk the tests already hold.

## Outcome

- `.sdlc/SDLC.md`'s *Always Tier 2* keeps Tier 2 for what can lose work, number twice, or let
  something run unasked: how numbers are allocated; how a change's folder is committed, archived or
  removed, and the `.sdlc/work/` layout; a change to what an existing config key, frontmatter key,
  file or trailer means; a skill's WAIT step; an `allowed-tools` rule that lets a command that
  writes run without asking.
- An additive change goes by its size: a new config or frontmatter key whose default keeps today's
  behaviour, a new read-only output, a new trailer line beside the old ones, an `allowed-tools`
  rule for a read-only command already in the skill's bash blocks.
- `./check.sh` passes; `tests/test_defaults.py` keeps the doc to this repo's answers under the
  guide's headings.
- **Moves O3:** among the next window's changes, those whose diffs are small come in at Tier 1,
  three gates instead of five, so their median stops fall.
- **Moves O4:** the next retrospective can check each change's tier against these rules, and
  revise them from the evidence.

## Affected

- **Area:** this repo's process answers.
- **Files & components:** `.sdlc/SDLC.md` (*Tiers: the overhead control → Always Tier 2*).
- **Downstream:** every later change here, at `/sdlc:intent`'s tier step, and ship's review, which
  reads the process doc. No host: hosts read the guide and their own answers.
- **Contracts:** "This repo's process docs hold only its answers": every block under a guide
  heading, none restating the guide.

## Constraints

- Only this repo's answers change; an improvement any repo could use goes into `guide/process.md`,
  a host-facing change of its own.
- The rules stay checkable at intent time: someone reading a seed can tell which side of the line
  it falls on without the diff.

## Open questions

- ~~Whether a removal from what `sdlc.py` writes (042 dropped `permission=`) counts as "changing what
  something means": it is, and stays Tier 2, but the wording has to say so.~~ Resolved: the second
  bullet says it, "its meaning changed or its writing stopped", with 042 as the example.
- ~~Whether the distinction (additive versus meaning-changing) is general enough that the guide's own
  *Always Tier 2* should say it for every host.~~ Resolved: not here. The guide is host-facing, so
  saying it for every host is a change of its own, worth making once a retrospective shows the line
  holds in this repo.

## Approach

Rewrite the two bullets under `### Always Tier 2, whatever the size of the diff` in `.sdlc/SDLC.md`
into the list above, each with its reason in a clause (what goes wrong in a host if it's wrong),
and add a short line saying the additive changes go by their size, with the examples. Run
`./check.sh`. One file, no code: no `plan.md`.
