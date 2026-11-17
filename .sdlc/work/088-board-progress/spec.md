---
id: 088
slug: board-progress
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 088 — The board shows how far each change has got · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

The step and its start time come from a record the factory's supervisor already has the means to
write (`verdicts --record`, which it runs after every step). This is the first open question
below, and the one the person must settle: every requirement marked † depends on it.

1. † `factory.py verdicts <NNN> --head <h> --record` writes `runs/step.md` with the step it read
   (`STEP:`, `loop_state()`'s `next`), `ROUND:`, `LIMIT:` (the run's `rounds`), `REVIEWERS:` (the
   run's expected reviewers, comma-separated, UI reviewers included when they join) and `SINCE:`
   (UTC, `YYYY-MM-DDTHH:MM:SSZ`). It writes this on every reading, a `stop` included, and
   `stopped.md` keeps doing what it does today. A test fails if `--record` leaves no `step.md`,
   or if any field differs from `verdicts`' own JSON for that reading
   (`test_record_writes_the_step_it_read`, `tests/test_factory.py`).
2. † `SINCE:` is kept while `STEP:` and `ROUND:` are unchanged: a second `--record` naming
   `review` for round 2, with reviewers still missing, keeps the first one's time. It is set anew
   when either changes. A test fails if a repeated reading moves the time, or if a new step keeps
   the old time (`test_the_step_record_keeps_its_since_while_the_step_holds`).
3. † Nothing in the loop reads `runs/step.md`. `loop_state()` returns the same reading with the
   file present, absent or garbled, and `verdicts` without `--record` never writes it. A test
   fails otherwise (`test_the_step_record_never_reaches_the_loop`).
4. A factory card's state gains `progress`: `{"steps": [...], "round", "limit", "step",
   "elapsed", "typical", "fraction", "samples", "plan"}`. `steps` is the six positions `build`,
   `gate`, `review`, `verify`, `rework`, `approve`, each `done`, `current` or `todo`, in the
   current round:
   - The step named by `STEP:` is `current`. Every step before it is `done` and every step after
     it is `todo`.
   - `fix` puts `current` on `gate`, labelled `fixing`.
   - A valid `decision.md` (READY or ESCALATE) makes every step `done` with no current step,
     whatever the record says.
   - `decide` keeps the record's last position, marked `paused`, with no bar.
   - `done` makes every step `done`.
   - A run with a stop record shown (`stopped` set) has `progress: null`.

   A parametrised test over each `next` value fails on any other mapping
   (`test_a_factory_card_shows_its_step_track`, `tests/test_board.py`).
5. The `review` position reads `reviews n/m`. `n` is the number of files in `reviews/round-<ROUND>/`
   that open with a `VERDICT:` line (`verified.md` excluded), counted on every request. `m` is the
   number of names on `REVIEWERS:`. A test fails if `n` doesn't count up as review files land
   while the record stays the same (`test_reviews_count_up_as_they_land`).
6. A run with no `step.md` (the first build, which the supervisor starts before its first
   `verdicts`) whose folder holds `runs/builder.sessions` and no `build/round-*.md` shows `build`
   as `current`, with `SINCE` taken from that file's modification time. A run with neither the
   record nor that file (a Tier 2 whose spec is still being drafted, or a run from a factory
   before this change) has `progress: null`, and its round rows show as today. A test fails on
   either case (`test_a_first_build_runs_from_its_builder_session`,
   `test_a_run_without_a_record_has_no_track`).
7. The board's `STEP_RE`, `ROUND_RE`, `LIMIT_RE`, `REVIEWERS_RE`, `SINCE_RE` and `STEP` path equal
   `factory.py`'s. A record written by `factory.py`'s writer reads back through `board.py`'s
   reader to the same fields. A test fails on either
   (`test_the_step_record_is_a_pinned_copy`, beside `test_the_factory_parsing_is_a_pinned_copy`).
8. `elapsed` is `now − SINCE` in seconds. `typical` is the median seconds for that step at the
   change's tier, from closed factory runs (R9). `fraction` is `min(elapsed / typical, 0.95)`.
   `typical`, `fraction` and `samples` are `null` when fewer than 3 closed changes of that tier
   give a sample for that step. A test fails if `fraction` ever exceeds 0.95, or if a tier with 2
   sampled changes gets a `typical`
   (`test_the_estimate_is_capped_and_absent_without_history`).
9. Typical times come from the newest 20 closed changes whose `Close` commit removed a
   `runs/costs.jsonl`. Each change's own files are read at `Close^`:
   - **tier**: `intent.md`'s `tier:`, read as text.
   - **build**: the first `builder` row's `duration_ms`.
   - **rework**: every later `builder` row before the first `approver` row (`fix` uses this too).
   - **review**: each maximal run of consecutive reviewer-role rows is one round, sampled as the
     largest `duration_ms` in it, since the reviewers run in parallel.
   - **verify**: each `verifier` row before the first `approver` row.
   - **approve**: the first `approver` row.
   - **gate**: every `Seconds:` line of `build/round-*.gate.md`.

   Rows after the first `approver` row are the landing's and are skipped. So are rows without an
   integer `duration_ms`. A test over a built history fails on any other sample set
   (`test_typical_times_come_from_closed_factory_runs`).
10. History is read once per base-branch tip. Each request runs only `git rev-parse
    refs/heads/<trunk>`, and the walk runs again only when the tip moves. A test with a counting
    stand-in for `sdlc._git` fails if two `state()` calls at one tip read history twice, or if a
    new `Close` commit isn't read (`test_history_is_read_once_per_base_branch_tip`).
11. `progress.plan` is `{"named": N, "touched": T}` for a factory change whose `plan.md` is filled
    and whose `## Files to change` section yields at least one path; otherwise it is `null`.
    - **Named paths:** the first backtick-quoted span of each list item in that section (a line
      opening with `-`, `*`, `+` or `1.`; an item's wrapped lines name nothing), else its first
      word, with a trailing `:`, `,` or ` (new)` stripped. It is kept only if it holds a `/` or a
      `.` and no `<` (D1).
    - **Touched paths:** what the branch changed against the base branch, plus, in a worktree of
      its own, its uncommitted edits. This is the reading `_seen()` already makes, moved into a
      shared helper.
    - A named directory (ending `/`) counts as touched when any touched path is under it.

    A test fails on a wrong count, or on a hint shown for a Tier 1 change or an unfilled plan
    (`test_the_plan_hint_counts_named_files_the_branch_touched`).
12. `TEMPLATE_READS` gains `"plan.md": {"headings": ("Files to change",)}`, since the script now
    reads that heading. A test fails if a `.sdlc/templates/plan.md` override without it isn't
    reported by `drift` (`test_an_override_plan_without_files_to_change_is_reported`, beside the
    existing `TEMPLATE_READS` tests).
13. The page draws `progress` under the round rows:
    - the six-step track, with the round as `R<round> of <limit>`;
    - for the current step, a bar of `fraction` labelled `~<typical> typical · estimate (<samples>
      runs)`, or `<elapsed> so far` with no bar when `typical` is null;
    - the plan hint `plan: T of N files touched`.

    Every node goes through `h()`. A change built by hand draws none of it.
    `test_the_page_is_self_contained_and_never_parses_data_as_html` and
    `test_no_column_key_is_a_class_the_page_styles_on_its_own` still pass. A new check fails if
    the page sets a bar width from anything but `progress.fraction`
    (`test_the_bar_is_drawn_from_the_capped_fraction`).
14. The board still writes nothing. `test_the_board_writes_nothing` runs over a fixture holding a
    factory run with a `step.md` and a closed factory change in history, and fails on any
    changed file. A manual card has no `progress` key; the existing
    `test_every_open_change_is_on_the_board_with_its_next_step` assertion that a manual card has
    no factory fields is extended to it.
15. The docs say what a factory card now shows and what `--record` writes:
    - `docs/REFERENCE.md`'s **The board** paragraph;
    - AGENTS.md's *The board* and *The factory* (the `--record` sentence);
    - `factory.py`'s module and `cmd_verdicts` docstrings;
    - `plugins/factory/skills/build/SKILL.md` step 2's `--record` sentence.
16. `./check.sh` passes.

## Design

### Assumptions checked

- **Nothing on disk says a step is running today.** `cmd_agent()`
  (`plugins/factory/scripts/factory.py:1687`) appends a fresh session id to
  `runs/<agent>.sessions` before it runs `claude`. A resumed builder (`fix`, `rework`, `decided`,
  `mend`) appends nothing. `record_cost()` writes a `costs.jsonl` row only when a session ends, and
  a failed one with no figures writes none. So "running since" can't be read reliably from the
  agents' files, and the gate (`cmd_gate`) leaves nothing until it finishes.
- **The supervisor runs `verdicts --record` after every step.** It does so before taking the step
  that reading names (`plugins/factory/skills/build/SKILL.md:216-226`). The first build is the one
  step taken before any `verdicts`. `--record` already writes a file for the board and status
  (`runs/stopped.md`, `factory.py:1002-1010`), and nothing in the loop reads it back.
- **The run's expected reviewers aren't in any file.** `m` in *reviews n/m* depends on `depth()`
  (the base branch's `[review] sensitive`, the diff, `factory.toml`'s `[light]`) and
  `ui_review()`. The board can't reproduce that without copying `factory.py`'s config loading and
  its git calls.
- **The change folder is committed with the branch,** `runs/` included (`_agent_sessions()` reads
  `runs/*.sessions` from the branch, `sdlc.py:3772`). The fast-forward puts it on the base branch,
  and the `Close` commit removes it. So a closed change's `costs.jsonl`, gate files and intent are
  at `Close^`, the same commit `closed_changes()` reads the intent from (`sdlc.py:5078`).
- **`Sdlc-Role:` trailers aren't per step.** They give `runs` and `agent` minutes per agent (the
  builder's build, fixes and reworks summed), and only when transcripts were readable. They are
  not used.
- **`costs.jsonl` rows are in completion order,** with `role` (`builder`, `code`, `security`, …,
  `verifier`, `approver`, `spec-writer`) and the run's own `duration_ms` (`_figures()`).
- **The gate records its own time** as `Seconds:` on each attempt (`factory.py:1301`).
- **Nothing in code reads `plan.md`'s headings today.** `## Files to change` is the template's
  (`templates/plan.md`), so reading it is a new `TEMPLATE_READS` entry.
- **The change folder is outside what the factory hashes.** `_changed_paths()` leaves out the
  change folders (`factory.py:542`), so writing `runs/step.md` never alters a snapshot, a build
  hash or the gate's tree check.

### The factory's side: `runs/step.md`

A new `step_text(out, since)` in `factory.py`, beside `stop_text()`, with the path and regexes as
module constants next to `STOPPED`:

    STEP: review
    ROUND: 2
    LIMIT: 3
    REVIEWERS: code, security, test, behaviour, ui
    SINCE: 2026-11-17T10:42:05Z

`cmd_verdicts(record=True)` writes it after `stopped.md`'s handling, from the same `loop_state()`
reading. If an existing `step.md` holds the same `STEP:` and `ROUND:`, its `SINCE:` is kept.
Otherwise `SINCE:` is now, in UTC. `ROUND:` is `loop_state()`'s `round`, or empty for
`decide`/`done`/`stop`. Nothing else reads or writes the file, and `loop_state()` never opens it.
The first `SINCE:` for a step is within seconds of the step starting, because the supervisor acts
on the reading right after it.

### The board's side

`_factory()` gains a `progress` entry, built by a new `_progress(folder, entry, history, now)`:

1. If `entry["stopped"]` is set, progress is `null` (the stop flags already say it all).
2. A `decision.md` that opens with a valid `DECISION:` line marks all six steps done (READY or
   ESCALATE; the column already reflects which).
3. Otherwise it reads `runs/step.md` with the pinned regexes. If the record is missing, it falls
   back to R6: `runs/builder.sessions` with no builder report means build is current, with
   `os.stat().st_mtime` as the start. If neither the record nor that file exists, progress is
   `null`.
4. It maps `STEP:` onto the six positions (R4) and counts `n` live from
   `reviews/round-<ROUND>/` with the existing `VERDICT_RE`.
5. It looks up `typical` in `history[(step_key, tier)]`, where `step_key` is `rework` for `fix`.
   It computes `elapsed`, and `fraction` capped at 0.95.
6. It adds `plan` (R11). The touched paths come from a helper `_touched(entry, folder, home,
   trunk)` factored out of `_seen()`, which keeps calling it unchanged.

`_factory()` then needs the change's tier, the board's `history` and `now`. `_entry()` already
holds all three (`rec["tier"]`, `now`), and `history` comes from `state()`.

**History, cached.** A module-level `_HISTORY = {"tip": None, "typical": {}}` guarded by a
`threading.Lock` (the server is a `ThreadingHTTPServer`). `state()` calls `typical_times(home,
trunk)`:

- It runs `rev-parse refs/heads/<trunk>`. If the tip matches the cached one, it returns the cache.
- Otherwise it makes one `git log --first-parent --format=%H%x00%s refs/heads/<trunk> --
  '<work_rel>/*/runs/costs.jsonl'` and keeps subjects starting `Close ` whose name passes
  `DIR_RE`, newest first, up to 20.
- For each, it runs `git show Close^:<work>/<name>/intent.md` (tier),
  `.../runs/costs.jsonl`, and `git ls-tree --name-only Close^:<work>/<name>/build` plus a show for
  each `*.gate.md`.
- It builds the samples (R9) and stores `{(step, tier): (median_seconds, changes)}` only where
  `changes >= 3`.

Any git failure gives an empty table, so the card shows elapsed only and never fails.
`statistics.median` is used, as `metrics.py` does. Each path given to git is built from
`sdlc.work_rel(home)`.

**The page.** `card()` gets a `progressRow(c.progress)` after the round rows, built only from
`h()`:

- a `.track` of six chips with classes `done`, `current` and `todo`, which `board.html`'s
  stylesheet defines and no column key shares;
- a `.bar` whose inner width style is `${Math.round(p.fraction * 100)}%`;
- the label text;
- the plan hint in a `.meta` line.

The page computes nothing it can't read from `progress`: no clock of its own, and `elapsed`
refreshes with each poll.

### Edge cases

- **The supervisor died mid-step.** The record stays and `elapsed` grows. The bar stops at 95% and
  the label still says estimate. The board can't tell a dead supervisor from a slow agent, and
  doesn't claim to.
- **A garbled `step.md`.** A `problems` line (`runs/step.md doesn't open with STEP:`), and
  `progress: null`, as `_stopped()` does for its record.
- **Reviews landed after the record.** `n` reaches `m` before the next `verdicts` moves the record
  on, and the track then shows `reviews 4/4` as current. That's true: the supervisor hasn't taken
  the next step yet.
- **A clock moved backwards** (`SINCE` in the future): `elapsed` is clamped to 0.
- **No base branch:** history is empty and the plan hint is `null`, as `_seen()` already behaves.

### Boundaries

- **Always:** derive progress fresh from the folder on each request; label every time from history
  as an estimate; keep the bar under 95% while a step runs.
- **Ask first (open questions below):** the factory writing `runs/step.md`; whether a change built
  by hand gets the plan hint; the window size, the minimum sample count and the statistic.
- **Never:** write a file, cache to disk, start or signal anything, import or run `factory.py`,
  read history on every request, or invent a typical time where none exists. No ETA for the whole
  run: the intent asks about the current step only.

## Contracts touched

- **The board writes nothing and starts nothing** (AGENTS.md, *The board*). The cache lives in the
  board process's memory and dies with it. The only new reads are `step.md`, a file's mtime,
  `plan.md` and git history. R14 runs `test_the_board_writes_nothing` over the new inputs.
- **The board never imports or runs `factory.py`; it reads with copies pinned by tests.** The step
  record's regexes and path are copied and pinned (R7), as `STOPPED_RE` is. The `Seconds:` line
  and the `costs.jsonl` row shape are pinned by building the test's history with `factory.py`'s
  own `record_cost()` and a gate file made by its `cmd_gate` writer in the fixture.
- **What the factory writes: this widens it, so it is the person's decision.** AGENTS.md says of
  `--record` that "it writes the stop it found to `runs/stopped.md` for the board and status, or
  removes it, and nothing reads that back into the loop". This change adds a second file under
  the same rule: written only with `--record`, which only the supervisor passes, read only by the
  board, never by the loop (R3). The AGENTS.md sentence and `cmd_verdicts`' docstring are edited
  to say so. That is a factual edit, not a new invariant, but it does put `factory.py` and the
  build skill's prose in the diff, which the intent's *Affected* list didn't name.
- **Every node through `textContent`** (`h()`): R13, under the existing page test.
- **`TEMPLATE_READS`** ("make the script read a new template heading, and that table gets the
  entry in the same change"): R12. Its consequence is that a host whose `.sdlc/templates/plan.md`
  drops `## Files to change` sees it under `drift`'s `breaking`, and `readiness` stops being
  `complete` until it is fixed or the override is removed. Without the entry, the board would
  quietly show no hint for such a host.
- **The base branch is never named `main`** (`test_no_git_call_names_main_itself`). The history
  walk uses `trunk` from `state()`. With no trunk, there is no history.
- **Windows:** every new `subprocess` path goes through `sdlc._git`, which already sets
  `encoding="utf-8"`. Paths compared with git's output are `as_posix()`. `factory.py`'s
  `step.md` write passes `newline="\n"`.
- **Skills:** the build skill's edit is prose only, so no new command, rule or WAIT. If ship's
  `cases` puts the factory's build skill in scope, the skill evals apply as for any skill edit.
- **Overlap with 086-board-signals-by-stage:** it edits the same `_factory()` and `test_board.py`.
  Whichever lands second rebases. Nothing here depends on 086.

## Alternatives rejected

- **A copy of `loop_state()`'s step logic in the board, pinned by a test.** It needs `depth()`,
  `ui_review()`, `_gate_state()`'s build hash, the base branch's `factory.toml` and `[review]`,
  and a git diff per request: most of `factory.py`'s config loading copied into the board. Even
  then it would give the step that is *next*, not one the supervisor has *started*, and no start
  time. One pinned record from the reading that already decides the step is smaller and more
  accurate.
- **Start times from file mtimes alone** (the newest reply, gate file or `.sessions` append).
  Resumed builder steps append nothing. The gate leaves no file until it ends. And the newest file
  can't tell "running" from "waiting for the supervisor". It is used only for the first build
  (R6), where `builder.sessions` is appended just before that session starts and nothing else
  could say it.
- **Typical times from `Sdlc-Role:` or `Sdlc-Stage … elapsed=` trailers.** These are per agent and
  per stage, not per step: the builder's build, fixes and reworks are summed. They are also absent
  when transcripts weren't readable. The closed change's own `costs.jsonl` has every session, in
  order.
- **Having `measure` add per-step trailers at close.** That changes the `Sdlc-*` trailer contract
  ("extend, never redefine") to serve a display. It would also give nothing for the history that
  already exists, which `Close^` holds as it is.
- **Reading history on every request, or caching to disk.** The first breaks the intent's
  constraint. The second makes the board write. An in-memory cache keyed by the base tip is
  invalidated by the only event that adds history: a close.
- **A whole-run ETA.** The round count isn't known in advance (rework depends on the reviews),
  so any whole-run figure would be a guess presented as a promise.
- **Mean instead of median.** One run stalled on a decision for a day would skew a mean for
  weeks.

## Verification

    uv run --group dev pytest -q tests/test_board.py tests/test_factory.py
    uv run --group dev pytest -q -m portable
    ./check.sh

Healthy looks like this:

- The two files' tests all pass, the new ones by the names in R1–R14.
- The portable run passes.
- `./check.sh` ends with ruff clean, `ruff format --check` with nothing to reformat, pytest
  green, and `claude plugin validate --strict` passing.
- `uv run --quiet --script scripts/sdlc.py drift` from the change's checkout reports nothing (no
  `defaults/` or `guide/` edit, so `setup.json` is untouched).

Manual check, on the board:

1. Run `uv run --quiet --script scripts/sdlc.py board` and open the page while a factory run is
   under way, or against a fixture folder with a `runs/step.md` naming `review` for round 2, two of
   four reviews written, and three or more closed factory changes of that tier in history.
2. Its card shows `R2 of 3`, build and gate done, `reviews 2/4` current, and verify, rework and
   approve still to do.
3. The bar is labelled `~Nm typical · estimate (k runs)` and never fills past about 95%.
4. When there's a plan, the hint reads `plan: T of N files touched`.
5. A change built by hand shows none of it.
6. `git status` in the main checkout is unchanged after the board has served a few polls.
