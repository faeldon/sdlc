# 058 — Setup stops on a set-up repo before reading its first-setup steps · notes

## Sizes

- `skills/setup/SKILL.md`: 314 lines before, 125 after (R7's budget is 150).
- `skills/setup/drafts.md`: 212 lines: the drift explanation, the arguments, Steps 1–3.

## Departures from the spec

- **`archive.target = "none"` counts as an answer for `complete`** (R1 named only
  `commands.build` and `commands.scan`). `readiness` warns `archive: none: archive.target is none`
  on every repo tracked locally, an answer setup itself writes, so as specified no local repo could
  ever be complete. Found when the set-up fixture (local, as the eval sandbox has no `gh`) failed
  `test_the_set_up_fixture_is_complete`. The `archive` item keeps its warning; only `complete`
  reads past it, and only for `none`, never for a tracker that can't run.
- **The unknown-key case** in `test_anything_left_to_draft_is_not_complete` trips `config: warn`
  as well as `report`; a `report` alone is covered by the monkeypatched
  `test_anything_drift_finds_is_not_complete`.
- **The set-up fixture has no `CLAUDE.md`** (R9 listed a one-line one): `AGENTS.md` alone serves
  `docs.policy` and `context`, which keeps any `CLAUDE.md` out of the plugin's tree.
- **No `## Steps 1 to 3` pointer heading** in `SKILL.md`: the tests' `_steps` split reads any
  `## Step…` heading as a step. Step 0's paragraph is the pointer.
- **Config keys and the guide keys** are read across a skill's side files
  (`test_skills_read_host_specifics_from_config`, `test_readers_of_the_process_read_the_guide_with_it`),
  as 056 made the rule tests do.
