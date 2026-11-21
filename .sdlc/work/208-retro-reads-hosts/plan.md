---
id: 208
slug: retro-reads-hosts
kind: plan
created: 2026-11-21
updated: 2026-11-21
---

# 208 — The retrospective reads what the local host repos show · plan

> Written by the builder after reading `scripts/retro.py` (`report_figures()`, `retro()`,
> `render_report()`, `insight_bundles()`, `metrics_summary()`, `_uses()`, `_keys_set()`), and
> `scripts/sdlc.py`'s `closed_changes()`, `dropped_changes()`, `load_config()`,
> `_resolve_trunk()`, `main_root()`, `_own_repo()`, `plugin_installs()` and `parse_installs()`.

## Files to change

- `scripts/retro.py`: a new section, "the hosts" (R1–R9, R12): `HOSTS_FILE`, `HOST_NOTE`,
  `UNREADABLE`, `HOSTS_UNMEASURED`, `host_list()`, `read_host()`, `_host_safe()`, `_vocabulary()`,
  `_scrub()`, `_pool()`, `_discover()`, `hosts_figures()`; `report_figures()` calls it once and
  `retro()` returns it as `hosts`. `_hosts_text()` and `{{hosts}}` in `render_report()` (R11).
  `INSIGHT_DATA` gains the R13 slices, and `insight_bundles()` adds `hosts.state`, `hosts.why`
  and `hosts.read` to every bundle (R13). `cmd_hosts()`, the terminal view (R10). The module
  docstring gains the vocabulary rule, `cmd_retro()`'s docstring the outside read (R16).
- `scripts/sdlc.py`: the `hosts` command's adapter (`@command("hosts", …)` calling
  `retro.cmd_hosts`), in neither `READ_ONLY` nor `ALLOW_RULES` (R10). Reused, unchanged:
  `closed_changes()`, `dropped_changes()`, `load_config()`, `_resolve_trunk()`, `main_root()`,
  `_own_repo()`, `plugin_installs()`, `plugin_version()`, `SEMVER_RE`, `CONFIG_KEYS`,
  `TEMPLATE_DIR`, `COMMANDS`.
- `scripts/retro.py` reuses `metrics_summary()`, `_way()`, `_keys_set()`, `TOOL_CALL_RE`,
  `COMMAND_RE`, `_skill_dirs()`, `FACTORY_DIR`.
- `templates/retro.md`: a `## Hosts` section holding `{{hosts}}`, last (R11); its note says so.
  Not in `TEMPLATE_READS` (an override without it renders as before).
- `.gitignore`: `.sdlc/hosts.local` (R1).
- `skills/retro/SKILL.md`: the direction pass reads `hosts`; the reply's unlisted count and
  `sdlc.py hosts` (R14). No new command run.
- `agents/insight.md`: how to read `hosts` (R15).
- `AGENTS.md` *Retrospectives*, `docs/CONTRIBUTING.md`, `docs/REFERENCE.md` *Retrospectives*,
  `docs/FEATURES.md` (R16).
- `tests/test_retro_hosts.py` (new): every R-test the spec names.
- `tests/test_retro.py`: `SECTIONS` gains `Hosts`.

## Work order

1. **The list.** `host_list()` reads `.sdlc/hosts.local`'s text: paths, `!` exclusions, `~`,
   comments, blanks. Test: `test_the_host_list_format` (portable).
2. **Gating.** `hosts_figures()` returns `unmeasured` outside the own repo and with no list,
   calling nothing; `report_figures()`/`retro()` carry `hosts`. Tests:
   `test_a_host_repo_never_reads_hosts`, `test_no_host_list_is_unmeasured`.
3. **Reading one host.** `read_host()` through `main_root()`, `load_config()`, `closed_changes()`,
   `dropped_changes()`, `git show` for `setup.json` and the templates tree, `_keys_set()`; reason
   words for failures. Own and duplicate skipping in `hosts_figures()`. Tests:
   `test_host_reads_are_log_and_show_only`, `test_an_unreadable_host_is_counted_not_fatal`.
