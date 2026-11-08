---
id: 044
slug: status-ranks-the-backlog
tier: 2
impact: minor
stage: shipped
created: 2026-11-08
updated: 2026-11-08
shipped: 2026-11-08
idea:
depends_on:
serves: [O3]
---

# 044 — Status ranks and groups the backlog, so choosing the next change takes one read

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`/sdlc:status` doesn't help pick what to work on now, which is the question it exists to answer.

- **It recommends work already in hand.** The skill's precedence (`skills/status/SKILL.md`, Step
  3) puts any open change at `stage: build` or later first ("finish what's started"). With several
  sessions running, that change almost always has a session on it already, so the top
  recommendation tells the person nothing new.
- **The order is fixed, and urgency has nowhere to go.** `next_up()` orders by `NEXT_RULES`: bugs,
  each open milestone's first seed, series, cost-`S` nits by theme, then every other idea oldest
  first. Milestone seeds do matter, but an idea that became urgent because the person needs that
  feature now can't rise. A bug's `Severity:` is the only urgency an entry can carry.
- **Too little is shown to choose from.** `NEXT_SHOWN = 5` lines print, then "(+31 more)", and the
  skill recommends one and at most two runners-up. So the person asks for the inbox to be listed,
  gets 57 entries in date order, and still can't tell which comes first.
- **Nothing says which entries go together.** The person often wants to take on a group of related
  entries as one session's work. Nits carry `Theme:`; ideas don't, and status groups nothing but
  nits.

What works in practice, from a recent session in a host repo: asked "what else in the inbox can we
close today?", it read the register and answered in groups (nearly settled, paperwork or one
command; small fixes a session could ship today; needs you; still blocked), bunching entries by
theme within them ("doc wording", "tests", one area's nits shipped as one reviewed change). The
person picked from that answer at once. Status should give that read without the ad hoc question.

## Outcome

- `sdlc.py status` on a full register shows about ten ranked candidates, each with a short reason
  for its rank, grouped by theme so related entries can be taken as one change, with a count per
  group and the full list one command or flag away.
- Open changes a session is already working on no longer fill the recommendation; they stay visible
  as what's in flight.
- The person can say an idea is urgent, and status ranks it accordingly.
- Entries filed before themes existed get one from a single approved pass, which status points to
  when many lack one.
- **Moves O3:** the person gets from "what next?" to an `/sdlc:intent` in one status read, without
  a follow-up "list the inbox" and a hand sort of the reply.

## Affected

- **Area:** the status pipeline in `scripts/sdlc.py`, and the status skill's precedence.
- **Files & components:** `next_up()`, `NEXT_RULES`, `NEXT_SHOWN` and the `■ Next up` printer in
  `scripts/sdlc.py`; `skills/status/SKILL.md` Steps 1 and 3; if urgency or themes become entry
  lines, `BODY_KEYS`, `templates/inbox.md`, and the `/sdlc:idea` and `/sdlc:triage` skills that
  write entries; `tests/test_sdlc.py`, `tests/test_skills.py`; `docs/REFERENCE.md` where it
  describes Next up.
- **Downstream:** every host running `/sdlc:status`; `status --json`'s `next_up` object, if
  anything reads it; hosts' existing inbox entries, which must still read correctly with no new
  lines.
- **Contracts:** inbox entries are read as text (`Key: value` body lines); a new entry key must
  default to today's behaviour; status stays read-only. The always-Tier-2 rule on what something
  a host has means applies if `next_up`'s fields or an existing entry key change meaning.

## Constraints

- Status stays read-only, and the skill still never reads the register itself: the script ranks,
  the skill reports.
- An entry with no new lines ranks relative to the others as it does today; no host has to edit
  its register.
- Bugs by severity and milestone seeds stay near the top: this makes room for urgency, it doesn't
  demote the direction doc.
- Output stays compact enough to read in a terminal: grouped, not a 57-line dump.

## Open questions

- ~~How does an idea become urgent, and does urgency expire?~~ Resolved: an optional `Priority:
  high|med|low` line on ideas and bugs, set by `/sdlc:idea`, `/sdlc:bug` or by hand; `high` ranks
  first, `low` last, absent or `med` as today. No expiry: editing the entry changes it (spec R1, R2).
- ~~Where do ideas' themes come from, and can a theme mix kinds?~~ Resolved: the optional `Theme:`
  line nits already carry, now read on ideas and bugs and proposed by `/sdlc:idea` and `/sdlc:bug`
  from the register's themes; one theme groups nits, ideas and bugs (spec R3, R5, R9).
- ~~How does status know an open change is already being worked in a session?~~ Resolved: status
  shows each open change's last activity (branch's last commit, mtimes of its worktree's changed
  files), and the skill recommends an open change only once it's been quiet 24 hours (spec R7, R8).
- ~~Should groups be by readiness and effort, as the host session's were?~~ Resolved: deferred, at
  the person's call, to a seed of its own: it needs an effort signal ideas don't carry (maybe
  inferred from where an entry came from), and status mustn't grow long or slow.
- ~~What's the full-list escape hatch?~~ Resolved: `status --all` (spec R6).
- ~~Does `next_up`'s JSON shape change, or only gain fields?~~ Resolved: status prints no JSON, and
  only `print_status` and the tests read `next_up()`'s dict; it gains fields (spec Design).
