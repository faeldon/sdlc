---
id: 179
slug: feature-inventory
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 179 — A map of what the plugin offers, and how much of it is used · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code. Each one is a fact this design rests on:

- Skill runs are already events. `metrics.py` emits a `skill` event for every plugin skill a change's session starts, typed or through the Skill tool (`SKILL_RE`, `SKILL_NAME_RE`). No trailer records them by name, though. `Sdlc-Tool` names the `Skill` tool alone (`_prompt_name()`), and `Sdlc-AfterGate` names only the gated skills with a stop. So the intent's "from the `Sdlc-Tool` and `Sdlc-Calls` trailers" covers commands, but not skills. Skills need one new trailer line.
- Command runs are already named. `_prompt_name()` names a plugin script's call `Bash:sdlc.py:<command>` or `Bash:factory.py:<command>`, and `Sdlc-Tool` writes one line per name. A sub-agent's calls and a factory agent's calls are `tool` events too (the module docstring: "A sub-agent's calls … carry its `role`"). So `Sdlc-Tool` already holds them, and `Sdlc-Calls` is a per-role split of the same calls.
- The core inventory is in code. Commands are `sdlc.COMMANDS` (the registry `@command` fills), config keys are `CONFIG_KEYS`, and skills are `skills/*/SKILL.md`, which `prose_metrics()` already globs from `PLUGIN_DIR`. The factory's skills are `plugins/factory/skills/*/SKILL.md`. Its commands are `@command("…"` (or `@command(` then the name on the next line) in `plugins/factory/scripts/factory.py`. Its config keys are not in `CONFIG_KEYS`.
- Only a change's sessions are measured. `read_events()` reads the sessions on the change's branch. A skill run from the main checkout outside any change (`idea`, `bug`, `triage`, `status`, `retro`, `release`, `publish`, `setup`, `uninstall`, `dashboard`, `health`) never reaches a `Close` commit's trailers.
- Windows are the spans between `Retrospective` commits (`sdlc.retrospectives()`), and `closed_changes(home, older, newer)` walks any one of them (`_previous_window()`).
- `_own_repo(home)` already tells this plugin's repo from a host by reading its files.

Requirements:

1. **R1. Close records skill runs.** Close writes one `Sdlc-Skill: <name> runs=<n>` line for each plugin skill a change's events started, and `parse_trailers()` reads it back as `skills: {name: {"runs": n}}`. A `Close` commit without any `Sdlc-Skill` line counts as unrecorded, never as zero. The test is `test_close_names_each_skill_it_ran` in `tests/test_metrics.py`, built from the fixture transcripts the skill events are already read from. It fails if the line is missing, or if a skill started twice counts once.
2. **R2. `retro` reports the core surface.** Its JSON gains `surface`. It lists every core skill, every `sdlc.py` command and every `CONFIG_KEYS` key, built from the code at run time, never from a hand-kept list. `test_the_surface_is_the_code` fails if a command registered in `COMMANDS`, a key added to `CONFIG_KEYS` or a skill folder added under `skills/` is missing from `surface`.
3. **R3. The factory's surface is listed when the factory is in play.** Its skills and `factory.py` commands appear, each tagged `plugin: "sdlc-factory"`, when `factory_enabled()` is true or the repo is the plugin's own. Otherwise they are left out. The commands are read from `factory.py`'s text by a regex copy. `test_the_factory_command_regex_finds_every_command` pins that copy to `factory.py`'s own `COMMANDS`, so a new decorator shape fails it.
4. **R4. Each item's use in the window.**
   - A skill's use is the sum of its `Sdlc-Skill` runs.
   - A command's use is the sum of its `Bash:sdlc.py:<c>` or `Bash:factory.py:<c>` calls on `Sdlc-Tool`, each call counted once. `Sdlc-Calls` is never added on top.
   - A key is used when the base branch's `.sdlc/config.toml` sets it explicitly. The file is read raw, not merged over the defaults.

   `test_a_call_counts_once` fails if a call that appears on both `Sdlc-Tool` and `Sdlc-Calls` counts twice.
