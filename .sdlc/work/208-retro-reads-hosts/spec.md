---
id: 208
slug: retro-reads-hosts
kind: spec
created: 2026-11-21
updated: 2026-11-21
---

# 208 — The retrospective reads what the local host repos show · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code before designing:

- `closed_changes()`, `dropped_changes()` and `metrics.parse_trailers()` take any repo root as `home`. They run only `git log` and `git show` there (`scripts/sdlc.py`), so pointing them at a host's main checkout reads that host's history with this plugin's readers and no new parser.
- `retro.evidence` output never reaches an `sdlc:insight` agent (189 R4: `HOST_COMMANDS`, and `INSIGHT_DATA` naming no `product.evidence`). It is also never rendered into the report (`render_report()` has no evidence placeholder). An evidence script therefore can't give agents or the report host figures. Only `retro.py`'s own reading can.
- `plugin_installs()` is the one reader of `claude plugin list --json`, and `parse_installs()` already gives each install's `scope` and resolved `project` path.
- `_own_repo()` decides "the plugin's own repo" from its files, and `surface` is already gated on it.
- `_keys_set()` reads the raw `section.key` names a config sets. `_way()` reads the way of building from `Sdlc-Mode` alone. `metrics_summary()` gives medians per tier and way, and per stage, from any list of closed changes.
- A host's free-text trailers exist (`Sdlc-Origin`, `Sdlc-Base`, prompt names such as `Bash:<program>:…`, role names). So reading trailers is not enough to keep a host's words out. The output also needs a vocabulary filter (R7).

Requirements:

1. R1. Host reading happens only in the plugin's own repo (`_own_repo()`), from `.sdlc/hosts.local` in its main checkout (`main_root()`), which `.gitignore` lists. Anywhere else, `retro`'s `hosts` block is `{"state": "unmeasured", "why": "read only in the plugin's own repo"}`. `test_a_host_repo_never_reads_hosts` fails if a non-own fixture with a `hosts.local` reads one.
2. R2. With no `.sdlc/hosts.local`, `hosts` is `{"state": "unmeasured", "why": "no host list"}`: no count is 0, no git call is made outside the repo, and `claude plugin list` is not run. `test_no_host_list_is_unmeasured` fails if any count appears or a subprocess runs against another path.
3. R3. The list format is one absolute path per line (`~` expanded). Blank lines and `#` lines are ignored. A `!<path>` line excludes that repo from discovery for good and is never read. A listed path resolving to this repo's main checkout, or one of its worktrees, is skipped and counted as `own`. Two lines resolving to the same main checkout are read once. `test_the_host_list_format` covers each case.
4. R4. Each listed host is read through `closed_changes()` and `dropped_changes()` on its main checkout. Its base branch comes from `_resolve_trunk()` over its own `load_config()`, and nothing else in it runs: no host command, hook, fetch or write. `test_host_reads_are_log_and_show_only` records every subprocess argv made against a fixture host. It fails on any git subcommand outside `log`, `show`, `rev-parse`, `symbolic-ref` and `for-each-ref`, and on any non-git program.
5. R5. A host that can't be read (missing path, not a git repo, no base branch, any exception while reading it) is counted under `unreadable` by a fixed reason word (`missing`, `not-a-repo`, `no-base`, `failed`). It is never a failed retro and never a zero in the figures. `test_an_unreadable_host_is_counted_not_fatal` fails if `retro` exits non-zero or the host's changes count as 0.
6. R6. `retro`'s output gains a top-level `hosts` block, built in `report_figures()` so `retro`, `retro --insights` and the report agree. It has six parts:
   - `read`: `listed`, `read`, `own`, `excluded`, `unreadable` by reason, `unlisted` (or `null` with `discovery: "unmeasured"`), a fixed `note`, and `unmeasured`.
   - `window`: closes and drops after this repo's last `Retrospective` commit's commit time. Holds `closed`, `dropped`, `by_way`, `tiers`, `dropped_at` by stage, escapes (`fixes`, `reworks`), `prompts` as a total, and `metrics_summary()`'s groups.
   - `all`: the same counts over each host's whole history, plus `drop_share`.
   - `busiest`: the host with the most closed changes, its `all` medians by way.
   - `versions`: hosts by recorded `setup.json` version, and `behind`.
   - `surface`: plugin skills by hosts and runs, plugin commands by calls, plugin config keys by hosts setting them, plugin templates by hosts overriding them.

   `test_two_fixture_hosts_give_known_counts` builds two fixture hosts with known `Close`/`Drop` commits and trailers (factory and manual, tiers 1 and 2, one `Sdlc-Fixes`, one `reworks:`, one older `Close` with no `Sdlc-Totals`). It asserts every count.
