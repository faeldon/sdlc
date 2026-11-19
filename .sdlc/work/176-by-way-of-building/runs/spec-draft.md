---
id: 176
slug: by-way-of-building
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 176 — The retrospective compares factory-built changes with hand-built ones · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: 2026-11-19-15

Facts checked in the code before designing:

- A change's way of building is its `Close` commit's `Sdlc-Mode`, read back as `metrics.mode`.
  It is `factory` exactly when the branch's tip holds the change's `decision.md`
  (`closing.measure_change()`, `way = "factory" if decided is not None else "manual"`), and
  `manual` otherwise. A `Close` commit with no `Sdlc-*` lines has no mode.
- `Sdlc-Totals`' `in`, `cache_read` and `out` add up the session's stages and every `Sdlc-Role`
  run. A factory agent's own `claude -p --agent` session counts as a `subagent` run of its role
  (`metrics.py`, `roles`). So tokens are measured the same way on both sides wherever close read
  the transcripts. Dollars come only from `runs/costs.jsonl` (`_cost()`), which only a factory run
  writes.
- `retro_report()` calls `process_views()` before `value_band()`, so a change's `work` is not set
  yet when the throughput rows are built there. `retro()` calls them the other way round.
- `_milestone_verdicts()` (in `sdlc.py`) is read by `retro()`'s `direction.milestones`, by
  `_milestone_follow()` and by `status`'s "milestones done" list (`sdlc.py`, the
  `all(r["verdict"] in ("closed", "shipped", "vanished") ...)` check).

The requirements:

1. **R1. One word for the way.** Every by-way figure reads a change's way from `metrics.mode`
   alone: `factory`, `manual`, or `unknown` when the `Close` commit records none. Nothing infers
   it from a folder's files, its branch or its history. The test
   `test_a_change_with_no_sdlc_mode_counts_as_unknown_way` closes one change with no `Sdlc-*`
   trailers but with a `decision.md` in its folder. It fails if that change counts as `factory`.
2. **R2. Lead time by way.** `process.lead` gains `ways`, which holds for each of `factory`,
   `manual` and `unknown` the `n`, `median` and `p85` (nearest rank) of `Sdlc-Lead`'s `lead`
   over every tier. A way with no measured change is `{"n": 0, "median": null, "p85": null}`.
   The per-tier `groups` are unchanged. The test is `test_lead_time_is_given_by_way_across_tiers`.
3. **R3. Throughput by way and by work class.** Each `process.throughput` row gains two counts:
   - `ways`: `factory`, `manual` and `unknown`, 0 included;
   - `classes`: each of `WORK_CLASSES` plus `unclassed`, from the change's `work.class`, 0
     included.

   For every row, each of the two sums to the row's `total`. The test
   `test_throughput_counts_each_week_by_way_and_by_work_class` fails if a row's counts don't sum
   to `total`.
4. **R4. The report classes before it counts.** `retro_report()` sets each change's `work` (via
   `value_band()`) before it builds the throughput rows, so the report's throughput and `retro`'s
   JSON agree. The test `test_the_report_s_throughput_shows_work_classes` renders a report whose
   window holds a `fix` change. It fails if the report reads `unclassed` for it.
5. **R5. A `by_way` block.** `retro()`'s new top-level `by_way` is built by one pure function,
   `by_way()`, which both `retro()` and `retro_report()` call. It holds:
   - `changes`: the window's closed changes per way.
   - `lead`: copied from R2.
   - `throughput`: per way, `closed`, `weeks` (the window's span in weeks to one place, from
     `since`'s date, or with no `since` the first change's close date, to today; at least 1/7)
     and `per_week` (`closed / weeks`, to two places).
   - `cost`: see R6.
   - `escapes`: see R7.

   `factory`, `manual` and `unknown` each appear in every part. The test
   `test_by_way_gives_every_figure_for_each_way_with_its_n` fails if a way is missing from any
   part, or if `changes` doesn't sum to the window's closed count.
6. **R6. Cost by way, in tokens for both and dollars where recorded.** `by_way.cost` gives each way:
   - `tokens`: `{n, median}`, the median of `in + cache_read + out` from `Sdlc-Totals`, over that
     way's changes whose totals came from transcripts (`_minutes_measured()`);
   - `usd`: `{n, median}`, over that way's landed changes with dollars, the same per-change sums
     `_cost()` reads;
   - for each of the two, `missing_because`, the reasons `_minutes_why()` and `_cost_why()` give.

   A median with `n` 0 is null, never 0. A hand-built change with no `costs.jsonl` is counted
   under `usd.missing_because` as `built by hand`, never as $0. The test
   `test_hand_built_cost_compares_in_tokens_and_is_missing_in_dollars` fails if the `manual`
   side's `usd.median` is 0 or its `tokens.n` is 0 when its changes recorded tokens.