5. **R5. An item with no record is `unmeasured`, never `unused`.** Each item's `state` is one of `used`, `unused` or `unmeasured`, and an unmeasured item carries a `why`:
   - A skill classed as running outside a change: "runs outside a change's sessions".
   - A command no skill's bash blocks run (`sdlc.bash_commands()` over every `SKILL.md` and side file): "no skill runs it".
   - Any skill or command when no change in the window recorded the kind of trailer that would show it: "no change recorded it".

   `test_an_unrecorded_item_is_never_unused` checks all three.
6. **R6. Every skill is classed by where it runs.** A constant in `retro.py` names each skill that is not a key of `metrics.SKILL_STAGE` as running inside or outside a change. `test_every_skill_says_where_it_runs` fails when a skill folder, core or factory, is in neither.
7. **R7. Share of the surface used.** `surface.share` holds `used / (used + unused)` per kind (`skills`, `commands`, `keys`) and overall, with unmeasured items outside the denominator. Beside it sits a `coverage` block in `_coverage()`'s shape: the window's changes that carry `Sdlc-Skill` or `Sdlc-Tool` lines, and why the rest are missing. `test_the_share_leaves_out_the_unmeasured` covers it.
8. **R8. Retire candidates.**
   - An item is a candidate when it was `unused` in each of the last `RETIRE_AFTER` windows (default 3), the current one included.
   - A window in which the item was `unmeasured` doesn't count toward the run, and doesn't break it.
   - With fewer measured windows than `RETIRE_AFTER`, there are no candidates, and `surface.retire` says how many windows it rests on.

   `test_retire_needs_n_unused_windows` fails if an item unused in N−1 windows, or unmeasured in one of N, is named.
9. **R9. Footprint.** `surface.footprint` holds three counts:
   - the paths in `.sdlc/setup.json`'s `created` on the base branch;
   - the keys the base branch's config sets;
   - the lines of tracked files under `.sdlc/` on the base branch, not counting the change folders (`work_rel()`), `retros/` or `reports/`.

   Without a `setup.json` the field is `null` with a `why`. `test_footprint_counts_what_setup_left` covers it.
10. **R10. Growth per release, in the plugin's own repo only.** `surface.growth` has one row per release tag in the window, plus the tag before the first. Each row holds `skills`, `commands`, `keys`, `doc_lines` and their change since the previous tag, all read at that tag. It also holds `capability`: the changes between the two tags with `impact` `major` or `minor`. A count that can't be read at a tag is `null`: no `@command` match in the script before the registry, or no `setup.json`. In a host, `growth` is `null` with `why: "only in the plugin's own repo"`. `test_growth_reads_each_release_tag` uses a scratch repo with two tags.
11. **R11. `docs/FEATURES.md` maps every feature.**
    - Each entry is a bullet `` - **`<term>`**: <one-line definition>. Specified: <path>. Depends on: <terms>. ``
    - The entries sit in sections: skills, stages, tiers, impacts, nits, review passes, the board, tracking documents, trailers, the retro's figures, and vocabulary.
    - A Mermaid `graph` shows the sections and how they depend on each other.

    `test_every_fixed_term_has_an_entry` (`tests/test_feature_map.py`) fails when any of these lacks an entry:
    - a `STAGES` value, a tier (0, 1, 2), an `IMPACTS` value, a `NIT_COSTS` or `NIT_VALUES` value, a `FINDING_PASSES` or `SHIP_PASSES` value;
    - a skill, core or factory, written `/sdlc:<name>` or `/sdlc-factory:<name>`;
    - a board column from `board.html`'s column array;
    - an `Sdlc-*` trailer key that `metrics.py`'s `trailers()` family writes.
12. **R12. The feature map points only at real things.** `test_the_feature_map_points_at_real_things` fails when:
    - a `Specified:` path doesn't exist in the repo;
    - a `Depends on:` term isn't another entry's term;
    - a graph node isn't a `##` section, or a section has no graph node.