7. R7. Nothing in `hosts` names a host. Every leaf is a number, bool, null, or a string from a fixed vocabulary:
   - tier `0`/`1`/`2`/`unknown`
   - `metrics.STAGES`
   - way `factory`/`manual`/`unknown`
   - a `SEMVER_RE` version or `unknown`
   - a plugin skill folder's name
   - a `CONFIG_KEYS` key
   - a `templates/` file name
   - a `TOOL_CALL_RE` command
   - the reason words and the fixed `note`

   Anything else is dropped and counted under `read.dropped_names`, never shown. Prompt names, role names, `Sdlc-Origin`, `Sdlc-Base`, change names, titles, dropped reasons and `problems` from host records never enter. `test_no_host_name_or_path_reaches_the_output` puts a distinctive directory name, a branch name, a title, a dropped reason, a free-text `Sdlc-Origin` and a `Bash:<host-program>` prompt into the fixtures. It fails if any of them, or the tmp path, appears in `retro`'s JSON, `retro --insights`' JSON or the rendered report.
8. R8. An older host's thinner trailers are read where they exist. A change whose `Close` commit lacks `Sdlc-Totals` counts in `closed` and `by_way` (as `unknown` without `Sdlc-Mode`) and stays out of every median, as `metrics_summary()` already does (`uncaptured`). A change whose intent isn't at `work_rel()` (one closed under the old `work/`) has tier `unknown`. `HISTORY_WORK` gains no new reader. `test_older_trailers_are_unmeasured_not_zero` fails if such a change lowers a median or is left out of `closed`.
9. R9. Discovery runs only when a list exists. It takes `plugin_installs()`'s `sdlc` rows at `project` or `local` scope, leaves out this repo's main checkout and anything under its `.claude/worktrees/`, and subtracts the listed and `!`-excluded paths, compared resolved and `as_posix()`. `retro` reports only the count, `read.unlisted`. If `plugin_installs()` fails, it reports `discovery: "unmeasured"`, never its reason text (which can hold a path). `test_discovery_counts_unlisted_installs` stubs `plugin_installs` and fails if a path or reason string appears in the output, or if the count is wrong.
10. R10. A new read-only command, `sdlc.py hosts`, prints to the terminal each listed host's state (read, or unreadable and why) and each unlisted discovered repo's path. Each unlisted path gets the two lines to append: `<path>` to read it, `!<path>` to exclude it for good. It writes nothing. It is in neither `READ_ONLY` nor `ALLOW_RULES`, so no model runs it unprompted and pulls paths into a session that writes public text. `test_hosts_command_prints_paths_and_writes_nothing` fails if the tree changes. `test_hosts_is_not_read_only` fails if it is listed.
11. R11. The report gains a `## Hosts` section (`{{hosts}}` in `templates/retro.md`).
    - In the plugin's own repo, it says how many hosts were read of how many listed, how many couldn't be read and how many installed repos aren't listed. Then the `note`: one machine's repos, a sample, never pooled with this repo's figures. Then tables of the window's and all-time counts by way, the median stops and elapsed time by tier and way, factory-built changes all time, and versions.
    - Anywhere else, it renders one line saying other repos are read only in the plugin's own repo.
    - A template without `{{hosts}}` renders as before.

    `test_the_report_has_a_hosts_section` and `test_a_template_without_hosts_renders_as_before` cover these.
