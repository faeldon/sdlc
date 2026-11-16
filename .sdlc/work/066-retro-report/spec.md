---
id: 066
slug: retro-report
kind: spec
created: 2026-11-16
updated: 2026-11-16
---

# 066 — A retro report and process views from each change's numbers · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. R1. `sdlc.py retro`'s JSON gains `process`, from the window's closed changes, and `report`, the
   path `retro-commit` will write:
   - `window`: since, today, closed by tier, dropped, `measured`, `unmeasured`;
   - `cycle`: per tier, `n`, median and max `elapsed`, median `agent`, median `days_open`;
   - `throughput`: per ISO week (its Monday's date), closed by tier and total;
   - `time`: per tier, median `agent`, `response`, `away`, `blocked`; over the window, the sum of
     each and the agent share (agent ÷ (agent + response + away));
   - `wip`: each measured change's span, [close time − `elapsed`, close time], and its
     concurrency (the most window changes whose spans overlapped any moment of it, itself
     included); the median and max concurrency;
   - `capacity`: rows for concurrency `1`, `2` and `3+`, each `n` and median `elapsed`, `agent`,
     `response`;
   - `rework`: declared links (060's `rework`), the changes reworked, links per closed change, and
     `rework_questions`' count;
   - `escapes`: from `bugs`: reported, fixed, median days to fix, and the escape rate this window
     and last with its trend.

   A test builds a fixture history with known trailers and asserts each figure.
2. R2. A change without `Sdlc-Totals` (`Sdlc-Coverage: none`) counts in `window`, `throughput`,
   `rework` and `escapes`, and stays out of `cycle`, `time`, `wip` and `capacity`, which rest on
   `measured` alone; with none measured those four are null and the report says "not measured" in
   their place. Tested both ways.
3. R3. No single velocity figure: no key or report line combines speed and stability into one
   number. A test asserts neither the template nor a rendered report holds `velocity` or `score`.
4. R4. `templates/retro.md`: `# Retrospective report`, a `>` note saying what the file is and that
   `retro-commit` writes it, then one `##` section per view holding its placeholder (`{{window}}`,
   `{{cycle}}`, …). It passes `tests/test_defaults.py`'s shape. A host's
   `.sdlc/templates/retro.md` is used in its place, and `config`'s `templates` lists `retro.md`.
5. R5. `sdlc.py retro --report` prints the report rendered for the current window as Markdown,
   writes nothing, and never runs `retro.evidence` or `retro.indicators`. A test asserts its
   figures equal `retro`'s `process` from the same fixture.
6. R6. `retro-commit`, only after every existing refusal passes, writes the report at
   `.sdlc/retros/<today>.md`, rendered for the window this commit closes, and commits it with the
   docs as `Retrospective <today>`. It refuses, writing nothing, when that path already exists or
   is changed by hand (the stray check, which the report path never joins). It never runs the
   host's evidence commands. Tested: a successful run holds the report in the commit; a refused
   one leaves none.
7. R7. `skills/retro/SKILL.md`: Step 0 describes `process` and `report`; the process pass cites
   the `process` figures (cycle time, agent share, capacity) for its findings on time, stops and
   load, saying how many changes each rests on; Step 5's question gains `, with the report at
   <report>,` before `then commit`; Step 7 gives the report's path. A `tests/test_skills.py` test
   pins these; the skill keeps one WAIT.
8. R8. `docs/REFERENCE.md`'s retro paragraph (the report, its template, `--report`) and
   `AGENTS.md`'s retrospectives paragraph (`retro-commit` writes the report itself, the one file it
   writes) say so.

## Design

- `process_views(changes, dropped, rework, questions, bugs, since, today)` in `scripts/sdlc.py`
  beside `metrics_summary`: pure over the records `retro()` already builds, returning R1's block.
  `closed_changes` adds `close_at`, the `Close` commit's ISO time (`%cI`, read beside `%cs`), so a
  span can be computed. Concurrency is a sweep over the spans' start and end points.
- `retro_report(home, cfg, today)` gathers the same records without the product pass,
  architecture, prose or evidence (`closed_changes`, `dropped_changes`, `_change_rows` for
  `bases`, `_rework`, `bugs_retro`), calls `process_views`, and renders with
  `render_report(template, process)`. `retro()` calls `process_views` on the records it already
  has, so the JSON and the report come from one function.
- `render_report` replaces each `{{key}}` with a small Markdown table, or one line, "not measured
  (N changes unmeasured)". Minutes show as `1h 16m`.
- `retro-commit` calls `retro_report(home, cfg, today)` before its own commit (`since` is still
  the previous retrospective), writes the file with `newline="\n"` only once `refusals` is empty,
  and adds the path to the `add` and `commit` it already runs. The report path is checked before
  the stray check: it must be absent.
- The skill reads `process` from the `retro` it already runs; it reads no new file.

## Contracts touched

- Metrics trailers are a contract: only read. The `Close` commit's time comes from git (`%cI`),
  not a new trailer.
- `retro-commit` commits only what a retrospective owns: the direction doc, the register and the
  product doc as before, plus the one file it writes itself, never one a person or skill wrote.
  `register_drift` and the follow-through guards are unchanged.
- One shape for shipped docs: the new template passes `tests/test_defaults.py` as written; it is
  not an exception like `issue.md`.
- `templates/` is irreversible: a new template reaches hosts once released. Recover by removing it
  in a later release; a host's override is its own. `TEMPLATE_READS` gets no entry: a host
  template lacking a placeholder drops that view, and nothing is misread.
- `metrics.py` and `indicators.py` stay pure and untouched; the views live in `sdlc.py` beside
  `metrics_summary`.
- 059's lean output: `process` holds aggregates only, no per-change rows.
- "No dashboard": a committed Markdown report, read when wanted.
- Windows: the report is written with `newline="\n"` and `encoding="utf-8"`; the path is compared
  as POSIX.
- "Run from the main checkout on `main`": unchanged; `retro-commit` still refuses elsewhere.

## Alternatives rejected

- The skill writes the report: tokens, and figures that could drift from the script's.
- Inside the direction doc: machine figures among the person's prose, tangled with the id guard.
- `.sdlc/reports/`: ignores itself, so nothing is committed.
- Replacing `metrics`: the skill's passes need its detail (prompts, extra stops, findings).
- A new `Sdlc-Started:` trailer: older changes lack it, and close time minus `elapsed` gives the
  span from what's recorded.
- A dashboard or a combined velocity score: ruled out in the intent.
- 2026-11-12-2's views (verbosity, tool calls, test pruning): their own seed.

## Verification

- `uv run --group dev pytest -q tests/test_retro.py tests/test_skills.py tests/test_defaults.py`
- `uv run --quiet --script scripts/sdlc.py retro | jq .process`: on this repo, 24 measured
  changes, `capacity` rows summing to 24.
- `uv run --quiet --script scripts/sdlc.py retro --report`: the Markdown report, no `{{` left.
- `./check.sh` exits 0.