7. **R7. Escape rate by way.** `bugs.escapes` rows gain `way`, the introducing change's way, or
   `unknown` when history doesn't hold that change. `bugs.rate.window` gains `by_way`, which gives
   each way `{escapes, changes, rate}` by the same rule as the window's rate: bugs reported in the
   window and tied to a change, divided by that way's changes closed in the window. `rate` is
   null when `changes` is 0. `by_way.escapes` is a copy of it. The `escapes` across ways sum to
   `rate.window.escapes`, and the test `test_escape_rate_is_split_by_the_introducing_change_s_way`
   fails if they don't.
8. **R8. The report shows the comparison.** `render_report()` takes `by_way`. When given, the
   `{{window}}` text ends, after the value sentences, with a *By way of building* table:
   - rows for changes, median lead, 85th percentile lead, closed per week, median tokens, median
     dollars and escape rate;
   - columns *Factory*, *By hand* and *Unknown*;
   - every figure followed by its `n` in brackets, and `–` where it is null.

   The throughput table gains *Ways* and *Classes* columns, written like *Tiers* (zero counts
   left out). No template gains a placeholder. The test
   `test_the_report_compares_the_ways_of_building` fails if the table is missing or a null figure
   prints as `0`.
9. **R9. A retired grouped seed reads `dropped`.** `_milestone_verdicts()` gives a grouped seed
   the verdict `dropped` when all three of these hold:
   - no closed change ships it;
   - the register no longer holds it;
   - a first-parent `Retire` subject on the base branch retired an entry the seed names. The
     match uses `ref_matches()` against that entry as the register held it just before the
     `Retire` commit, so a seed grouped by its quoted title matches too.

   A seed gone with none of these still reads `vanished`. The test
   `test_a_grouped_seed_retired_by_inbox_commit_reads_dropped` covers one seed grouped by id and
   one by title. It fails if either reads `vanished`.
10. **R10. One reader of `Retire` subjects.** `sdlc.py` gains `retired_entries(home, trunk,
    since=None)`, which returns the entries each `Retire` part of a first-parent subject names
    (`File a; Retire b, c`), each with its `id` and, when the register before that commit held
    it, its `title`. `retro.py`'s `_retired_ids()` is removed, and `_seed_follow()` reads the ids
    from this function instead. The existing
    `test_follow_through_scores_the_last_retrospective_s_seeds` must still pass unchanged.
11. **R11. A milestone's verdict counts dropped rows as finished.** In `_milestone_follow()`, when
    every grouped row is `closed`, `shipped` or `dropped`, the milestone is `done` if at least one
    row is `closed` or `shipped`, and `dropped` if every row is `dropped`. `status` counts a
    milestone as done when every row is `closed`, `shipped`, `dropped` or `vanished`, so a
    milestone it called done before is still done. The test
    `test_a_milestone_whose_grouped_seeds_were_retired_follows_through_as_dropped` fails if such a
    milestone reads `carried`. The test `test_status_counts_a_milestone_with_a_retired_seed_done`
    fails if `status` stops calling it done.
12. **R12. Nit 2026-11-19-15: setup's record is not skipped.** `_is_process()` stops skipping
    `.sdlc/setup.json`, so the file counts like any other `.sdlc/` path. The skip set keeps only
    the register. The docstring and `docs/REFERENCE.md`'s *Retrospectives* say so. The test
    `test_a_change_touching_only_setup_s_record_is_process_work` closes a change whose only path
    outside its own folder is `.sdlc/setup.json`. It fails if that change is not classed
    `process`.
13. **R13. The docs say what is now true.**
    - `docs/REFERENCE.md` *Retrospectives* describes `by_way`, `process.lead.ways`, throughput's
      `ways` and `classes`, `bugs.escapes[].way`, `rate.window.by_way`, the `dropped` grouped seed
      and the milestone rule.
    - `docs/RETRO-SCORECARD.md` marks *Supporting: throughput* captured (by way, S9; by work
      class, 176), *Guardrail: escape rate, factory against by hand* captured (S9, 176), and S9
      done in wave 3.
    - `skills/retro/SKILL.md`'s `direction.milestones` line names `dropped`, and the skill
      describes `by_way`.

    The checks are review and a grep of each name the diff touches. `./check.sh` must stay green.

## Design

