---
id: 066
slug: retro-report
kind: plan
created: 2026-11-16
updated: 2026-11-16
---

# 066 — A retro report and process views from each change's numbers · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it.

## Context

Close records every change's numbers as `Sdlc-*` trailers, but nothing turns them into something a
person reads: retro's `metrics` medians feed the skill and vanish into the conversation. Spec R1–R8:
a `process` block in `retro`'s JSON (cycle time, throughput, waiting vs agent time, WIP, capacity,
rework, escapes), rendered by the script into `.sdlc/retros/<date>.md` from a new
`templates/retro.md`, committed by `retro-commit` itself, previewable with `retro --report`, and
cited by the retro skill's process pass. No velocity figure, no dashboard, unmeasured changes
counted, never zeroed.

## Files to change

- **`scripts/sdlc.py`**
  - `closed_changes()` (~L4713): log format gains `%cI`; each record gets `close_at`.
  - `process_views(changes, dropped, rework, questions, bugs, since, today) -> dict` (new, beside
    `metrics_summary` ~L6097): measured = changes whose `metrics.totals.elapsed` is an int.
    `window`, `cycle` (per tier n / median+max elapsed / median agent / median days_open),
    `throughput` (ISO-week Monday from `close_date`, by tier + total), `time` (per-tier medians
    and window sums of agent/response/away/blocked, `agent_share`), `wip` (spans
    `[close_at − elapsed min, close_at]`; each change's concurrency = max overlap count during its
    span, by sweep; median/max), `capacity` (rows `1`, `2`, `3+`: n, median elapsed/agent/response),
    `rework` (links, changes reworked, per-closed rate, questions), `escapes` (from `bugs_retro`:
    reported, fixed, days_to_fix median, rate, previous rate, trend). The four measured views are
    None when nothing is measured. Reuse `statistics.median` as `metrics_summary` does.
  - `RETROS = "retros"` and `report_rel(home, today)` → `.sdlc/retros/<today>.md`.
  - `render_report(template, process) -> str` (new): each `{{key}}` → a Markdown table, or
    `not measured (N changes unmeasured)`; minutes as `1h 16m` (`_hm()`). `{{since}}`, `{{today}}`.
  - `retro_report(home, cfg, today) -> str` (new): `last_retrospective`, `closed_changes`,
    `dropped_changes`, `_change_rows` for `bases` (as `retro()` does), `_rework`, `bugs_retro`,
    then `process_views` + `render_report` with `template_path(home, "retro.md")`. No evidence,
    indicators, product or prose.
  - `retro()` (~L6392): add `"process": process_views(...)` from its own records and
    `"report": report_rel(...)`.
  - `cmd_retro(root, metrics, report)`: with `--report`, print `retro_report(...)` and nothing else.
    Parser: `p_retro.add_argument("--report", …)`.
  - `cmd_retro_commit()` (~L6789): before the stray check, refuse when the report path exists;
    after all refusals, write `retro_report(home, cfg, today)` (mkdir parents, utf-8,
    `newline="\n"`) and append the path to `changed` for the `add`/`commit`.
  - `DOC_TEMPLATES` gains `"retro.md"` (config's `templates`; `test_defaults` checks config lists
    every template).
- **`templates/retro.md`** (new): `# Retrospective report`, `>` note (what it is, written by
    `retro-commit` from history, figures from `sdlc.py retro`'s `process`), then `## Window`,
    `## Cycle time`, `## Throughput`, `## Time`, `## Work in progress and capacity`, `## Rework`,
    `## Escapes`, each holding its placeholder. No `<…>` prompts, no `---`.
- **`skills/retro/SKILL.md`**: Step 0 bullets for `process` and `report`; Step 2 process pass cites
  `process` figures (cycle, agent share, capacity) with the n behind each; Step 5 question gains
  `, with the report at <report>,` before `then commit`; Step 6 says `retro-commit` writes the
  report itself; Step 7 gives its path. Keep one WAIT; frontmatter description unchanged in YAML
  terms (no `: `).
- **Docs**: `docs/REFERENCE.md` retro paragraph (~L715); `AGENTS.md` retrospectives paragraph.
- **Tests**
  - `tests/test_retro.py`: fixture with `_close(..., trailers=("Sdlc-Totals: elapsed=… agent=…
    response=… away=… blocked=…",))` at chosen times (the helper's `when` sets the close time;
    give overlapping/non-overlapping changes via `closed` dates and elapsed): asserts `cycle`,
    `throughput`, `time.agent_share`, `wip`, `capacity` sums, `rework`, `escapes` (R1); an
    unmeasured change counted in `window`/`throughput` but not `cycle`; all-unmeasured → None and
    "not measured" (R2); no `velocity`/`score` in template or render (R3); `--report` equals
    `process` figures and leaves no `{{` (R5); `retro-commit` commits `.sdlc/retros/<day>.md` and
    a refused run writes none; an existing report path is refused (R6).
  - `tests/test_defaults.py`: shape passes by glob; add `templates/retro.md` to whatever
    per-file note map needs it.
  - `tests/test_skills.py`: retro text for R7.

## Work order

1. `close_at` + `process_views` + tests. 2. template + `render_report` + `retro_report` +
`--report` + tests. 3. `retro-commit` writes it + tests. 4. Skill + docs + skill test.
5. `./check.sh`; `notes.md` with this repo's `process` figures.

## Verification

- `uv run --group dev pytest -q tests/test_retro.py tests/test_skills.py tests/test_defaults.py`
- `uv run --quiet --script scripts/sdlc.py retro | jq .process` — 24 measured, capacity n sums to 24.
- `uv run --quiet --script scripts/sdlc.py retro --report` — Markdown, no `{{`.
- `./check.sh` exit 0.
