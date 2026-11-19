---
id: 184
slug: scorecard-report
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 184 — The retrospective report opens with the scorecard · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: 2026-11-19-35, 2026-11-19-42, 2026-11-19-43, 2026-11-19-53, 2026-11-19-60

The page (S14, idea 2026-11-18-105):

1. **R1.** `templates/retro.md` has these `##` sections, in this order, each holding its one placeholder: `Window` (`{{window}}`), `Scorecard` (`{{scorecard}}`), `Speed` (`{{speed}}`), `Quality` (`{{quality}}`), `Indicators` (`{{indicators}}`), `Autonomy` (`{{autonomy}}`), `Cost` (`{{cost}}`), `Spend` (`{{spend}}`), `Simplicity` (`{{simplicity}}`). `tests/test_defaults.py`'s shape tests pass on it. A new test in `tests/test_retro.py` fails if a rendered report's `##` headings come in any other order, or if the report still holds a `{{` from the template.
2. **R2.** `## Scorecard` holds three parts, in this order: the Value band, then the pillar table, then the Trust band. The Value band is `value_band()`'s three sentences (`_value_text()`, unchanged). The pillar table sits under its header line `SCORECARD_HEAD`. The Trust band is the coverage lines and the *What changed underneath* line (`_coverage_lines()`, unchanged), then one line naming the `unmeasured` signals. When the template holds `{{scorecard}}`, `{{window}}` is the window's sentence alone. A test fails if a rendered report's Value band, coverage lines or *By way of building* table show up in `## Window` as well as in their new place.
3. **R3.** The pillar table's rows are exactly the ones listed under *Design → The pillar table*, built by one pure function, `scorecard()`. In a host the surface-share row is left out. A test fails if `scorecard()` returns any other `(pillar, role, figure)` list for a host fixture or for an own-repo fixture.
4. **R4.** `retro()`'s JSON gains `scorecard`, holding `rows` (each with `pillar`, `role`, `figure`, `unit`, `value`, `n`, `last`, `trend`, `note`) and `since`. The report's table is rendered from those same rows. A test reads a rendered report's table back with the shared reader (R7) and fails if any `value` or `n` differs from `retro()["scorecard"]["rows"]` on the same fixture.
5. **R5.** When a row's figure is null, its Value cell is `—` and its Note gives the reason. The reason is the source block's `missing_because` reason with the largest count, or `none in the window` where the block has no such reason. It is never shown as `0`. A test with a window holding no factory change fails if `Median lead time, factory` reads anything but `—`, or if its Note is empty.
6. **R6.** When a row's source block carries `coverage.greyed`, its Note reads `a hint: under half the changes`. A test fails if a greyed lead time is missing that note.
7. **R7.** Each row's `last` is the same `(pillar, figure)` row's value in the last retrospective's committed report. It is read from that report's table with `indicators.report_rows()`, generalised over its header and key columns so that one parser reads both tables. The exception is `Escape rate`, which takes `process.escapes.previous` and `trend` as they are now. `trend` is `up`, `down` or `flat` from `value` against `last`. It is `unknown` when there is no `last`, or when either side's `n` is under `RATE_MIN_CHANGES`. Tests in `tests/test_retro.py` fail on any of these: a second retrospective's rows don't carry the first's values as `last`; a first retrospective's rows have a `last` other than null or a `trend` other than `unknown`; a row with `n` 4 gets a trend.
8. **R8.** Each pillar section renders figures `retro` already computes, as listed under *Design → The pillar sections*. That includes `autonomy`, `pipeline` and `cost`, which the report doesn't show today. A test fails if `## Autonomy` lacks the escalations line, if `## Speed` lacks the landing's gates, ejections, bisections, base moves and accept stops, or if `## Cost` lacks the waste share.
9. **R9.** `## Simplicity` in a host holds `simplicity.workarounds` alone: `outside`, `hand_record` and `restored` with their rows, and `overrides`. In the plugin's own repo (`sdlc._own_repo()`), `surface`'s share, retire candidates, footprint and growth follow. One test fails if a host report names `surface`, `footprint` or `growth`. Another fails if the own-repo report leaves them out.

Hosts' overrides:

10. **R10.** An override of the template without `{{scorecard}}` still renders, as it does today. `{{window}}` keeps the Value band, the coverage lines and the *By way of building* table. Every placeholder the template had before this change (`since`, `today`, `window`, `cycle`, `throughput`, `time`, `capacity`, `rework`, `escapes`, `spend`, `indicators`) is still filled. A test renders the template as it stood before this change, kept in the test as a string, and fails if any of those placeholders is left in it or if `{{window}}` loses those three parts.
11. **R11.** `TEMPLATE_READS["retro.md"]` adds the `Scorecard` heading and the `{{scorecard}}` placeholder to the entries it has now. The next retrospective reads the scorecard table back, so an override without them is misread. `sdlc.py drift` therefore lists such an override under `breaking`. A test fails if `_template_misses("retro.md", <the pre-change template>)` doesn't name exactly those two. The two existing tests that slice the template at `## Spend` and `## Indicators` are updated to the new order.

