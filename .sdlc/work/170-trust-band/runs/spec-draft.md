---
id: 170
slug: trust-band
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 170 — The retrospective says how far its numbers can be trusted · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code before designing:
- No scorecard exists yet: S14 builds it. So "each headline" here means the four headline figures `sdlc.py retro` already produces:
  - lead time, `process.lead` (Speed);
  - escape rate, `process.escapes` (Quality);
  - the person's response and stops, `metrics` (Autonomy);
  - token spend, `spend` (Cost; dollars come with S4).
- The structural debt index (S7, S8) and the Simplicity headlines (S5, `prose`) are not per change, so they get no coverage here.
- Nothing in `scripts/retro.py`, `templates/retro.md` or `skills/retro/SKILL.md` mentions the skills' cases today.
- The only figure that is factory-only today is `landing_catches`. Mode comparison and pipeline health are S9 and S10.
- Real Claude Code transcripts carry the Claude Code version as `version` on each entry, and the model as `message.model` on assistant entries. `read_events()` reads neither today. Each new read gets a test built from a real entry's shape (REVIEW.md, *A transcript's shape assumed, not read*).

1. R1. `metrics.read_events()` records each Claude Code version (an entry's `version`) and each model (an assistant entry's `message.model`) found in the entries it keeps for the change, as a new event kind, `runtime{claude?, model?}`.
   - It reads the main session, each factory agent's session (`_run()`) and each sub-agent's transcript (`_subagent()`).
   - It skips an empty value and the harness's `<synthetic>` model.
   - `test_runtime_is_read_from_each_entrys_version_and_model` (`tests/test_metrics.py`) uses entries copied in shape from a real transcript, with neutral values and no text or path. It fails if a sub-agent's model is missing, if `<synthetic>` appears, or if a branch's other sessions leak in.
2. R2. A new pure function, `metrics.runtime_trailer(events, role_models, plugin)`, returns `Sdlc-Runtime: claude=<v>[,<v>…] models=<m>[,<m>…] plugin=<v>`, or None when it knows nothing.
   - `models` joins the `runtime` events' models with the factory roles' `model=` from `runs/costs.jsonl`.
   - Each value is sorted and deduplicated, and passed through `_word()`, or `_model_word()` for models.
   - A part that isn't known is left out, never written empty.
   - `parse_trailers()` reads it back as `runtime`: a dict of strings, so `2.1.10` stays text.
   - `test_runtime_trailer_round_trips` fails if a version comes back as a number, or if a `/`, `~` or space survives into the line.
