---
id: 179
slug: feature-inventory
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 179 — A map of what the plugin offers, and how much of it is used · plan

> Written after reading `scripts/metrics.py` (`summarize()`, `trailers()`, `parse_trailers()`),
> `scripts/retro.py` (`retro()`, `prose_metrics()`, `_coverage()`, `_previous_window()`,
> `_line_counts()`), `scripts/sdlc.py` (`COMMANDS`, `CONFIG_KEYS`, `RETIRED_KEYS`,
> `closed_changes()`, `retrospectives()`, `_release_tags()`, `_own_repo()`, `factory_enabled()`,
> `bash_commands()`), `plugins/factory/scripts/factory.py`'s `@command` registry and
> `scripts/board.html`'s `COLUMNS`.

## Files to change

- `scripts/metrics.py`: `summarize()` counts `skills` from `skill` events; `trailers()` writes
  `Sdlc-Skill: <name> runs=<n>`; `parse_trailers()` reads it back as `skills`; the docstring adds
  the line to the contract.
- `scripts/retro.py`: `RETIRE_AFTER = 3`, `SKILL_RUNS`, `COMMAND_RE`, and `surface()` with its
  helpers (`_inventory()`, `_callers()`, `_use()`, `_states()`, `_share()`, `_retire()`,
  `_footprint()`, `_growth()`); `retro()` returns it as `"surface"`.
- `docs/FEATURES.md` (new): the feature map, its sections and the Mermaid graph.
- `docs/PROCESS.md` (new): the change, release and retro loops as Mermaid flowcharts.
- `tests/test_metrics.py`: `test_close_names_each_skill_it_ran` (R1).
- `tests/test_surface.py` (new): R2–R10's tests, on scratch repos built as `test_retro.py` does.
- `tests/test_feature_map.py` (new, `portable`): R11–R14's tests for both maps.
- `tests/test_retro.py`: `MOVED`-style lists untouched; nothing else unless a key check needs
  `surface`.
- `docs/REFERENCE.md` (*Retrospectives*): `surface`, its fields, `RETIRE_AFTER`, the unmeasured
  rule.
- `README.md`: a pointer to both maps.
- `docs/RETRO-SCORECARD.md`: S5's Simplicity rows marked fed.
- `AGENTS.md`: the factory paragraph names the new read (skill folder names and `@command` names
  as text, for the inventory); the retrospective paragraph names `surface`.

Reused, not re-derived: `sdlc.bash_commands()` for a skill's commands, `_coverage()` for the
coverage block, `sdlc.closed_changes()` and `sdlc.retrospectives()` for windows,
`sdlc._release_tags()` for tags, `indicators.grep_counts()` (as `_line_counts()` uses it) for line
counts, `sdlc._own_repo()` and `sdlc.factory_enabled()` for R3/R10's conditions.

## Work order

1. **The trailer** (R1). Test first in `test_metrics.py` from the existing fixture transcripts (a
   skill typed twice, one started by the Skill tool), then `summarize()`/`trailers()`/
   `parse_trailers()`.
2. **The inventory and its use** (R2–R7). `surface()` in `retro.py` with the current window only:
   inventory from the code, use from `skills`/`tools`, keys from the base branch's raw config,
   states with their `why`, share and coverage. Tests in `test_surface.py`.
3. **Retire** (R8). Walk earlier windows from `sdlc.retrospectives()`; tests with scratch repos
   holding `Retrospective` commits and `Close` commits carrying trailers.
4. **Footprint** (R9). `setup.json` and the config at the base branch, `.sdlc/` lines via `git
   grep -c`.
5. **Growth** (R10). Release tags plus the one before; a scratch repo with two tags, `_own_repo`
   stubbed true.
6. **FEATURES.md** (R11, R12, R14) with its test.
7. **PROCESS.md** (R13) with its test.
8. **Docs** (R15) and `./check.sh` through the factory's `check`.

## Tests

- R1: `test_close_names_each_skill_it_ran` (`tests/test_metrics.py`).
- R2: `test_the_surface_is_the_code`.
- R3: `test_the_factory_command_regex_finds_every_command`, plus
  `test_the_factory_is_listed_only_when_in_play`.
- R4: `test_a_call_counts_once`, `test_a_key_is_used_when_the_config_sets_it`.
- R5: `test_an_unrecorded_item_is_never_unused`.
- R6: `test_every_skill_says_where_it_runs`.
- R7: `test_the_share_leaves_out_the_unmeasured`.
- R8: `test_retire_needs_n_unused_windows`.
- R9: `test_footprint_counts_what_setup_left`.
- R10: `test_growth_reads_each_release_tag`.
- R11, R14: `test_every_fixed_term_has_an_entry`, `test_the_maps_cite_no_change_and_hold_no_html`
  (`tests/test_feature_map.py`).
- R12: `test_the_feature_map_points_at_real_things`.
- R13: `test_the_process_map_holds_every_stage_skill_and_wait`.
- R15: `./check.sh` via `factory.py check 179`; the docs edits by review. Mermaid rendering on
  GitHub: manual, by eye on the pushed branch.

## Departures, as built

- **`SKILL_RUNS` has a third class, `supervised`,** for `/sdlc-factory:build` and `land`: the
  supervisor's session keeps a change's typed command but none of its calls
  (`metrics._supervised()`), so a command only those skills run is `unmeasured` ("runs outside a
  change's sessions"), never `unused`. A recorded use always makes an item `used`, whatever its
  class (an agent's `factory.py check`). Raised as a default decision.
- **`OWN_REPO_COMMANDS`** (`cases`, `run-cases`) are left out of a host's inventory, as `prose`
  leaves out ship's cases branch: `test_a_hosts_retrospective_never_mentions_the_cases` holds a
  host's retro to saying nothing of the skills' cases.
- **The retire walk** reads an earlier window's `Close` trailers through `_window_trailers()`
  (`closed_changes(read=False)` and one `git show` of the bodies) rather than `closed_changes()`'s
  three git calls a change, and stops for a kind at a window `_counted_before()` that kind: a
  window with a change measured from transcripts and no line of the kind. A window with nothing
  recorded is passed over.
- **`tests/test_surface.py`** holds R2–R10's tests (calling `surface()` directly; one test checks
  `retro()` returns the same), beside `test_retro.py`, which is already over 3,000 lines.
- `test_the_surface_is_the_code`'s growth regex test also pins `COMMAND_RE` to `sdlc.py`'s own
  registry, which `_growth()` reads at each tag.

## Rollback

`git revert` undoes all of it. The one thing it doesn't: `Close` commits made while this was in
place carry `Sdlc-Skill` lines. They stay in history, harmless: `parse_trailers()` after a revert
puts an unknown key under `out["skill"]` and nothing reads it.