13. **R13. `docs/PROCESS.md` maps the three loops** (change, release, retro) as Mermaid flowcharts, in FEATURES.md's terms. Each stage shows its skill, the `sdlc.py` calls it makes, its checks (gate, acceptance checks, review passes) and what it writes. Each WAIT is a node labelled `WAIT: /<plugin>:<skill>`. `test_the_process_map_holds_every_stage_skill_and_wait` fails when:
    - a skill is missing;
    - a `STAGES` value isn't written as `stage: <value>`;
    - the skills with a `WAIT` heading in their `SKILL.md` differ from the skills named in `WAIT:` nodes.
14. **R14. The maps stay clean.** Neither map commits generated HTML, and neither cites a change by its folder number. `tests/test_nothing_local.py` already scans `docs/`, and R11's test also refuses a line matching `\b\d{3}-[a-z]`.
15. **R15. Docs follow.**
    - `docs/REFERENCE.md` *Retrospectives* describes `surface` and its fields, `RETIRE_AFTER` and the unmeasured rule.
    - The `metrics.py` docstring adds `Sdlc-Skill` to the contract.
    - README.md points to both maps.
    - `docs/RETRO-SCORECARD.md` marks the Simplicity rows S5 fed: share used, footprint, growth, never-used.
    - AGENTS.md's factory paragraph names the new read of the factory's files (see Contracts).
    - `./check.sh` passes.

## Design

**The trailer (`scripts/metrics.py`).** `summarize()` already walks every event. It gains a `skills` count, `{name: runs}`, from `kind == "skill"` events. `trailers()` writes it as `Sdlc-Skill: <_word(name)> runs=<n>` lines, sorted by name, after the `Sdlc-Tool` lines. `parse_trailers()` gets an `elif key == "skill" and name:` branch beside `tool` and `calls`. Nothing existing is redefined, and the docstring says that a commit without the line was closed before skills were counted.

**The inventory and its use (`scripts/retro.py`).** One new public function, `surface(home, cfg, changes, since)`, is called from `retro()` and returned as `"surface"`.

1. **Inventory.**
   - Core skills come from `sdlc.PLUGIN_DIR / "skills"`, core commands from `sdlc.COMMANDS` and keys from `sdlc.CONFIG_KEYS` as `section.key`, minus `RETIRED_KEYS`.
   - The factory's skills and commands come from `PLUGIN_DIR / "plugins/factory"`. The command regex is `@command\(\s*"([a-z][a-z0-9-]*)"`, read from the file's text and never imported. They are included under R3's condition.
   - Each item is `{kind, name, plugin}`.
2. **Use.**
   - For each change, take `rec["metrics"]` (already parsed) and read `skills` and `tool`.
   - A `Bash:sdlc.py:<c>` or `Bash:factory.py:<c>` tool name maps to command `c` of that script. Everything else on `Sdlc-Tool` is ignored.
   - Keys: `sdlc._git(home, "show", f"{trunk}:.sdlc/config.toml")`, parsed with `tomllib`, flattened to `section.key`.
3. **State** (R5). This is where an unrecorded item stays apart from an unused one.
   - Where a skill runs comes from a dict, `SKILL_RUNS = {"sdlc:idea": "outside", …}`, covering every skill that is not in `metrics.SKILL_STAGE`. A skill in `SKILL_STAGE` runs in a change.
   - A command's callers are found once by running `sdlc.bash_commands()` over each skill's `SKILL.md` and side files. These are the same texts `prose_metrics()` reads, so their reading is shared rather than copied.
   - A command whose only callers run outside a change is `unmeasured` too.
