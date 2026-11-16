---
id: 062
slug: backlog-readiness-and-themes
tier: 2
impact: minor
stage: shipped
created: 2026-11-16
updated: 2026-11-16
shipped: 2026-11-16
idea: 2026-11-08-1
depends_on:
serves: none
---

# 062 — Readiness groups for the backlog, and taking a theme as one change

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Status ranks the backlog and groups it by theme (044), but two things were deferred, and this
session met both.

**No idea of what's ready.** `■ Next up` gives ten lines ranked by a fixed rule, and
`status --all` every candidate by theme: 27 today. Neither says which can simply be built, which
need the person to decide whether they're worth building, and which are waiting. Readiness needs an
effort signal ideas don't carry, and tagging every entry by hand is too much work; but where an
entry came from already says a lot. A `[nit]` was raised by a change's review and weighed with a
cost; a `[bug]` has a severity; a seed the person wrote is a proposal, and often an old one: 16 of
today's 26 ideas are `Priority: low`, almost all 21–23 days old. In this session the person had to
ask "what's still in my inbox" and read the whole list to judge it, and retired one seed
(2026-10-25-9) only after asking whether it still mattered.

**A theme can't be one change.** `idea:` names one seed: `intent_idea()` reads the line as a list
but keeps only its first item, and `sdlc.py ship` deletes only that entry. Nits can be taken by the
handful, since ship retires them by id (061 paid down seven), but ideas can't: a change built for a
theme's seeds leaves all but one in the register, which `status` puts forward again and someone
retires by hand.

## Outcome

- Status's `Next up` (or a view of its own) sorts candidates into readiness groups, inferred,
  never tagged: ready to build (nits and bugs a review or a person already weighed), needs a
  decision (seeds the person wrote, low-priority and old ones apart), and blocked (waiting on an
  `After:` or an open change). Status stays short; a test pins each group's rule.
- An intent's `idea:` can name several seeds by id (`idea: [2026-10-24-4, 2026-11-12-2]`);
  `/sdlc:intent` offers a theme's seeds together and tags each `[building]`; `sdlc.py ship`
  deletes every one; `status` leaves them all out while the change is open. An `idea:` with one
  value, or a title, reads exactly as today.

## Affected

- **Area:** the backlog: status's Next up, and the intent → ship path that consumes seeds.
- **Files & components:** `scripts/sdlc.py` (`next_up()`, `intent_idea()`, `ship`'s seed deletion,
  `_open_claims()`, status's printing, orphan-`[building]` checks); `skills/intent/SKILL.md`
  (offering a theme), `skills/status/SKILL.md` (reading the groups); `tests/test_next_up.py`,
  `tests/test_sdlc.py`, `tests/test_inbox.py`.
- **Downstream:** every host's `status` output and its `/sdlc:status` skill; every intent's
  `idea:` line, read by ship, status, `check` and retro's milestone verdicts. History's intents
  name seeds one at a time, and retro reads them for good.
- **Contracts:** frontmatter read as text, never YAML; `idea:` matched by `ref_matches()` /
  `same_ref()`, never by title alone; `stamp_shipped` edits lines in place; a nit is never put
  forward as a seed; `inbox-commit` never removes an entry an open change's `idea:` names
  (`_open_claims()`).

## Constraints

- An `idea:` with one value, an id or a quoted title, keeps today's meaning in every reader,
  history included.
- Readiness is inferred from what an entry already holds (its kind, `Priority:`, `After:`, its
  `Raised by:`): nothing new to tag by hand.
- Status stays short: the groups replace or reshape lines, never add pages.
- Retro's milestone verdicts still find the change that shipped each grouped seed.

## Open questions

- ~~Do readiness groups replace Next up's ranking, sit inside it, or live in `status --all`
  only?~~ Resolved: Next up splits in two, `Ready to build` then `Needs a decision`, sharing its
  ten-line cap (the person's choice).
- ~~What makes a seed "ready": is a person's own seed always "needs a decision", or does a recent
  `Priority:` or a milestone grouping count as decided?~~ Resolved: milestone and series seeds,
  `Priority: high`, bugs and nits are ready; plain and low seeds need a decision.
- ~~Is "blocked" its own group, or the existing "waiting on earlier seeds" count?~~ Resolved: the
  existing count.
- ~~Does `/sdlc:intent` offer a whole theme from status's theme line (as
  `/sdlc:intent pay down the [style] nits` already does for nits), or take several ids as
  arguments?~~ Resolved: several ids; `status --all` prints the command per theme.
- ~~Do retro's milestone verdicts and `check`'s orphan-`[building]` problem read a multi-seed
  `idea:` with no other change?~~ Resolved: no; they read `ideas`, R6.