One computation (nit 2026-11-19-35):

12. **R12.** `retro()` and `retro_report()` both get the report's figures from one function, `report_figures()`. Those figures are process, value, metrics, cost, by way, autonomy, pipeline, workarounds, spend, scorecard, and surface where it is shown. A test wraps `sdlc.retro._cost` in a counting stand-in. It fails if `_cost` runs more than once in either `retro()` or `retro_report()`, or if `_cost` is called anywhere but `report_figures()`.

The three seeds:

13. **R13.** Seed 2026-11-19-59: when the window spans fewer than 7 days, `by_way.throughput[way].per_week` is null. In that case it carries `why: "window under a week"`, still gives its `closed` and `weeks`, and the report's cell reads `–`. A test fails if a retrospective one day after the last gives a number there. The existing 3-week assertion keeps its numbers, plus `why: None`.
14. **R14.** Seed 2026-11-19-54: `skills/retro/SKILL.md`'s Step 0 lists `scorecard`. Its process pass in Step 2 reads `simplicity.workarounds`: when an `outside` or `restored` row recurs, or one stands out, it becomes a seed naming what the process lacked. A `hand_record` row is a question about which record needed fixing. The skill keeps every `tests/test_skills.py` invariant: no new command and no new `allowed-tools` rule. A test fails if Step 2 doesn't name `simplicity.workarounds`.
15. **R15.** Seed 2026-11-19-39: `indicators.host_rows()` rejects a row whose `unit` is `—`, or whose `name` or `unit` has leading or trailing whitespace, as `(None, "line N's name has stray spaces")` or the equivalent for `unit`. A test in `tests/test_indicators.py` fails if any of the three is accepted.

The five nits:

16. **R16.** Nit 2026-11-19-42: `_surface_at()` gets a comment saying that `commands` is None at a tag from before the `@command` registry only because `core` is empty there. A test in `tests/test_surface.py` fails if such a tag gives `commands` other than None.
17. **R17.** Nit 2026-11-19-43: `_retire()`'s docstring and REFERENCE.md's `retire` sentence say that `windows` counts the windows actually read. It can be below `RETIRE_AFTER` when every item was decided early, and no candidate is hidden then. `tests/test_surface.py`'s existing `windows == 2` with no items stays as the pin.
18. **R18.** Nit 2026-11-19-53: `pipeline.landing.bisections` and `accept_stops` each gain `per_change`, which is `_share(total, n)` and null when `n` is 0. A test fails if either is missing.
19. **R19.** Nit 2026-11-19-60: `bugs_retro()` works out each distinct `Introduced by:` value's way once, in a dict built before the rate is counted, so the rate stops rescanning `history` for every bug and every way. A test with three bugs from one change wraps `sdlc.names_change` in a counting stand-in. It fails if the call count grows with the number of bugs or ways. The existing by-way escape tests keep their numbers.

Docs and setup:

20. **R20.** The docs say what the report now does:
    - REFERENCE.md's *Retrospectives* describes `scorecard` and the report's layout, and names `## Scorecard` and `{{scorecard}}` in the override sentence. It drops "The report doesn't show these yet" (twice) and "the figures themselves aren't in its body yet".
    - `docs/RETRO-SCORECARD.md` marks S14 done (184) and updates the Outcomes-moved status line.
    - This is checked by the review, and by the `grep` under Verification returning nothing.
21. **R21.** `scripts/sdlc.py record` is run from this change's checkout, so `.sdlc/setup.json` records the new template. `sdlc.py drift` reports nothing in this repo.

## Design

**Assumptions checked in the code.**
- The report and the JSON are built today by two parallel paths: `retro()` (`scripts/retro.py:2762`) and `retro_report()` (`:2052`). Each calls `_cost`, `value_band`, `process_views`, `bugs_retro` and `by_way` itself.
- `render_report()` replaces only the `{{key}}`s it knows, so a placeholder it doesn't fill stays in the report as literal text.
- `indicators.report_rows()` reads a past report's table by its exact header line, never by its heading.
- `drift` puts what `_template_misses()` finds under `breaking`. A template whose plugin copy changed shows up only as a `changed` note.
- This repo has no `.sdlc/templates/` override.
- `sdlc._own_repo()` is how the code tells the plugin's own repo from a host.