**The way.** A small helper in `retro.py`, `_way(c) -> str`, returns `metrics.mode` when it is
`factory` or `manual`, and `unknown` otherwise. `WAYS = ("factory", "manual", "unknown")` gives
the order everywhere. `process_views()`'s `mode()` and `window.factory` / `mode_unknown` stay as
they are, since they already mean the same thing.

**Lead (R2).** `lead_view()` already groups by `(tier, way)`. It also groups by way alone over
the same `led` list into `ways`, using the same `_p85()` and `statistics.median`. The `unknown`
key replaces the current `"unknown"` string fallback. Nothing else in the per-tier rows changes.

**Throughput (R3, R4).** In `process_views()`'s week loop, each week's `Counter` becomes three
counters: tiers (as now), `_way(c)`, and `(c.get("work") or {}).get("class") or "unclassed"`.
Rows are written with every way and class key present. `retro_report()` moves its `value =
value_band(...)` call above `process_views(...)`; that move is all R4 needs. `process_views()` is
also called directly by tests with no `work`, which then counts every change as `unclassed`. That
is the right answer for a record nobody classed.

**Cost (R6).** `_cost()` keeps its output, and its loop also keeps each landed change's
`(rec, usd)` in a list. `_cost()` returns that list under a private key, `_landed`, which
`by_way()` reads and `retro()` pops before returning. That way the dollars are summed once, by
the code that already owns them. Tokens come from `metrics.totals`, the same keys `COMPARED`
names (`in`, `cache_read`, `out`), counted only for `_minutes_measured(c)` changes. A
`history_summary()` change has no token keys and lands under `missing_because` with its `none:`
reason.

**Escapes (R7).** In `bugs_retro()`, after `escapes` is built, each row gets
`way = _way(history[name])` if `name in history`, else `unknown`. For the rate, the `attributed`
list keeps `(reported, introduced_by)` pairs instead of bare dates. `window_rate()` gets an
optional way filter, and the introducer is resolved with `names_change()` against `history`, as
the escapes loop does. The per-way denominator is the window's `changes` with that `_way()`. The
previous window's rate and the trend are unchanged; by-way trends are not in this change.

**`by_way()` (R5).** This is a pure function,
`by_way(changes, lead, cost_landed, bugs, since, today)`, with no git and no `sdlc` call. It
assembles `changes`, `lead` (from `lead["ways"]`), `throughput` (counting `_way()` itself), `cost`
and `escapes` (from `bugs["rate"]["window"]["by_way"]`). `retro()` adds `"by_way": by_way(...)`.
`retro_report()` computes it the same way and passes it to `render_report()`.

**Report (R8).** A new `_by_way_text(by_way)` renders the one table through `_table()`. It is
appended in `render_report()` after `_value_text()`, inside `values["window"]`, so `templates/retro.md`
and `TEMPLATE_READS` are untouched and a host's overridden template gets it where it already
shows the window. The throughput table's two new columns use the *Tiers* formatter.

**Retired seeds (R9–R11).**
- `retired_entries()` runs one `git log --first-parent --format=%H%x00%s <span>` and keeps only
  the subjects with a `Retire ` part. For each such commit it reads the register once at `<sha>^`
  through `parse_entries()`, then returns `[{id, title}]`.
- `_milestone_verdicts()` calls it only when a grouped seed is neither shipped nor in the
  register, so `status` pays for the walk only when a grouped seed has gone, and only once per
  call.
- The order is: `shipped`, then `open`, then `dropped` (`ref_matches(seed, entry)` against a
  retired entry), then `vanished`.
- `_seed_follow()` builds its id set as `{e["id"] for e in retired_entries(home, trunk,
  since["sha"])}`.
- `_milestone_follow()` adds the rule from R11 before its `carried` fallback.
- `status`'s done check adds `dropped` to its tuple.

**Setup's record (R12).** Remove `sdlc.MANIFEST` from `_is_process()`'s `skip`. A change that
edits `defaults/` or `guide/` also rewrites `.sdlc/setup.json`, but it touches a path outside
`.sdlc/` too, so it was never `process`, with or without the skip. The skip only ever changed a
change whose sole edit was setup's record, and that is setup work, which is process.

**Edge cases.**
- A window with no factory change gives `factory` zeros and nulls, with its `n` of 0, never a
  missing key.
- An escape whose introducer was closed in an earlier window still counts in the window it was
  reported in, as the current rate does. Its way comes from that earlier change's record.
- A seed retired, then filed again under a new id, is a different seed.

## Contracts touched

- **`Sdlc-Mode` and the metrics trailer contract** (`scripts/metrics.py`'s docstring: extend,
  never redefine). This change only reads `mode`, and adds no trailer and no event. The way is
  whatever close recorded, so a factory-built change shipped by hand from its worktree is
  `factory`, because its `decision.md` is on the tip. A change whose factory run never reached a
  decision is `manual`.