3. R3. Close writes the line after the lines it already writes, on every `Close` and `Drop` commit (`closing.measure_change()`'s `finish()`). `trailers()`' own output is unchanged: the existing trailer tests pass untouched.
   - With no transcripts, the line holds `plugin=` alone, from `sdlc.plugin_version()`. `tests/test_adoption.py` asserts `^Sdlc-Runtime: plugin=\d+\.\d+\.\d+$`.
   - If building the line raises, the line is left out, `Sdlc-Coverage` gains ` runtime=failed`, and the close still lands.
   - `test_a_failed_runtime_read_never_stops_a_close` fails if the close stops, or if the line appears anyway.
4. R4. Each headline block carries `coverage: {measured, of, greyed}` and `missing_because: {<reason>: <count>}`, and the counts in `missing_because` sum to `of - measured`. The blocks are `process.lead`, `process.escapes`, `metrics` and `spend`; `of` is the window's closed changes.
   - `test_every_headline_says_its_coverage_and_why_the_rest_is_missing` (`tests/test_retro.py`) builds a window that mixes:
     - a fully measured change;
     - a history-only change;
     - a change with `lead=none`;
     - a change closed before `Sdlc-Lead` existed;
     - a commit with no trailers.
   - It fails on any headline whose sums disagree, or that lacks either field.
5. R5. The reasons are fixed words, read only from what each commit carries:
   - **Lead time:**
     - `not measured at close` (no `Sdlc-*` at all);
     - `no opened: line` (`lead=none`);
     - `opened: unreadable` (`lead=bad-opened`);
     - `timing failed` (`lead=failed`);
     - `closed before lead time was recorded` (none of those).
   - **The person's minutes:**
     - `not measured at close`;
     - the `Sdlc-Coverage: none: <reason>` text (`no transcripts for this repo`, `metrics.transcripts is off`).
   - **Spend:** its existing `why`.
   - **Escape rate:** rests on every closed change, so it has an empty `missing_because`.
   - Pinned by the same test as R4, with the expected dicts written out.
6. R6. `greyed` is true exactly when `2 × measured < of`. With `of` 0 it is false and the headline shows no line. `test_a_headline_under_half_its_changes_is_greyed` checks 4 of 10 (greyed), 5 of 10 (not greyed) and 0 of 0.
7. R7. The report's `{{window}}` value (`render_report()`) is followed by one *Coverage* line per headline, giving `measured of of changes` and the reasons with their counts.
   - A greyed headline's line is in italics and ends `a hint: under half the changes`.
   - `templates/retro.md` is not edited.
   - `test_the_report_greys_a_thin_headline` fails if a greyed line isn't marked, or a full one is.
8. R8. `process.underneath` holds, for the window and for the last window:
   - each dimension (`claude`, `models`, `plugin`) as `{value: changes}`;
   - `recorded` and `unrecorded` counts;
   - `changed: {claude, models, plugin}`.

   Its rules:
   - Each `changed` value is true or false, and null when either side recorded none.
   - A change closed before `Sdlc-Runtime` gives its models from its `Sdlc-Role` `model=`, if any. It counts as `unrecorded` for `claude` and `plugin`.
   - The last window is the changes closed between the retrospective before `since` and `since`. With only one retrospective, it runs from the start of history to `since`. With none, `previous` is null.
   - `test_what_changed_underneath_compares_with_the_last_window` fails if a version that differs isn't flagged, if one that matches is, or if an unrecorded side reads as unchanged rather than null.
9. R9. The report adds a *What changed underneath* line after the coverage lines.
   - It gives each dimension's values in the window against the last window, says which changed, and how many changes recorded none.
   - With no earlier window, it says `no earlier window to compare`.
   - Every value is passed through `metrics._word()` again, so a hand-written trailer can't put a path in the report.
   - `test_the_report_says_what_changed_underneath` fails on a missing line, or on a value holding `/`.
10. R10. `process.window.factory` counts the window's changes whose `Sdlc-Mode` is `factory`.
    - When it is 0, `process.landing_catches` is null, and the report says `No factory changes in this window.` where the landing-catches line would be, never `0 of 0`.
    - Changes with no `Sdlc-Mode` are counted as `process.window.mode_unknown`, and the sentence names them when there are any.
    - `test_a_window_with_no_factory_changes_says_so` fails on `Landing catches: 0 of 0` or on a missing sentence.
11. R11. In a host, `sdlc.py retro`'s JSON and `retro --report` hold nothing about the skills' cases: no `cases` key outside `tests.times`, where JUnit test cases are counted, and no `skills' cases`, `Skill evals` or `run-cases` text. `test_a_hosts_retrospective_never_mentions_the_cases` runs both on a host fixture (`_own_repo()` false) and fails on any of them.
12. R12. Underneath is read only from history. `retro` reads no transcript, runs no `claude --version` and reads no `plugin.json`, so `cmd_retro()`'s "reads nothing outside the repo" holds. `test_underneath_reads_history_alone` replaces `subprocess.run` and the `claude` lookup with stand-ins that raise. It fails if either is reached.
13. R13. The docs say it:
    - `docs/REFERENCE.md` *Metrics* describes `Sdlc-Runtime` and ` runtime=failed`.
    - `docs/REFERENCE.md` *Retrospectives* describes `coverage`, `missing_because`, greying, `process.underneath` and `process.window.factory`.
    - `metrics.py`'s docstring lists the `runtime` event and `runtime_trailer()` in its contract.
    - `docs/RETRO-SCORECARD.md` marks S11's two figures captured, and changes *What changed underneath*'s **Where** to the `Sdlc-Runtime` trailer.

    The review checks these; `./check.sh` stays green.
14. R14. `skills/retro/SKILL.md` gains one bullet, beside `unmeasured`, telling the passes two things:
    - read each headline's `coverage` and treat a `greyed` one as a hint;
    - rule out `process.underneath.changed` before reading any trend.

    Its `allowed-tools` and its WAIT are unchanged; `tests/test_skills.py` passes.

## Design

**At close (`scripts/metrics.py`, `scripts/closing.py`).**
- `read_events()` already walks every kept entry, in three loops: the main session's, `_run()`'s and `_subagent()`'s.
- Each loop notes the distinct `version` and `message.model` values it sees for the change. It emits one `runtime` event per distinct value per session, at that value's first timestamp, so the event list grows by a handful of entries at most.
- `runtime_trailer()` sits beside `lead_trailer()`: pure, given the events, the roles' models and the plugin version, which `closing` passes in because `metrics.py` imports nothing of `sdlc.py`.
- The roles' models are what `_agent_models()` already reads from `runs/costs.jsonl`.
- `finish()` calls it inside its own `try` after the lead line. It appends the line to the list it returns, as `lead` is appended, and leaves `trailers()` alone.
- The history-only path has no events, so it yields `plugin=` alone.
- `parse_trailers()` needs no change: a line whose first word holds `=` already falls to `out[key] = fields`, and `_value()` keeps `2.1.4,2.1.5` and `1.9.0` as text. R2's test pins that, so a later change to `_value()` can't break it quietly.

**At the retrospective (`scripts/retro.py`).**
- **Coverage, one helper:** `_coverage(changes, measured, why)` returns `{"coverage": {...}, "missing_because": {...}}` from a predicate and a reason function, and is used four times:
  - lead time, which reads `metrics.lead` and the `lead=` words in `metrics.coverage`;
  - the person's minutes, which reads `metrics.totals` and `coverage`'s `none:` prefix, reusing `_unrecorded()`'s reading of it;
  - spend, which reuses `recorded` and `why`, which already exist;
  - escapes, all of the window.
- **Where coverage is attached:**
  - `lead_view()` adds the result to its block, and `process_views()` adds it to `escapes`;
  - `metrics_summary()` adds it to `metrics`, and `_spend()` adds it to `spend`;
  - each headline carries its own coverage, and nothing holds a second copy.
- **Underneath:** `underneath(changes, previous)` is a pure function over two lists of records, reading `metrics.runtime` and falling back to `metrics.roles[*].model`.
  - Its previous list comes from `_previous_window(home, trunk, since)`. That reuses `sdlc.retrospectives()` the way `bugs_retro()` does for the escape rate, and calls `sdlc.closed_changes(home, older_sha_or_None, since_sha)`.
  - `retro()` and `retro_report()` both call it and pass the result into `process_views()`, which stores it as `process.underneath`.
  - The report and the JSON read the same block.
- **Factory count:** `process_views()` counts `window.factory` and `window.mode_unknown` from `metrics.mode`, and sets `landing_catches` to None when `factory` is 0.
- **The report:**
  - `render_report()` gains an optional `metrics` argument, which `retro_report()` fills from `metrics_summary()`. Existing two-argument calls still work: without `metrics`, the Autonomy line says `not given`.
  - The coverage lines and the underneath line are appended to the `window` value, since the template stays as it is. A host's override that keeps `{{window}}` gets them too; one without it loses them, as it already loses the window sentence.
  - `_sources_text()` prints the no-factory sentence when `catches` is None and `window.factory` is 0.
- **What `--metrics` shows:** `_lean()` already strips each change's `metrics`, so a change's own runtime is printed only with `--metrics`. The aggregates are built from the full records first.

**Edge cases.**
- A change whose versions moved during its life records both, comma-joined, and counts once under each.
- A trailer value a hand edit damaged is still only a word after `_word()`.
- A first retrospective has `previous: null`, and its `changed` values are all null.

## Contracts touched

- **The metrics trailer format is extended, never redefined** (`metrics.py`'s docstring, REFERENCE.md *Metrics*). The change adds one new line and one new `Sdlc-Coverage` word, the way `Sdlc-Lead` and ` lead=failed` were added. No existing key, field or value changes meaning, and `trailers()`' output is identical.
- **`metrics.py` is pure.** `runtime_trailer()` takes the plugin version as an argument. No subprocess runs and nothing imports `sdlc.py`.
- **No message text, file path or session id leaves `read_events`.** A version and a model name are names. Both are sanitised by `_word()` or `_model_word()` when written, and again when the report renders them.
- **Measuring never refuses.** A failure here only drops the line and adds ` runtime=failed` (R3).
- **A transcript's shape is read, not assumed** (REVIEW.md). R1's fixture is copied in shape from a real transcript's entries, with neutral values.
- **Retro reads only history.** `cmd_retro()` says it reads nothing outside the repo. Underneath comes from trailers, never from `plugin.json`, `claude --version` or transcripts at retro time (R12). Reading `plugin.json` at close is the closing script reading its own manifest, as `plugin_version()` already does for `drift`.
- **Modules loaded by path.** `retro.py` reaches `metrics` and the history walks as `sdlc.metrics`, `sdlc.closed_changes` and `sdlc.retrospectives`. `closing.py` reaches `plugin_version` as `sdlc.plugin_version`, so tests' stand-ins reach it.
- **The factory boundary.** The only new factory data read is `runs/costs.jsonl`'s models, which `_agent_models()` already reads through `factory_records`. No other core file names a record.
- **Templates and `breaking`.** `templates/retro.md` is not edited, and no new template heading or config key is read, so `TEMPLATE_READS`, `RETIRED_KEYS` and `.sdlc/setup.json` are untouched.
- **Nothing local.** Test data uses made-up versions and model names under made-up paths, and no project or machine path appears.
- **Windows.** No new subprocess or file write; every reader is a text parse.
- **Skills.** R14 adds prose only: no command, rule, WAIT or config key, so `READS_CONFIG` and `allowed-tools` stay as they are.

No invariant needs to change.

## Alternatives rejected

- **Claude Code version from the skills' cases (`result.json`'s `claudeVersion`)**, which is where the scorecard doc first pointed. A host has no cases (R11), and a run of the cases happens at a different time from the change. The trailer is right in every repo.
- **`claude --version` at close.** It gives the version that ran close, not the one the change was built on. It would also add a subprocess, which CI and `test_adoption.py`'s bare repo don't have.
- **Reading transcripts at retro time.** Transcripts live on one machine and go stale, while retro reads history alone. Close's trailers are the record, as for every other metric.
- **Plugin version from release tags** (also the scorecard doc's first pointer). In a host, the tags are the host's own product's versions, and even here a tag says what was released, not what ran.
- **A separate top-level `trust` block holding every headline's coverage.** It would be a second copy of numbers each headline block already owns, and could drift from them. Each block carries its own coverage instead, and only underneath, which belongs to no headline, gets a block of its own.
- **A `## Trust` section in the template.** The intent rules it out: the template stays unedited, as with 162, so a host's override doesn't break. The window section already says what the figures rest on.
- **Greying with HTML colour.** GitHub strips `style`, so the line would look like any other. Italics plus the words `a hint` survive every renderer.
- **Hiding the factory figures by `factory_enabled()`.** That setting says whether the plugin is installed now, not what the window built. A host that dropped the factory still has factory changes in an older window. The window's own `Sdlc-Mode` decides.
- **Coverage for the Simplicity headlines and the structural debt index.** They are not per change: `prose` is an estimate of the plugin, S5 and S7/S8 aren't built, and a coverage of N of N would only mislead.

## Verification

```bash
./check.sh                                                     # ruff, format, pytest -n auto, plugin validate: all green
uv run --group dev pytest -q tests/test_metrics.py tests/test_retro.py tests/test_adoption.py -n auto
uv run --group dev pytest -q -k "runtime or coverage or underneath or no_factory or never_mentions_the_cases" tests/
git diff --exit-code "$(git merge-base HEAD "$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null || echo main)")" -- templates/retro.md   # prints nothing
uv run --quiet --script scripts/sdlc.py retro | python3 -c 'import json,sys; d=json.load(sys.stdin); print({k: d["process"][k] for k in ("underneath",)}, d["process"]["lead"]["coverage"], d["spend"]["missing_because"])'
uv run --quiet --script scripts/sdlc.py retro --report | sed -n '/## Window/,/## Cycle time/p'
```

What healthy output looks like:
- The suite passes, the new tests included, and `claude plugin validate --strict` passes.
- `templates/retro.md` shows no diff.
- In this repo, most past changes predate the trailer. So the JSON shows `process.underneath.window.unrecorded` near the window's size, and `changed` values that are null, not false. `lead.coverage` shows the changes closed since 162 out of the window, with `closed before lead time was recorded` covering the rest.
- The report's Window section ends with one *Coverage* line per headline (italic where under half) and a *What changed underneath* line, with no path in either.
- After the first close that carries the trailer, `git log -1 --format=%B <close sha>` shows `Sdlc-Runtime: claude=… models=… plugin=…`.