**`report_figures(home, cfg, today, *, surface: bool)`.** This is new in `scripts/retro.py`. It computes once what both callers need:
- `changes`, `dropped`, `bases`, `paths` and `diffs`;
- rework, `bugs_retro`, `value_band` (still before `process_views`, so each change's `work` is set), `process_views`, `metrics_summary`, `_cost` (popping `_landed`), `by_way`, `_autonomy`, `_pipeline`, `_workarounds` and `_spend`;
- `surface()` only when asked;
- the scorecard (below).

`retro()` asks for `surface=True` and adds its other parts on top: the product pass, architecture, prose, tests and the register. `retro_report()` asks for `surface=_own_repo(home)`, adds `_indicator_rows()`, and renders the report. Both commands still run in separate processes, so `retro` and then `retro-commit` read each change's commit once each. What ends is the second call site, and with it any chance that the report and the JSON disagree.

**The pillar table.** The header is `| Pillar | Role | Figure | Unit | Value | n | Last retrospective | Trend | Note |`. Rows come in this order. Each takes its value and `n` from a block already in the JSON. No pooled figure is computed, so a headline the JSON gives only per way or per tier gets one row per way or tier present.

| Pillar | Role | Figure | Unit | From |
|---|---|---|---|---|
| Speed | headline | Median lead time, factory / by hand | minutes | `process.lead.ways[way]` (`median`, `n`) |
| Speed | guardrail | Rework links per closed change | per change | `process.rework.per_change`, `n` = `window.closed` |
| Quality | headline | Escape rate | per change | `process.escapes.rate`, its `previous` and `trend` |
| Autonomy | headline | Median response, tier N | minutes | `process.time.tiers[N].response`, `n` = `process.cycle[N].n` |
| Autonomy | headline | Questions answered per factory change | per change | `autonomy.asked` |
| Autonomy | guardrail | Escape rate, factory / by hand | per change | `by_way.escapes[way]` |
| Cost | headline | Median dollars per landed change, tier N | USD | `cost.per_change[N].usd.median`; one `—` row with the reason when there's no tier |
| Simplicity | headline | Share of the surface used | share | `surface.share.overall`, own repo only |
| Simplicity | headline | Commits outside the loop / Records edited by hand / Register entries restored | commits, entries | `simplicity.workarounds` |

The guardrails that are another pillar's headline get one line under the table rather than rows of their own: "Quality and Simplicity are guarded by Speed's lead time, and Cost by Quality's escape rate." The structural debt index stays in `## Indicators`: it is the host's, in its own language, and core never computes it. Outcomes moved are scored by the product pass in the direction doc, not by the script, so the Value band says that in one line and the report holds nothing the skill wrote.

**Last and trend.** `_last_rows()` already reads the last retrospective's report from its own commit. It now passes the text to the generalised `report_rows(text, head, keys)` twice: once for the indicator table (keys Indicator and Unit, as now) and once for the scorecard (keys Pillar and Figure). A Value cell holds a plain number, as the indicator table's do, so it reads back. Minutes are written as integers, with the `Unit` column saying `minutes`. A first scorecard, or a report written from an old override, gives `last` null and `trend` `unknown` everywhere except the escape rate.

**The pillar sections.** Each is built from existing renderers wherever there is one.
- **Speed:** `_lead_text` with the cycle table; the throughput, time and capacity tables; `_by_way_text`; then `pipeline.gates` (window against previous) and `pipeline.landing` (gates, ejections by cause, bisections, base moves, accept stops, conflicts), each with its `n`.
- **Quality:** the escapes table with `_sources_text`, the rework table, `pipeline.red_gate`, `depth` and `unreviewed`.
- **Autonomy:** `autonomy`'s escalations, asked, kept default, auto-landed, spurious stops and looks, then `metrics.extra`'s kinds.
- **Cost:** `cost.per_change` by tier (dollars and agent-minutes), `waste` with its parts, `by_role` and `by_model`.
- **Simplicity:** see R9.

Each figure carries its `n` and reads `—` with its reason when null. The old placeholders' values come from the same helpers, so `{{cycle}}` in an old override and the cycle part of `{{speed}}` are always the same text.

**Window when `{{scorecard}}` is absent.** `render_report()` checks whether the template holds `{{scorecard}}`. If it does, `{{window}}` is the bare sentence. If not, `{{window}}` is what it is today. Either way each figure appears once.

**Edge cases.**
- No change closed: the table's rows all read `—` with `none in the window`, and the Trust band gives its existing empty form.
- No factory change: factory rows read `—`, and the Speed and Quality pipeline parts say `No factory changes in this window.` (`_no_factory_text()`).
- A window under a week: R13.
- A host with no `setup.json`: Simplicity doesn't show the footprint, as R9 says.

**Boundaries.**
- **Always:** every figure comes from the script, null figures read `—` with their reason, and every old placeholder is still filled.
- **Ask first:** making the pillar placeholders breaking in `drift`, adding pooled medians, or adding any new figure.
- **Never:** run `retro.evidence` or `retro.test_times` from the report, write prose the skill drafted into the report, or build the Insights section or its guide file (S15) or the experience rating (S16).

## Contracts touched

- **`breaking` is only what the plugin would now misread (AGENTS.md, *Setup*).** Only `{{scorecard}}` and its heading are read back, so only they go into `TEMPLATE_READS`, in this same change. The pillar placeholders are optional, as `{{cycle}}` is today. An override without them loses those sections, and `drift`'s existing `changed` note says the plugin's `retro.md` changed. The constraint "drift says what it lacks" is met in `breaking` for what is read back, and in that note for the rest.
- **`templates/` is `[review] irreversible`.** The template change gets the deep review. A host that copied the old template keeps rendering it (R10). `sdlc.py record` runs from this checkout (R21).
- **One shape for the shipped docs (`tests/test_defaults.py`).** The template keeps one `# ` title and its `>` note, which is reworded to name the scorecard, then `##` sections only, with no `---` rule.
- **Retrospectives: read-only but for its report, and only `retro.indicators` runs from it.** `report_figures()` adds only git reads to `retro-commit` (`_autonomy`, `_pipeline`, `_workarounds`, and `surface` in the own repo) and runs no further host command.
- **Modules loaded by path.** `retro.py` keeps calling shared code as `sdlc.<name>`, so the counting stand-ins in R12 and R19 reach it. `indicators.py` stays pure: the generalised `report_rows()` takes text and returns rows, with no git.
- **Windows (`tests/test_windows.py`).** No new write and no new subprocess. `retro-commit` already writes the report with `newline="\n"`.
- **Skills (`tests/test_skills.py`).** R14 changes prose in Steps 0 and 2 of the retro skill only: no new bash block, rule or WAIT.
- **A doc's claim the change made false (`.sdlc/REVIEW.md`).** R20 names the three REFERENCE.md sentences this change makes false.
- **Metrics' trailer contract.** Untouched: nothing new is recorded at close.

No invariant needs to move.

## Alternatives rejected

- **Work out `last` by re-running the figures over the previous window.** That would double every git read in `retro-commit`: `_cost`, `_autonomy` and `_pipeline` all walk each change's commit. It would also give the first scorecard a "last" the person never saw. Reading the last committed report back is the pattern the indicators already use, and its numbers are the ones a person read then.
- **Pooled medians, one row per pillar.** Cleaner on the page, but they are new figures, which the intent's first constraint rules out. Left as an open question.
- **Make every pillar placeholder breaking in `drift`.** Every host with an override would be told its report is misread, when it isn't: a missing pillar section is just not shown.
- **Only new placeholders added inside the current layout.** That would leave the report opening with *Cycle time*, the wall of tables S14 exists to replace. Without the scorecard placeholder, an override doesn't get the new layout, and R10 keeps it rendering as before.
- **Render the report from `retro()`'s whole output.** That would run the product pass's `retro.evidence` and `retro.test_times`, which runs the suite, inside `retro-commit`.
- **Floor `by_way` throughput at one week (seed 2026-11-19-59's other option).** A 3-day window with 10 changes would read 10 a week against a real rate of about 23. A null with its reason follows the rule for missing data.
- **The synthesis-questions guide file.** It is S15, wave 5, and comes after this change.

## Verification

```bash
./check.sh
uv run --group dev pytest -q tests/test_retro.py tests/test_indicators.py tests/test_surface.py tests/test_skills.py tests/test_defaults.py
uv run --quiet --script scripts/sdlc.py retro --report | head -60
uv run --quiet --script scripts/sdlc.py retro | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d["scorecard"]["rows"]), d["by_way"]["throughput"]["factory"], d["pipeline"]["landing"]["bisections"])'
uv run --quiet --script scripts/sdlc.py drift
grep -n "doesn't show these yet\|aren't in its body yet" docs/REFERENCE.md
```

What a healthy run looks like:
- `check.sh` ends green: ruff, the format check, pytest and `claude plugin validate --strict` all pass.
- The report opens with `## Window`, a single sentence, and then `## Scorecard`: the work-mix, time-to-users and follow-through sentences, the pillar table with numbers, `n`, `—` where null, and `unknown` trends (this repo has no scorecard from before), then the coverage and underneath lines.
- After that come `## Speed` through `## Simplicity`. Simplicity shows the surface share, because this is the plugin's own repo.
- The JSON line prints a row count, `per_week: null` with `why` if the window is under a week, and `bisections` with a `per_change`.
- `drift` shows `"breaking": []` and no template report.
- The `grep` prints nothing.