4. **Share and coverage** (R7) reuse `_coverage(changes, measured, why)`, where `measured` is "has `skills` or `tool`".
5. **Retire** (R8). Walk back through `sdlc.retrospectives(home, trunk)` to get the last `RETIRE_AFTER - 1` earlier windows' `closed_changes`, then run step 2 and step 3 on each. Key use in an earlier window is read from the config at that window's end commit. A module constant `RETIRE_AFTER = 3` sits beside `ARCH_LOOKBACK`.
6. **Footprint** (R9). `setup.json` is read with `git show <trunk>:.sdlc/setup.json`. The `.sdlc/` lines come from one `git diff --numstat <empty-tree> <trunk> -- .sdlc/` with the change folders (`work_rel()`), `retros/` and `reports/` left out. Paths are compared as git prints them (`as_posix()`).
7. **Growth** (R10). Taken only when `sdlc._own_repo(home)` is true. The tags are `sdlc._release_tags(home, cfg, since)` plus the tag before the first.
   - At each tag, skills come from `git ls-tree -r --name-only <tag> -- skills plugins/factory/skills`, filtered to `*/SKILL.md`.
   - Commands come from the regex over `git show <tag>:scripts/sdlc.py` and `factory.py`.
   - Keys come from `setup.json`'s `config_keys` at the tag.
   - `doc_lines` comes from one numstat against the empty tree over `skills/ plugins/factory/skills/ agents/ plugins/factory/agents/ guide/ defaults/ templates/ docs/ README.md`.
   - `capability` comes from `sdlc.closed_changes(home, prev_tag, tag)`, filtered by impact.

Every `git` call goes through `sdlc._git`, so it is read-only and UTF-8. `retro` stays read-only but for its report. `--metrics`/`_lean()` is untouched: `surface` holds names and counts, not one change's numbers.

**The maps.** Both are hand-written prose, checked by `tests/test_feature_map.py` against the code (one test file for both maps).

