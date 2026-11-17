---
id: 092
slug: retro-outcome-coverage
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 092 — Retro checks its goals and the work against the outcomes · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `doc_items()` gives every item `serves: []`; a goal's from a trailing
  `(O1, O3)` (`CITES_RE`), a milestone's from its first `Serves:` line (`SERVES_RE`, read like
  `GROUPS_RE`, with `current` reset at a heading). Nothing reaches `problems`. *Built beyond the
  spec's R1:* an open goal wrapped onto indented lines (as this repo's G6–G8 are) is cited at the
  end of its last line (`_goal_cites()` over the joined text); its `title` stays the first line's.
  A struck goal's wrapped lines are its reason's and are never read. Without this, the spec's own
  Verification (G6–G8 not uncited) fails.
- `scripts/retro.py`: `NONE_THEME_RECURS = 3` beside `RATE_MIN_CHANGES`; `_uncited(direction,
  product)` and `_none_themes(home, changes, bases)`; `_product()` gains `direction` and `bases`
  and returns `uncited` and `none_themes` beside its old keys; `retro()` passes both. Reuses
  `sdlc._git`, `sdlc.work_rel`, `sdlc.INBOX`, `sdlc.parse_entries`, `sdlc.ideas_of`,
  `sdlc.ref_matches`, `sdlc.entry_theme`, `sdlc.NO_THEME`, and the `bases` `retro()` already
  builds from `_change_base()`.
- `templates/direction.md`: the fenced example's G1 ends `(O1)`, M1 gets `Serves: G1`; a sentence
  in the note; the Goals and Milestones prompts ask for citations.
- `skills/retro/SKILL.md`: Step 0's `direction` and `product` bullets; pass 4 (uncited items,
  recurring themes → proposed `O<n>`), pass 5 (every goal cites, every milestone has `Serves:`).
- `docs/REFERENCE.md`: the goals-and-milestones paragraph states both forms, reported never refused.
- `tests/test_retro.py`: R1–R3, R5–R8 tests; `tests/test_next_up.py`: R4's; `tests/test_skills.py`:
  R9's.

## Work order

1. **Goal citations** (R1, R3 part): test, then `CITES_RE` in `doc_items()`.
2. **Milestone `Serves:`** (R2, R3, R4): tests, then `SERVES_RE`; the next_up equivalence test.
3. **`product.uncited`** (R5, R3's retro-commit test): fixture repo test, then `_uncited()` and the
   `_product()`/`retro()` wiring.
4. **`product.none_themes`** (R6, R7): fixture with seeds deleted in the ship commit and
   `Sdlc-Base` on the `Close`, then `_none_themes()`.
5. **Template** (R8): extend the example test, then edit the template.
6. **Skill and reference** (R9, R10): the skill test, then the prose. Gate.

## Tests

- R1 `test_a_goal_cites_the_outcomes_at_the_end_of_its_line`
- R2 `test_a_milestone_cites_on_its_serves_line`
- R3 `test_citations_never_add_a_problem`, `test_retro_commit_takes_an_uncited_goal`
- R4 existing `test_the_templates_example_parses_to_its_ids`, `tests/test_next_up.py` unchanged;
  `test_next_up_is_the_same_with_and_without_serves_lines`
- R5 `test_retro_names_goals_and_milestones_that_reach_no_open_outcome`
- R6 `test_none_changes_are_grouped_by_their_seeds_themes`
- R7 `test_a_theme_recurs_at_three_none_changes`
- R8 `test_the_templates_example_parses_to_its_ids` extended; `tests/test_defaults.py` shape tests
- R9 `test_the_retro_skill_names_the_coverage_fields`; existing skill invariants
- R10 `./check.sh`

## Rollback

`git revert` undoes all of it: nothing is written outside the repo, `retro` stays read-only, and
the new JSON keys are additive. A host whose direction doc already gained `Serves:` lines or `(O1)`
citations keeps them as plain text: the reader before this change ignores both.
