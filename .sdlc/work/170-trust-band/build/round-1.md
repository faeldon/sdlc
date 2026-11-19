I built change 170 and left it uncommitted. The full gate passes: 3081 passed, 28 skipped, and ruff, format and plugin validate are clean. Three things go beyond the spec and are raised as defaults at the end.

## Slices built
1. **Runtime events (R1).** `read_events()` now records each Claude Code version and model it finds as a `runtime` event. It reads them from the main session, factory agent sessions and sub-agents, and skips empty values and `<synthetic>`. `summarize()` and lead time's first mark both ignore the new event, so no existing figure moves.
2. **The trailer (R2).** `metrics.runtime_trailer()` builds the `Sdlc-Runtime` line, and `parse_trailers()` reads it back as text, so `2.1.10` stays a string.
3. **Close writes it (R3).** It goes after `Sdlc-Lead` on every `Close` and `Drop` commit. With no transcripts it holds `plugin=` alone. If building it raises, the line is left out, coverage gains ` runtime=failed`, and the close still lands.
4. **Coverage (R4–R6).** `_coverage()` gives lead time, escape rate, the person's minutes and spend each a `coverage` block and a `missing_because` count, using the fixed reason words.
5. **The report (R7, R9).** The Window section gains one *Coverage* line per headline (in italics, marked `a hint: under half the changes`, when it's thin) and a *What changed underneath* line. `templates/retro.md` is unchanged.
6. **What changed underneath (R8, R12).** `underneath()` compares this window with the last one, which `_previous_window()` finds. It reads history only.
7. **No factory changes (R10).** The window counts factory changes and changes with no way of building recorded. With no factory change, landing catches are null and the report says `No factory changes in this window.`
8. **Docs and skill (R11, R13, R14).** REFERENCE.md (*Metrics* and *Retrospectives*), RETRO-SCORECARD.md (S11's two figures marked captured), `metrics.py`'s docstring, and one bullet in the retro skill.

## Tests added
- **`test_metrics.py`:** `test_runtime_is_read_from_each_entrys_version_and_model` (R1) and `test_runtime_trailer_round_trips` (R2).
- **`test_archive.py`:** `test_close_writes_the_runtime_line`, `test_a_drop_records_the_plugin_alone` and `test_a_failed_runtime_read_never_stops_a_close` (R3).
- **`test_adoption.py`:** a check that a bare repo's close writes `^Sdlc-Runtime: plugin=\d+\.\d+\.\d+$` (R3).
- **`test_retro.py`:** one test each for R4/R5, R6 (three cases), R7, R8 (plus one for a single earlier retrospective), R9, R10, R11 and R12.

Each failed for the expected reason before the code went in.

## Existing tests updated
- 162's `test_close_times_a_factory_change_from_its_run_files` assumed `Sdlc-Lead` was the last measured line; the runtime line now follows it.
- Three exact-shape assertions gained the new keys: the process views' `escapes` and `window`, and `lead`.
- 136's landing-catch fixture had factory-reviewed changes with no `Sdlc-Mode`. It now carries `Sdlc-Mode: factory`, as every real factory close does, because R10 counts catches only in a window with a factory change.
- `test_prose_counts_each_of_the_plugins_skills` now checks that a host leaves out ship's `cases.md` and this repo keeps it.

`plan.md` now records all of these and the extra test names. Nothing went into `notes.md`.

- DECISION: [default] Leave ship's `cases.md` branch out of a host's `prose` block. The spec assumed retro never mentions the skills' cases, but `prose` listed that file in every host's JSON, so R11 couldn't pass without it. Going ahead unless told otherwise.
  - OPTION: leave it out in a host (`OWN_REPO_BRANCHES`) — meets R11, and a host never reads that branch; one more rule in `prose`
  - OPTION: keep listing it and narrow R11 — no code change; a host's JSON keeps naming this repo's cases
  - WHY: R11's own test fails on that key, and `SHIP_BRANCHES` names the file only where the cases suite exists
- DECISION: [default] Strip the trailing words close adds (` lead=failed`, ` runtime=failed`) from a `none:` coverage reason, for spend's `why` as well as the new `missing_because`. Going ahead unless told otherwise.
  - OPTION: strip them everywhere (`_none_reason()`) — R5's reason words come out as written, and `missing_because` matches spend's `why`; spend's `why` text changes for such changes
  - OPTION: strip them only for coverage — spend's `why` stays as it was; the same change shows two different reasons
  - WHY: R5 names the reasons as `no transcripts for this repo`, without the suffix
- DECISION: [default] Clean each version in `Sdlc-Runtime` with `_model_word()`, not `_word()`. Going ahead unless told otherwise.
  - OPTION: `_model_word()` — a `,` can't split one value and a `:` can't turn it into a pair; it is stricter than `_word()`
  - OPTION: `_word()`, as the spec wrote — follows the spec exactly; a value holding `a:1` reads back as a dict
  - WHY: R2 asks for a version to come back as text

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_metrics.py -k "runtime"   (before the code)
FAILED tests/test_metrics.py::test_runtime_is_read_from_each_entrys_version_and_model
FAILED tests/test_metrics.py::test_runtime_trailer_round_trips - AttributeErr...
2 failed, 187 deselected in 0.17s
exit: 1

$ uv run --group dev pytest -q tests/test_metrics.py
189 passed in 1.76s
exit: 0

$ uv run --group dev pytest -q tests/test_archive.py -k "runtime or plugin_alone"   (before the code)
3 failed, 159 deselected in 6.12s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_archive.py tests/test_adoption.py
173 passed in 24.49s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_nits.py tests/test_train.py
59 passed in 80.67s (0:01:20)
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py -k "coverage or greyed"   (before the code)
4 failed, 145 deselected in 4.67s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k "underneath or last_window"   (before the code)
4 failed, 150 deselected in 8.02s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k "no_factory_changes"   (before the code)
E       KeyError: 'factory'
1 failed, 154 deselected in 4.02s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_retro.py
156 passed in 30.65s
exit: 0

$ uv run --group dev ruff check scripts tests
All checks passed!
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 170
All checks passed!
307 files already formatted
3081 passed, 28 skipped in 128.71s (0:02:08)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_metrics.py tests/test_retro.py tests/test_archive.py tests/test_adoption.py tests/test_skills.py -k "runtime or coverage or greyed or greys or underneath or last_window or no_factory or never_mentions_the_cases or prose_counts or landing_catch or process_views_count or without_a_lead_line or factory_change_from_its_run_files or plugin_alone or first_change"
23 passed in 31.72s
exit: 0

$ git diff --exit-code main -- templates/retro.md && echo "template unchanged"
template unchanged
exit: 0
