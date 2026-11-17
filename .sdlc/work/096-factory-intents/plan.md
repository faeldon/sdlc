---
id: 096
slug: factory-intents
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 096 — Intent opens several changes from one run · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `cmd_groups()` beside `cmd_nits()`, its `groups` subparser and dispatch,
  `"groups"` in `READ_ONLY`.
- `skills/intent/batch.md` (new): the batch's steps, read only when the argument holds `;`.
- `skills/intent/SKILL.md`: description, `argument-hint`, the `groups` rule, a pointer to
  `batch.md` in Steps 0–3, 5 and 6, and the batch question in Step 4.
- `tests/test_groups.py` (new): `groups`' parse, refusals, order, `depends_on` and rerun.
- `docs/REFERENCE.md`, `README.md`, `plugins/factory/README.md`: the batch syntax and its report.
- `.sdlc/work/096-factory-intents/notes.md` (new): the R4 deviation below.

## Work order

1. `cmd_groups()`: tokenize each group (ids by `ENTRY_ID_RE`; `as`, `tier`, `after` pairs; any
   other word a refusal), slugs through `slugify()`; join ids with `inbox_entries(main_root())`
   (kind, `seed` read as `idea`; title; `entry_issues()`); claimed ids from `_open_claims()` and
   `[building]` tags, allowed when the claimant is the group's own `created` change; `created` from
   `_used()`; refusals of R4; a stable Kahn sort for `order`, an unplaced group a cycle;
   `depends_on` from the `after` group's `created`. JSON `groups`, `order`, `refusals`; exit 1 with
   refusals. Tested by `tests/test_groups.py` before the skill uses it.
2. `batch.md` and `SKILL.md`; `./check.sh`'s skill tests cover the side file, the rule and the
   question.
3. The docs.

**Deviation from R4**, in `notes.md`: no refusal for a slug a closed change used. `new` doesn't
refuse one (`_used()` reads only open folders), so `groups` refuses exactly what `new` would.

## Tests

- R2–R6, R11: `tests/test_groups.py`: parse; each refusal; `order` for a chain, a fan-out and a
  tie; `depends_on` null, then the number once the `after` group's folder exists; a rerun where a
  group's slug is an open change claiming its ids reads `created`, with no refusal; exit codes;
  `groups` in `READ_ONLY`.
- R7, R9, R13: `tests/test_skills.py` as it stands (side file named and gate-free, every rule used
  and covering its command, the question's 2–4 answers, one WAIT).
- R1: the intent eval case's fixture still passes `check --strict` (`tests/test_evals.py`), and
  the single run's questions are unchanged word for word.
- R8, R10, R12: manual, after landing: this batch's own command (096's intent, Outcome) shows ten
  drafts and one question, creates them in order with wave 2's `depends_on:` set, and a rerun
  creates nothing twice.
- Live, read-only: `sdlc.py groups "2026-11-17-31 2026-11-17-32 as landing-fixes tier 1"
  "2026-11-17-35 as landing-does tier 2 after landing-fixes"` prints `order` landing-fixes first
  and `depends_on` null.

## Rollback

`git revert <sha>` covers it all: `groups` only reads, and the skill's batch writes only what a
single run writes. Changes a batch already opened stay open, each its own worktree and issue,
dropped one by one with `/sdlc:drop` if unwanted.
