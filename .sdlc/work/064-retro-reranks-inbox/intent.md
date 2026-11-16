---
id: 064
slug: retro-reranks-inbox
tier: 2
impact: minor
stage: shipped
created: 2026-11-16
updated: 2026-11-16
shipped: 2026-11-16
idea: 2026-11-08-3
depends_on:
serves: [O4]
---

# 064 — Retro re-ranks the inbox

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A retrospective sets the direction (milestones, what's carried, what's put off), but never touches
the register's order. `/sdlc:retro` proposes new seeds and settles milestones; it never proposes a
`Priority:` line, and its skill text never mentions one. So after each retro, status's Next up
still ranks the backlog by age and by whatever `Priority:` lines someone added by hand between
cycles.

Since 062 that order matters more: a `Priority: high` puts a seed under **Ready to build**, a
plain seed sits under **Needs a decision**. Today 23 seeds need a decision, 16 of them
`Priority: low` set by hand weeks ago, and five milestones (M4–M8) ran out of seeds with nothing
ranking what comes next. In this session the person asked "what do I still have in my inbox",
read all 28 entries, and retired one (2026-10-25-9) only after asking whether it still mattered:
judgments the retrospective is meant to make once per cycle, from evidence.

Raised 2026-11-08, after 2026-11-08-1, which shipped as 062.

## Outcome

- After its passes, `/sdlc:retro` proposes a table of the register's open ideas and bugs:
  `Priority: high` for what the new direction and milestones make urgent, or what a pass found
  biting now (stops measured past target, a rule a seed says is broken, landed work piling up
  unpushed); `Priority: low` for what the direction puts off; removing a `Priority:` that no
  longer holds; and a `Theme:` for any entry still without one, as `/sdlc:idea --themes` does.
- The table sits behind retro's one approval; the edits are written to the register and committed
  in the `Retrospective` commit, which already holds `.sdlc/work/inbox.md`. No second commit or
  stop.
- Nits keep their own rank: never a `Priority:` (their `Cost:` and `Value:` rank them), as `check`
  already enforces.
- **Moves O4:** after each retrospective, Next up's **Ready to build** holds what the new direction
  made urgent, so the next change starts from the retro's decision instead of a hand re-rank.

## Affected

- **Area:** the retrospective loop and the backlog it ranks.
- **Files & components:** `skills/retro/SKILL.md` (the proposal, its table in the WAIT, its
  write); possibly `scripts/sdlc.py` (a read-only listing of open entries with their current
  `Priority:` and `Theme:` for retro to propose against, if `retro`'s output doesn't carry enough;
  `cmd_retro_commit`'s checks, if the register's edits need guarding); `tests/test_skills.py`,
  `tests/test_retro.py`; `docs/REFERENCE.md`, `AGENTS.md`.
- **Downstream:** every host's retrospective, and every status after one (Next up's order and
  groups follow the new lines); `/sdlc:idea --themes`, whose job the theme part overlaps.
- **Contracts:** retro's one WAIT and what it approves; `retro-commit` writes only the direction
  doc, the register and the product doc, and refuses a doc that drops an open id; `Priority:`
  words from `PRIORITIES`; a nit never takes a `Priority:`; an entry being built (`[building]` or
  named on an open change's `idea:`) is never touched.

## Constraints

- Every proposed line is the person's to approve, change or drop: retro proposes, nothing ranks
  itself.
- No entry is retired or rewritten by this: only its `Priority:` and `Theme:` lines change, so its
  id, title and prose stay as filed.
- An entry being built, and every nit, are left alone.
- Still one stop: the table joins retro's existing question, never a question of its own.

## Open questions

- ~~Should the retro also propose retiring seeds it judges no longer wanted (as the person did with
  2026-10-25-9), or only re-rank and leave retirement to `/sdlc:idea`?~~ Resolved: re-rank only;
  retire candidates are named with `/sdlc:idea <id>`, and `retro-commit` refuses a removed entry
  (the person's choice).
- ~~Does retro's output need a listing of open entries with their current `Priority:` and
  `Theme:`, or does it read the register itself?~~ Resolved: `retro` prints `entries`.
- ~~How large can the table get before the one approval stops being a real review: capped, or
  only the lines that change?~~ Resolved: only the lines that change.
- ~~Does a proposed `Theme:` reuse `/sdlc:idea --themes`' rules, or call it?~~ Resolved: the retro
  skill states the rule (reuse a theme in use when one fits), no second approval.
- ~~Should a `high` the retro sets carry a reason, so the next retro can tell its own call from the
  person's?~~ Resolved: no stored reason; the table shows one at approval.