12. R12. Host figures stay apart. No host figure enters `process`, `by_way`, `metrics`, `surface`'s states, the `scorecard` or the indicators the next retro reads back, so every history-based figure is unchanged by the list. `test_host_figures_never_move_this_repos_figures` runs `retro` with and without a list. It fails if anything outside `hosts` differs.
13. R13. Each insight bundle carries `hosts.read`. Each pillar also gets its slice through `INSIGHT_DATA`:

    | Pillar | Slices |
    |---|---|
    | Value | `hosts.all`, `hosts.versions` |
    | Speed | `hosts.window.by_way`, `hosts.window.metrics`, `hosts.busiest` |
    | Quality | `hosts.window.escapes`, `hosts.window.dropped_at` |
    | Autonomy | `hosts.window.prompts` |
    | Cost | `hosts.window.metrics` |
    | Simplicity | `hosts.surface` |
    | Tradeoffs | `hosts.all` |

    `test_insight_bundles_carry_host_slices` fails if a pillar's bundle lacks its slice or holds another pillar's. The existing 189 R4 test still passes: no host *command* output reaches a bundle.
14. R14. `skills/retro/SKILL.md` covers two things.
    - **Direction pass:** read `hosts` as evidence from other repos, as it reads `origins.host`. A goal or milestone that waits on another repo's use (G7, M13) is judged from `hosts.all`'s factory-built count, with `read.read` hosts as its `n`, in the skill's own words. No host is ever named.
    - **Reply:** when `read.unlisted` is above 0, the reply says `<n> installed repo(s) not in your host list` and names the command `sdlc.py hosts` for the person to run.

    The skill's rule against quoting evidence covers `hosts` too. `tests/test_skills.py` still passes, since the skill runs no new command.
15. R15. `agents/insight.md` says how to read `hosts`: other repos on this machine, a sample of one person's, never pooled with this repo's and never named. A claim from it cites `read.read` as its `n`.
16. R16. The docs say what is now true:
    - `AGENTS.md` *Retrospectives* and `cmd_retro()`'s docstring: retro now reads outside the repo, in the plugin's own repo, when a host list exists.
    - `docs/CONTRIBUTING.md`: the list, its format, `sdlc.py hosts`.
    - `docs/REFERENCE.md` *Retrospectives*: the `## Hosts` section and its one-line form in a host.
    - `docs/FEATURES.md`: the `hosts` command and the `hosts` figures.
    - `retro.py`'s module docstring: the vocabulary rule.

    `tests/test_feature_map.py` fails while the command is unmapped.

## Design

**Where it lives.** It goes in a new section of `scripts/retro.py`, "the hosts", which `report_figures()` calls once as `f["hosts"] = hosts_figures(home, cfg, since, today)` and `retro()` returns as `hosts`. No new module, since it reuses `sdlc.closed_changes`, `sdlc.dropped_changes`, `sdlc.load_config`, `sdlc._resolve_trunk`, `sdlc.main_root`, `sdlc.plugin_installs`, `metrics_summary()`, `_way()`, `_keys_set()` and `_uses()`. The pieces:

- `host_list(main) -> (paths, excluded, problems)`: reads `.sdlc/hosts.local` (R3). Pure over its text.
- `read_host(path) -> dict | str`: one host's records, or a reason word (R4, R5). It resolves `main_root()`, then `load_config()`, then `_resolve_trunk()`. It calls `closed_changes(host, None, trunk)` and `dropped_changes(host, None, trunk)`. It reads `.sdlc/setup.json`'s `version` from the base branch (`git show`), the raw config key names (`_keys_set(host, trunk)`), and the names of files under `.sdlc/templates/` at the base branch (`git show <trunk>:.sdlc/templates/`, a tree listing). All of it runs inside one `try`, so any failure becomes `failed`.
- `_host_safe(records)`: reduces each record to the R7 vocabulary before any summary is built. Each record keeps `tier`, way, `close_at`, `dropped_at`, `reworks` as a count, and `metrics` with `stages` filtered to `metrics.STAGES` and `skills`/`tools` filtered to the plugin's own names. `prompts` becomes a total, and `roles`, `origin` and `base` are removed. Filtering before summarising, rather than after, means a summary can't carry a name the filter never saw.
- `hosts_figures()`: pools the safe records into `window` and `all`. The window is `close_at` after this repo's last `Retrospective` commit's commit time, read once with `git show -s --format=%cI`. `metrics_summary()` runs over the pooled window records. `busiest` comes from the host with the most `all` closes. `versions` compares each host's version with `sdlc.plugin_version()`, and `behind` counts a lower major or minor. Discovery (R9) follows when a list exists.
- `cmd_hosts()` in `sdlc.py`: the terminal view (R10). It calls the same `host_list()` and `read_host()` and the discovery, then prints paths. It is registered in `COMMANDS` and not in `READ_ONLY`.
- `_hosts_text(hosts, own)` renders `{{hosts}}` (R11). `INSIGHT_DATA` gains the paths in R13, and `insight_bundles()` adds `hosts.read` beside `process.window` for every question.