- **`docs/FEATURES.md`.**
  - It opens with a one-paragraph note on what it is.
  - Then one `##` section per group, with R11's bullets. The Vocabulary section holds the terms the code doesn't fix: change, gate, WAIT, stop, seed, finding, landed, retro, direction, outcome, drift.
  - Then a Mermaid `graph LR` whose nodes are the sections.
  - The test parses the bullets with one regex, `^- \*\*`([^`]+)`\*\*:`. It reads the code's terms from the loaded `sdlc` module (`STAGES`, `IMPACTS`, `NIT_COSTS`, `NIT_VALUES`, `FINDING_PASSES`, `SHIP_PASSES`, `TIER_ARTIFACTS` plus tier 0), the skill folders, `board.html`'s `key:`/`label:` column array, and the `Sdlc-…:` literals in `metrics.py` and `sdlc.py`'s trailer writers.
- **`docs/PROCESS.md`.** Three `flowchart` blocks (change, release, retro), each with a short lead paragraph. The test reads each `SKILL.md`'s headings for `WAIT` with the same rule `test_skills.py` uses.

**What isn't built.** Nothing renders `surface` in the report page: `templates/retro.md` and the retro skill are unchanged. Turning the figures into the scorecard's Simplicity row is S14's job. Setup copies neither map.

## Contracts touched

- **Metrics trailers are a contract: extend, never redefine** (AGENTS.md, *Metrics*). `Sdlc-Skill` is a new line. No existing line, key or meaning changes, and an old `Close` commit reads as unrecorded. Measuring still never refuses: a failure inside `summarize()` falls under the existing `Sdlc-Coverage` handling.
- **Modules loaded by path; `metrics.py` pure.** The new counting in `metrics.py` uses events only: no subprocess, no import of `sdlc.py`. `retro.py` reads everything as `sdlc.<name>`.
- **⚠ The factory boundary needs a policy edit.** AGENTS.md lists every file `sdlc` reads of the factory: run files, `gate_jobs`, slot locks, the train's run lock, `[ui]` and screenshots. Each read uses a copy of `factory.py`'s parsing, pinned by a test. R3 adds one more read: `plugins/factory/skills/*/SKILL.md` names and `factory.py`'s `@command` names, as text, for the inventory. It never runs or imports `factory.py`, and `test_the_factory_command_regex_finds_every_command` pins the copy. This is a change to the map's list of crossings. The person decides it; it is not a side effect. If the answer is no, R3 is dropped and the inventory is core only (see Alternatives).
- **`retro` is read-only but for its report** and runs host commands only in `_evidence()`. `surface` runs only `git` reads and reads files.
- **Nothing about a project or a workspace.** The maps use the plugin's own terms and no change folder numbers (R14).
- **One shape for the shipped docs** (`tests/test_defaults.py`) covers only `defaults/` and `templates/`. Neither map goes there, and setup copies neither, so `sdlc.py record` doesn't run and `drift` is unaffected.
- **The scripts run on Windows.** There is no new subprocess outside `sdlc._git`, every compared path is `as_posix()`, and `tests/test_feature_map.py` reads with `encoding="utf-8"`. The map tests are marked `portable`; they need no shebang fakes.
- **Context docs** (`[docs] context`): this change makes README.md, docs/REFERENCE.md and AGENTS.md need edits, and R15 makes them in this change.
- **Release, publish and measuring never read the register.** None of this reads `inbox.md`.

## Alternatives rejected

- **`retro` reads the inventory from `docs/FEATURES.md`.** The intent's constraint forbids it ("built from the code, never kept by hand"), and a host may have no copy of `docs/` it could find. The code is the inventory, and FEATURES.md is checked against it.
- **One FEATURES.md entry per `sdlc.py` command and per config key.** There are over 70 commands across the two scripts, and around 45 keys, which `docs/REFERENCE.md` already documents. Copying them would make a second hand-kept list. FEATURES.md maps the terms a person reads; `surface` lists every command and key.
- **Counting a skill's use from the `sdlc.py` commands it runs.** Most skills start with `config`, so no command tells one skill from another. A trailer named after the skill is exact.
- **Counting unrecorded items as unused.** In the first windows after this lands, every older `Close` commit lacks `Sdlc-Skill`. Counting those as unused would make every skill a retire candidate. Reading them as unmeasured keeps a gap from being read as zero (the Trust band).
- **N as a config key.** A key added to measure how many keys go unused grows the very surface it measures. It is a constant, `RETIRE_AFTER`, and changing it is a change.
- **Growth in a host.** A host's tags are its own releases, not the plugin's. The plugin's surface at a host's tag means nothing.
- **A setup copy of the maps.** It would add files to every host's footprint (against O5) and a drift surface under `defaults/` (`irreversible`), for docs that describe the plugin and are read on GitHub. If wanted later, it's a change of its own.
- **Generated HTML or a diagram tool.** The intent rules it out. Mermaid renders on GitHub as written.
- **Leaving the factory out of the inventory.** This avoids the policy edit, but `surface` would then miss a third of the skills and the factory's commands, whose use is the most worth knowing. It is the fallback if the policy edit is refused.

## Verification

```bash
uv run --group dev pytest tests/test_feature_map.py tests/test_metrics.py tests/test_retro.py -q -n auto
uv run --group dev pytest -q -m portable
uv run --quiet --script scripts/sdlc.py retro | python3 -c 'import json,sys; s=json.load(sys.stdin)["surface"]; print({k: s[k] for k in ("share","coverage")}); print(len(s["retire"]["items"]), s["growth"] is not None)'
./check.sh
```

Healthy output:

- The named tests pass, and the portable run includes `test_feature_map.py`.
- `retro`'s `surface` lists every skill, command and key. Because no `Close` commit before this one has `Sdlc-Skill`, skills show `unmeasured` ("no change recorded it"). Commands show use from `Sdlc-Tool`. `retire.items` is empty while fewer than three measured windows exist, and `growth` is a list here.
- GitHub's preview of both docs renders every Mermaid block. Check this by eye on the pushed branch.
- `./check.sh` ends green, `claude plugin validate --strict` included.

The behaviour to watch in review: an item counted `unused` when its window recorded nothing, a call counted twice across `Sdlc-Tool` and `Sdlc-Calls`, and a change number cited in either map.

