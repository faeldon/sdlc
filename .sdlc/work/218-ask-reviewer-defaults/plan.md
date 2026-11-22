# 218 — Plan

> Tier 1, but the Approach touches the script, a skill, an agent and the tests, so a plan: what
> to change, in what order, and what proves it.

## Files to change

- `plugins/factory/scripts/factory.py`: `cmd_ask()`'s `next`. Reuse `read_ledger()` (each line's
  `source`, `kind`, `answer`) and `KEPT_ANSWER`. New: `BUILT_RE` (`- BUILT: D<n>` in a builder
  report) and `unbuilt_defaults(folder, ledger, ids)`, the answered defaults kept by the person
  whose source isn't a builder and that no builder report of a later round names as built.
- `plugins/factory/agents/builder.md`: the builder writes `- BUILT: D<n>: <what>` in its report
  for a reviewer's or the approver's default it built, so the script can read it.
- `plugins/factory/skills/decide/SKILL.md`: `rebuild` also says a kept default the build never
  made, named in `unbuilt`.
- `plugins/factory/README.md`: the decide line names that reason too, and autopilot's
  *What it holds* the new hold (round 2).
- `plugins/factory/scripts/autopilot.py`: `hold_causes()` holds a change with an open reviewer's
  or approver's default no later build made, through `factory.unbuilt_defaults()` (round 2, D2).
- `plugins/factory/skills/autopilot/SKILL.md`: its hold paragraph names that cause (round 2).
- `tests/test_factory_decisions.py`: the tests below.

## Work order

1. A reviewer's default confirmed, no later builder report → `rebuild`, `unbuilt` naming it; a
   builder's own default confirmed → `ship` (already, kept by a test).
2. A later builder report's `- BUILT: D<n>` → `ship`; the same line in the raising round's own
   report, or a report of an earlier round, isn't enough.
3. The builder's instruction, the skill's and README's wording.
4. Round 2, D2 decided "autopilot holds such a change": `unbuilt_defaults(folder, lines)` takes the
   ledger lines to weigh (`cmd_ask()` the kept ones, as before), and autopilot's `hold_causes()`
   passes the open ones `finish()` would answer, holding the change while any is unbuilt. The
   factory README's and the autopilot skill's hold lists name the cause.

## Tests

- `test_ask_says_rebuild_for_a_reviewer_s_default_never_built` — Outcome 1 and 3 (216's case),
  `then` for ESCALATE and READY.
- `test_ask_says_ship_once_a_later_builder_report_built_it` — Outcome 1 (the `BUILT` line, and a
  round no later than the raise doesn't count).
- `test_ask_says_ship_when_every_default_is_kept` (existing) — Outcome 2: a builder's default kept.
- `test_held_change_and_its_dependents_never_land[unbuilt]` — D2: autopilot holds a change whose
  reviewer's default is open and unbuilt, and its dependent never builds.
- `test_a_reviewer_s_default_a_later_build_made_lands` — D2: the same default with a later
  `- BUILT: D1` is answered as autopilot and lands, so the hold doesn't overreach.
- A skill-text test that the builder names `- BUILT: D<n>` and decide's `rebuild` names `unbuilt`.

## Rollback

Nothing outside git: `ask` writes nothing. `git revert` undoes it.
