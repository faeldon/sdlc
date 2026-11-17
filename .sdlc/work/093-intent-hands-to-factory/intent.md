---
id: 093
slug: intent-hands-to-factory
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
serves: [O6, O3]
---

# 093 — Intent offers the factory as a way to build the change, with no plan mode

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`/sdlc:intent`'s question for a Tier 1 change ends by starting plan mode: `…off main, then start
plan mode? (yes / yes, without plan mode / change the tier / edit a section)`. Its first option, the
recommended one, leads straight into planning the change in this session: the manual path. The
factory path is different: the person files the intent, and `/sdlc-factory:build NNN` hands the plan
and the build to the builder, which writes `plan.md` itself.

On 2026-11-17 several changes were opened to be built by the factory (086, 087, 089). Each time the
person had to pick the second option or decline plan mode, and one, 087, was planned and built by
hand in the session when the factory was meant to take it; at `stage: test` it could no longer be
handed to the factory at all (`factory.py start` starts a Tier 1 only at `plan`). The question
doesn't say which path the change is taking, and nothing records it. The session also moves into
the new worktree either way, though a factory supervisor belongs in the main checkout, so after
each intent the person or the session had to move back. A Tier 2 has the same gap: the intent says
`/sdlc:spec` comes next, though the factory's spec-writer drafts the spec under
`/sdlc-factory:build`.

## Outcome

- **Moves O6:** a change meant for the factory is filed and handed over in one step, with no
  plan-mode stop and no session sitting in its worktree, so the person stops only at the intent's
  yes and the factory's own gate.
- **Moves O3:** a Tier 1 meant for the factory no longer offers, or starts, plan mode, a stop O3
  counts.
- `/sdlc:intent`'s question offers both paths as its yes answers:
  - **`yes, by hand`** (the manual process): as today; a Tier 1 starts plan mode, a Tier 2 goes to
    `/sdlc:spec`, and the session moves into the worktree;
  - **`yes, for the factory`**: the intent is created and synced as today, but no plan mode starts,
    the session stays in the main checkout, and the next step reads `/sdlc-factory:build NNN`,
    whose builder plans a Tier 1 and whose spec-writer drafts a Tier 2's spec;
  - plus `change the tier` and `edit a section`, as today: still 2 to 4 answers, as
    `test_every_wait_asks_in_a_dialog` requires.
- The factory option appears only where the factory is installed for the repo; elsewhere the
  question reads as today, so a host without `sdlc-factory` sees no option it can't use.
- `tests/test_skills.py` pins both yes answers and what each leads to, and the skills' cases
  (`evals/`) for `intent` still pass, run for this change's scope.
- Takes in nit 2026-11-17-6: an `intent` case runs on a fixture with a `.sdlc/PRODUCT.md`, so a
  paid run shows intent proposing `serves:` without asking and naming the outcomes at its gate,
  not only the skill's wording pinned. `/sdlc:ship` retires the nit once the diff does it.
- `./check.sh` passes.

## Affected

- **Area:** `/sdlc:intent`'s WAIT and what follows it.
- **Files & components:** `skills/intent/SKILL.md` (Step 4's question, Step 5's `EnterWorktree`,
  Step 6's next action); `evals/intent/` and `evals/fixtures/` (nit 2026-11-17-6); perhaps `scripts/sdlc.py` if `config` or `readiness` reports whether the
  factory is installed; `tests/test_skills.py`; the `intent` case in `evals/`; and
  `docs/REFERENCE.md` or the README's account of a first change.
- **Downstream:** every person opening a change, here and in hosts; `/sdlc-factory:build`, which
  starts a Tier 1 only at `plan`, so a change filed for it must stay there; metrics, which read a
  dialog's answer in a gated span as the gate, so the new answer must still read as a yes; O3's stop
  count, since plan mode is a counted stop.
- **Contracts:** *Skills* (exactly one WAIT, asked in an `AskUserQuestion` dialog with 2 to 4
  answers, only a chosen yes approves: `test_every_wait_asks_in_a_dialog`); the always-Tier-2 rule
  for a WAIT's change; *the factory, optional by being installed or not, `sdlc` loading nothing from
  `plugins/`* (the core may know whether the factory is there, never need it);
  `test_spec_and_a_tier_one_intent_start_plan_mode_after_their_wait`, which changes with the
  question.

## Constraints

- A host without the factory sees the intent's question exactly as today; the core never assumes
  the factory.
- Only a chosen yes approves, and the factory answer approves exactly what the manual one does (the
  change, its worktree, its issue), nothing more: it starts no factory run, and
  `/sdlc-factory:build` keeps its own WAIT.
- The manual path is unchanged: plan mode for a Tier 1, `/sdlc:spec` for a Tier 2.

## Open questions

- ~~How does `/sdlc:intent` know the factory is installed: `.claude/settings.json`'s `enabledPlugins`
  (as 079 set it, which misses a user-scope install), the presence of `.sdlc/factory.toml`, or a
  `config` field read from `claude plugin list` (slow, outside git)?~~ Resolved: `config` reads
  `enabledPlugins` from the main checkout's `.claude/settings.local.json`, then
  `.claude/settings.json`, then `~/.claude/settings.json`, the most specific naming
  `sdlc-factory@*` deciding (spec R1–R3).
- ~~Is the answer recorded on the change, say `mode: factory` in the frontmatter, so status and the
  board show "waiting for the factory" before the run starts, or is the report's next step enough?~~
  Resolved: not recorded; the report's next step, then the run's `runs/` files and `Sdlc-Mode`.
- ~~Which yes comes first, and so is recommended: a per-repo default (in `.sdlc/factory.toml`, say), or
  always the manual one? The person's account has the manual one first.~~ Resolved: always
  `yes, by hand` first (R5).
- ~~Does `yes, without plan mode` go, now that `yes, for the factory` covers its main use? Keeping it
  makes five answers, past the dialog's four.~~ Resolved: dropped only in the form shown when the
  factory is enabled; without it the question is unchanged (R4, R5).