**The signals, and the privacy rule for each source.**

| Signal | Source | Informs | Rule |
|---|---|---|---|
| Closed, dropped, by way | `Close`/`Drop` subjects, `Sdlc-Mode` | Value; G7, M13 (factory built in a host or not) | counts |
| Stops, elapsed, agent time, tokens per tier, way and stage | `Sdlc-Totals`, `Sdlc-Stage` | Speed, Cost; O3, the product doc's first bet | medians, `metrics_summary()`'s |
| Where drops stopped | `dropped_at:` | Value, Quality; O3 | counts by stage; the reason (prose) never |
| Escapes | `Sdlc-Fixes`, `reworks:` | Quality; O2 | counts |
| Tool prompts | `Sdlc-Prompt` | Autonomy | one total; names never (a program name can be a host's) |
| Skill runs, plugin command calls | `Sdlc-Skill`, `Sdlc-Tool` (`TOOL_CALL_RE` only) | Simplicity: real-host use beside `surface` | plugin names only |
| Config keys set | `.sdlc/config.toml` at the base branch, raw | Simplicity | `CONFIG_KEYS` names only; values never |
| Templates overridden | `.sdlc/templates/` names at the base branch | Simplicity | plugin template names only; content never |
| Version lag | `.sdlc/setup.json` `version` | Value; the update path (O1) | `SEMVER_RE` strings |
| Session friction outside a change (refusals, prompts, errors in `retro`, `setup`, `status` sessions) | Claude Code transcripts | Autonomy | **not read here**: listed in `read.unmeasured` with what would measure it |

The transcripts of a change's own sessions are already read at close by `metrics.read_events()`, whose contract keeps text, paths and session ids out. Their counts reach the host's trailers, so this change reads them there. That leaves the transcripts of sessions outside a change, which are listed as unmeasured.

**Edge cases.**
- An empty list (comments only) reads as `listed: 0`. That is `state: "read"` with zero hosts, and every figure is `null`, not 0, because `n` is 0.
- A host with no `Close` commits is read, and its counts are honest zeros: it was read.
- A host whose `setup.json` is missing, or holds no semver, counts under `versions.unknown`.
- Time: each closed change costs about three `git show` calls in its host. A hundred changes is a few seconds, paid once per `retro` invocation.

### Boundaries

- **Always:**
  - Read only paths the person listed, and only in the plugin's own repo.
  - Report counts and fixed words only.
  - Say how many hosts were read.
  - Keep host figures in `hosts`.
  - Treat a missing list or an unreadable host as unmeasured.
- **Ask first:**
  - Nothing new behind a question: `hosts` is run by the person. The retro skill's single WAIT already covers what it writes, and a host figure reaches the direction doc only in the skill's own words at that WAIT.
- **Never:**
  - Write, fetch, commit or run a command in a host.
  - Read a host's transcripts, prose, titles, branch names, config values or template content.
  - Put a path or name in `retro`'s JSON, the insights JSON or a report.
  - Run `claude plugin list` without a list.
  - Pool host figures into this repo's.

## Contracts touched

- **Nothing about a project or a workspace** (`tests/test_nothing_local.py`). The list is gitignored, like `.sdlc/terms.local`, and read from the main checkout. Everything that reaches a committed report is a count or a fixed word (R7), and the paths are printed only by `sdlc.py hosts` to the terminal. Fixture hosts use neutral names under `tmp_path`, and R7's test is the guard.
- **Retrospectives: "read-only but for its report", "reads nothing outside the repo" (`cmd_retro()`'s docstring), and "from history".**
  - Read-only holds: every host call is a git read (R4).
  - **The second statement moves:** in the plugin's own repo, with a list, retro now reads other repos on this machine. That is the change the intent asks for. The docstring and `AGENTS.md`'s paragraph are edited to say so (R16), and the person should see it as a contract edit, not a side effect.
  - "From history" holds for every figure outside `hosts` (R12).
- **`_evidence()` is the only place a host's commands run.** This holds: host reading runs none of a host's commands (R4), and it is not one of `HOST_COMMANDS`. So `retro --insights` still empties only those. And 189 R4, that no host *command's* output reaches an agent, still holds: `hosts` is the script's own counting.
- **`unmeasured`, never `unused`** and **unrecorded, never none.** These hold: no list, an unreadable host, a failed discovery, a thin trailer and transcripts are each `unmeasured` (R2, R5, R8, R9), and `surface`'s states are untouched (R12).
- **Mechanism vs. policy.** The plugin learns nothing about what a host builds. It reads the plugin's own records in repos the person names, and only in its own repo, as `surface` and the cases are. No config key is added, so `CONFIG_KEYS`, `READS_CONFIG`, setup and `drift` are untouched.
- **`templates/` is `[review] irreversible`.** Adding `## Hosts` to `templates/retro.md` is a host-visible change: every host's next report gains a one-line section. A host's own `.sdlc/templates/retro.md` without `{{hosts}}` is unaffected (R11). This is not `breaking`, since the script reads no new heading from a host's template.
- **Narrow `allowed-tools`; skills' invariants.** The retro skill runs no new command. `hosts` is not in `READ_ONLY` or `ALLOW_RULES`.
- **The scripts run on Windows.** Path comparisons are `resolve().as_posix()`, every subprocess names `encoding="utf-8"`, and `host_list()`'s tests are `portable`.
- **The hosts' confidentiality.** Filtering into a fixed vocabulary before summarising (R7) is the design's answer, and R7's test plants a name of every kind a host could leak.

## Alternatives rejected

- **A second `retro.evidence` script (`.sdlc/hosts.py`).** It would keep the plugin unchanged, but its output never reaches an insight agent (189 R4) and is never in the report. So the direction could cite it only through the skill's reading, and the intent's insight and report outcomes would be lost.
- **A plugin feature behind a `retro.hosts` key, for any host.** It grows the surface and setup's questions, and gives every host a confidentiality decision to make. It also needs `READS_CONFIG` and drift entries. Gating on the own repo leaves the door open, since the reader takes a path list and works anywhere, without deciding it now (left open below).
- **Reading host transcripts now.** Most of what matters is already counted from them at close, in the trailers. Raw transcripts would need their own read of shapes (`.sdlc/REVIEW.md`, *A transcript's shape assumed*) and a privacy argument per field. They stay `unmeasured` with what would measure them.
- **Naming hosts by a hash.** A stable id is still an identifier across committed reports. `busiest` is enough for the comparison the intent asks for.
- **Pooling host figures into the scorecard or `surface`.** The trend would depend on whose machine ran the retro, which breaks reproducibility from git (constraint). The figures sit beside this repo's, never inside them.
- **Discovery in `status`.** `status` runs constantly, and `claude plugin list` costs a subprocess with a timeout. The retro is where the figures are used, and `hosts` is where paths can be shown.
- **Changing `_milestone_verdicts()` so M13 is done only by a host factory landing.** That changes how every milestone is judged, beyond this intent. The figure is enough for the retro's direction pass to judge G7 and M13 by measurement (R14). A rule change can be its own seed.

## Verification

```bash
uv run --group dev pytest tests/test_retro_hosts.py -q     # the new tests: all pass
uv run --group dev pytest tests/test_retro.py tests/test_feature_map.py tests/test_skills.py \
  tests/test_nothing_local.py tests/test_defaults.py -q    # unchanged behaviour: all pass
uv run --group dev pytest -q -m portable                    # what CI's Windows job runs
./check.sh                                                  # the gate: ruff, format, pytest, validate
```

Healthy:
- On a machine with no `.sdlc/hosts.local`, `uv run --quiet --script scripts/sdlc.py retro` prints a `hosts` block of `{"state": "unmeasured", "why": "no host list"}`, and every other key matches a run before the change.
- With a list, `hosts.read.read` equals the readable listed repos, and `hosts.all.by_way.factory` shows whether any host change was factory-built.
- `retro --report` has a `## Hosts` section with counts and the sample note, and no path.
- `uv run --quiet --script scripts/sdlc.py hosts` prints each listed path's state and each unlisted install's path with its two append lines, and `git status` stays clean.
- A grep of `retro`'s JSON, `retro --insights`' JSON and `retro --report` for each listed host's directory name finds nothing.