- **Retrospectives are read-only but for the report** (`retro()`). Every new figure comes from
  history and records already read. `retired_entries()` only runs `git log` and `git show` through
  `sdlc._git()`, which is UTF-8 and has no `shell=True`.
- **Modules loaded by path.** `retro.py` reaches the new `retired_entries()` as
  `sdlc.retired_entries`. `factory_records.py` is unchanged, and no core file outside it names a
  run's record (`tests/test_modules.py`).
- **`direction.milestones`' meaning changes.** This is the change idea 2026-11-19-14 asked for, and
  the intent is its approval. A grouped seed gains a fourth verdict, `dropped`, and a milestone can
  now follow through as `done` or `dropped` by its grouped rows. `status`'s "done" list keeps
  every milestone it named before. Anything that read `direction.milestones` and treated a retired
  seed as `vanished` (the retro skill's step 7 wording) is updated in the same change.
- **Templates.** No template heading or placeholder is added, so `TEMPLATE_READS` and
  `breaking` are untouched.
- **Release, publish and measuring never read the register.** `retired_entries()` reads the
  register's history for the retrospective and `status` only. Neither is release, publish nor
  measuring (`test_release_publish_and_measuring_never_read_the_register` keeps passing).
- **Nothing about a project.** Test data uses neutral examples (`reopen-drafts`, `draft-sync`).
- **The review doc's classes.** "A doc's claim the change made false": R13 greps every name
  touched. "A path compared as text": R12 only removes a comparison.

## Alternatives rejected

- **Guess the way for a change with no `Sdlc-Mode`**, from a `runs/` folder or `decision.md` in
  its commit. The intent forbids guessing, and two records of one fact would disagree on old
  changes. Such a change is `unknown`, shown with its `n`.
- **Compare cost in dollars only**, with the hand side missing. That would never compare
  anything, because hand-built changes have no dollars. Tokens are measured on both sides by the
  same code, so they are the comparison, and dollars stay beside them for the factory.
- **Make a factory change's dollars into tokens, or price a hand-built change's tokens.** That
  invents a price list the plugin would then have to keep current.
- **A new `{{by_way}}` template placeholder and section.** A host's overridden `retro.md` would
  never show it, and adding it would make a template read that `drift` would have to propose. The
  comparison goes in the window text, which every template has. S14's scorecard will lay it out
  properly.
- **A by-way trend against the last window.** The intent asks for the comparison, not its trend,
  and with both sides split the samples are too small for a trend to mean much yet.
- **Keep `.sdlc/setup.json` skipped and only document it.** `docs/REFERENCE.md` already says so,
  but the skip only ever reclassifies a setup-only change away from `process`, which is wrong. It
  is less code to drop.
- **Teach `_milestone_verdicts()` about a seed retired in a `Close` commit** (a change's
  `entries.md` `Retire` lines). Only nits are retired that way, and milestones group ideas. It can
  be added if a grouped nit ever needs it.

## Verification

```bash
uv run --group dev pytest tests/test_retro.py -q -n auto
uv run --group dev pytest tests/test_retro.py -q -k "by_way or way or retired or setup_s_record or work_class"
./check.sh
uv run --quiet --script scripts/sdlc.py retro | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps(d["by_way"], indent=1)); print(d["process"]["throughput"][-1])'
```

Healthy output:

- Every test passes, including the 168 tests for follow-through and work mix, unchanged.
- `./check.sh` ends green: ruff, format, pytest and `claude plugin validate --strict`.
- On this repo, `by_way` shows `factory`, `manual` and `unknown`, each with `changes`, `lead`,
  `throughput`, `cost` and `escapes`. `manual.cost.usd` is `{"n": 0, "median": null}` with
  `built by hand` under its `missing_because`, and `manual.cost.tokens.n` is above 0.
- The last throughput row's `ways` and `classes` each sum to its `total`.
- `grep -n "vanished" skills/retro/SKILL.md docs/REFERENCE.md` shows every mention next to the new
  `dropped`.

**Boundaries.**
- **Always:** read the way from `Sdlc-Mode` alone; give every figure with its `n`; leave a figure
  null, never 0, when it has nothing to divide; keep `retro` read-only.
- **Ask first:** any change to how close decides `Sdlc-Mode`; any by-way trend or threshold that
  would flag a side; touching `templates/retro.md`.
- **Never:** write a trailer, price tokens in dollars, or read the register from release, publish
  or measuring.