4. **The figures.** `_host_safe()` reduces records to the vocabulary before `_pool()` summarises;
   `window`, `all`, `busiest`, `versions`, `surface`; `_scrub()` drops any leaf string outside the
   vocabulary as a last guard, counted in `read.dropped_names`. Tests:
   `test_two_fixture_hosts_give_known_counts`, `test_older_trailers_are_unmeasured_not_zero`,
   `test_no_host_name_or_path_reaches_the_output` (JSON parts), `test_host_figures_never_move_this_repos_figures`.
5. **Discovery.** `_discover()` over `plugin_installs()`, only with a list; count only, or
   `discovery: "unmeasured"`. Test: `test_discovery_counts_unlisted_installs`.
6. **The report.** `{{hosts}}`, `_hosts_text()`. Tests: `test_the_report_has_a_hosts_section`,
   `test_a_template_without_hosts_renders_as_before`, the report part of the no-name test.
7. **Insights.** `INSIGHT_DATA` slices and `hosts.read` in every bundle. Test:
   `test_insight_bundles_carry_host_slices`, and the insights part of the no-name test.
8. **The command.** `cmd_hosts()` and its adapter. Tests:
   `test_hosts_command_prints_paths_and_writes_nothing`, `test_hosts_is_not_read_only`.
9. **Words.** Skill, agent, docs, feature map. Tests: `tests/test_skills.py`,
   `tests/test_feature_map.py`, `tests/test_nothing_local.py`, `tests/test_defaults.py`.

## Tests

All in `tests/test_retro_hosts.py` unless named. Fixture hosts are repos under `tmp_path` built
with `Close`/`Drop` commits as `tests/test_retro.py` builds them; "this repo" is a fixture with
the `sdlc` manifest and `scripts/sdlc.py`, so `_own_repo()` holds.

- R1: `test_a_host_repo_never_reads_hosts`.
- R2: `test_no_host_list_is_unmeasured`.
- R3: `test_the_host_list_format` (portable), and own/duplicate skipping in
  `test_two_fixture_hosts_give_known_counts`.
- R4: `test_host_reads_are_log_and_show_only`.
- R5: `test_an_unreadable_host_is_counted_not_fatal`.
- R6: `test_two_fixture_hosts_give_known_counts`.
- R7: `test_no_host_name_or_path_reaches_the_output`.
- R8: `test_older_trailers_are_unmeasured_not_zero`.
- R9: `test_discovery_counts_unlisted_installs`.
- R10: `test_hosts_command_prints_paths_and_writes_nothing`, `test_hosts_is_not_read_only`.
- R11: `test_the_report_has_a_hosts_section`, `test_a_template_without_hosts_renders_as_before`;
  `tests/test_retro.py`'s section-order tests with `Hosts` added.
- R12: `test_host_figures_never_move_this_repos_figures`.
- R13: `test_insight_bundles_carry_host_slices`.
- R14, R15: words; `tests/test_skills.py` still passes. Judged by review.
- R16: `tests/test_feature_map.py` (the `hosts` command mapped).

## Where the build departed from this plan

- `cmd_hosts()` lives in `scripts/retro.py`, beside `cmd_retro()` and the readers it shares; the
  `hosts` adapter in `sdlc.py` calls it (the spec put it in `sdlc.py`).
- `sdlc.dropped_changes()` gains `drop_at`, the `Drop` commit's time (`%cI`), so the window
  compares drops by time as it compares closes by `close_at`. Additive: every other key is as it
  was.
- `read` gains `repeated`, a listed path whose main checkout another line already named, so
  `listed` = `read` + `own` + `repeated` + the unreadable.
- `dropped_at` is kept to `sdlc.REACHED` (the change stages a drop records), not
  `metrics.STAGES`, which names no `spec` or `plan`.
- `docs/FEATURES.md` maps no script command (each is in `surface`), so the `hosts` figure gets an
  entry under *The retro's figures* and `tests/test_feature_map.py` has nothing to fail on for
  the command (R16's test line).
- A variable named `main` in a git call trips `test_no_git_call_names_main_itself`, so a host's
  main checkout is `checkout` in `read_host()`.

## Rollback

`git revert` undoes all of it. Nothing is written outside this repo: host reading is git reads
only, and `.sdlc/hosts.local` is the person's own gitignored file, which a revert leaves on disk
(harmless: nothing reads it then; `rm .sdlc/hosts.local` to remove it). A retrospective report
committed with a `## Hosts` section keeps it; history is not rewritten.
