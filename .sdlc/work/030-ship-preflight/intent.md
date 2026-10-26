---
id: 030
slug: ship-preflight
tier: 2
impact:
stage: test
created: 2026-10-27
updated: 2026-10-27
idea: 2026-10-26-9
depends_on:
serves: [O3]
---

# 030 — One preflight call for ship's lookups

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Ship is the largest skill (`skills/ship/SKILL.md`, 412 lines, about 6,000 tokens, 21 commands)
and 7 of the last 20 changes edited it. Its Step 0 runs `status`, `config`, `base`, `undone`,
`nits --change`, `closes` and `checks` one by one on the same change, each with prose on how to
read its result. Step 5 builds its WAIT question in prose by leaving out clauses a rule decides:
the context update when none was proposed, the nits when none are added or retired, the closing
and splitting clauses when `closes:` names nothing or every issue was resolved, the issue update
when `archive.target` is `none`. Those rules are tested only by a model reading them right every
time. Every new list ship has gained so far has added a command, an `allowed-tools` rule and a
paragraph to the skill, which is why it keeps growing and keeps being edited. Raised by the
retrospective of 2026-10-26.

## Outcome

- One `sdlc.py ship --check <NNN>` call returns, as one JSON document, what ship's Step 0 now
  gathers in separate calls: the change's folder and tier, its undone items, the nits its diff
  touches, the issues it would close, and its acceptance checks.
- The WAIT question's clauses are decided by the script, not the skill's prose: the question is
  returned or rendered from what the call returns, and a test pins each clause rule.
- `skills/ship/SKILL.md` is measurably shorter, with fewer commands and fewer `allowed-tools`
  rules, and a new list ship needs later goes into `ship --check`, not a new step.
- **Moves O3:** ship runs fewer separate commands before its WAIT, so a host whose permissions
  don't already allow each one is prompted fewer times per ship.

## Affected

- **Area:** the ship skill and the `ship` subcommand of `scripts/sdlc.py`.
- **Files & components:** `skills/ship/SKILL.md` (Step 0, Step 5, `allowed-tools`);
  `scripts/sdlc.py` (`cmd_ship` or a sibling, and the readers it bundles: `undone`, `nits`,
  `closes`, `checks`); `tests/test_sdlc.py`, `tests/test_skills.py`; likely
  `ALLOW_RULES`/`READ_ONLY` and `docs/REFERENCE.md` if the subcommand is host-facing.
- **Downstream:** every host shipping with the plugin. Ship is the gate every change passes, and
  its WAIT question is the person's one approval of the commit. The factory's build session
  leaves the change folder ship then reviews.
- **Contracts:** narrow `allowed-tools` (each rule matches a command run exactly); exactly one
  `WAIT` heading; `accept` never gets an allow rule and stays asked in prose; `base` is the one
  write before the WAIT; only publish pushes.

## Constraints

- `base` stays a write ship makes, and it stays first. A preflight that only reads can't also
  fast-forward or rebase, so `base` either stays its own call before `--check`, or `--check` only
  reports whether the branch is behind.
- `accept` is never folded in: it runs host commands and must stay one the harness asks about.
- The WAIT stays the person's approval. The script may draft the question; the skill still asks
  it, and nothing is committed before the answer.
- The existing subcommands (`undone`, `nits`, `closes`, `checks`) stay for the other skills and
  people who call them; `--check` composes them, it doesn't replace them.

## Open questions

- ~~Does `--check` run `base` first, report on it, or leave it as its own call? The order "bring
  up to date, then review" must hold either way.~~ Resolved: `base` stays its own call, first;
  `preflight` only reads, after it.
- ~~A flag on `ship` (`ship --check`), which today writes, or its own read-only subcommand
  (`preflight`) that `READ_ONLY` can cover?~~ Resolved: its own `preflight` subcommand, since an
  allow rule for `ship *` would also cover the stamping `ship <NNN>`.
- ~~Can the script render the WAIT question, when some clauses depend on what only Step 4
  knows?~~ Resolved: a second call after Step 4, `preflight <NNN> --question` with flags for
  those facts, renders it word for word.
- ~~Do `status` and `config` belong in the bundle?~~ Resolved: no, every skill opens with them
  and `config` is read throughout ship.
- ~~Is there a measure to compare before and after?~~ Resolved: close already writes
  `Sdlc-Stage: ship … permission=N` on each `Close` commit.
