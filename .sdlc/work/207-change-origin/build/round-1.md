I built all twelve requirements, test first. Nothing is committed. The full gate run through `factory.py check 207` passed: 3635 passed, 29 skipped, exit 0. To make it pass I also changed one test file the spec doesn't cover (first decision below).

**Slices built (see plan.md)**
1. **R1–R2:** `ORIGINS = ("host", "self")` in `sdlc.py`. `load_change()` reads `origin:` as text into `rec["origin"]`. A wrong word or more than one value is an error; a missing line is not.
2. **R3:** `_change_record()` sets `origin` only for a valid line. It never guesses one.
3. **R6–R7:** `parse_trailers()` reads `origin` back as text, and the `metrics.py` docstring gains a paragraph on `Sdlc-Origin`.
4. **R4–R5:** `origin_trailer()` in `closing.py` sits beside `fix_trailers()` and never raises. `_step_remove_folder()` adds its line to the `Close` commit. A drop never gets one.
5. **R8–R9:** `retro()` returns `origins` (`host`, `self`, `unknown`, `n`). The retro skill reads the `host` changes as evidence from another repo, names no goal id, and says nothing about origins when every change is `unknown`.
6. **R11:** `BODY_KEYS` gains `"Origin"`. `/sdlc:idea` and `/sdlc:bug` add `Origin: host` to an entry only when the person says it came from another repo.
7. **R10:** `/sdlc:intent` proposes `origin:` and shows where it came from. Its question gains `, found in a host` or `, found here` in every form. `batch.md` does the same.
8. **R12:** REFERENCE.md now covers the trailer, `origins`, the intent's `origin:` line and the register's `Origin:` line. FEATURES.md gains entries for `origin:`, `Sdlc-Origin` and `origins`.

**Tests added.** Each failed first for the expected reason; the three skill tests failed against the base versions of the skills.
- **`test_sdlc.py`:** `test_origin_values_are_host_and_self` (R1); `test_vet_strict_passes_a_change_with_no_origin` and `test_an_origin_outside_host_and_self_is_an_error` (R2); `test_a_closed_change_without_origin_reads_none` (R3); `test_an_entry_reads_its_origin_line` (R11).
- **`test_archive.py`:** `test_close_writes_an_origin_trailer` (R4) and `test_an_invalid_origin_closes_without_the_trailer`; `test_a_change_without_origin_closes_without_the_trailer` and `test_a_dropped_change_carries_no_origin_trailer` (R5).
- **`test_metrics.py`:** `test_parse_trailers_reads_origin_as_text` (R6).
- **`test_retro.py`:** `test_retro_counts_changes_by_origin` (R8) and `test_a_window_before_origins_reads_as_all_unknown`. `origins` was also added to the every-key test.
- **`test_skills.py`:** `test_retro_skill_reads_origins` (R9), `test_intent_proposes_an_origin` (R10), `test_idea_and_bug_offer_an_origin_line` (R11).
- R7 and R12 are covered by the existing `test_feature_map.py`, which failed until FEATURES.md named `Sdlc-Origin`.

**Changes to `plan.md`:** I wrote it first, then added `batch.md`, the extra tests and the fixture fix below. There is no `notes.md`: nothing was left undone.

**Decisions**
- DECISION: [default] Fix the stale `tests/fixtures/close-output.json` in this change? It pins `plugin=1.10.0`, which Release 1.11.0 made stale, so four `test_close_output_is_unchanged` cases fail on the base branch itself (confirmed on a `git archive HEAD` copy). The gate would be red for any build. Going ahead with `_normal()` masking `plugin=<version>`, as it masks shas, unless told otherwise.
  - OPTION: mask the version in this change — the gate goes green, and later releases won't break the fixture again; an unrelated test edit rides on this change
  - OPTION: revert it and fix it in its own Tier 0 change on the base branch — keeps this change narrow; this build's gate is red until that lands
  - WHY: the gate runs the whole suite on this build, and the fault isn't in this change's code.
- DECISION: [default] Write `origin:` on 207's own intent? Leaving it unset, the same as 206 (the intent's open question): the line is the person's to approve through `/sdlc:intent`, not the builder's.
  - OPTION: leave it unset — reads as unknown, which is what the spec says a missing line means; 207 isn't counted
  - OPTION: `origin: self` — 207 is counted; the builder would be writing a line the person never approved
  - WHY: the spec's constraint that origins are never guessed or backfilled.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_sdlc.py -k "origin"   (before the code)
6 failed, 289 deselected in 25.79s
exit: 1

$ uv run --group dev pytest -q tests/test_metrics.py::test_parse_trailers_reads_origin_as_text   (before the code)
E       AssertionError: assert ({} == 'host')
1 failed in 0.44s
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py -k origin   (before the code)
E       AttributeError: module 'sdlc_closing' has no attribute 'origin_trailer'
2 failed, 2 passed, 170 deselected in 13.60s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k origin   (before the code)
E       KeyError: 'origins'
2 failed, 288 deselected in 13.03s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py -k "origin"   (against the base skill texts)
3 failed, 428 deselected in 0.35s
exit: 1

$ uv run --group dev pytest -q -p no:cacheprovider "tests/test_archive.py::test_close_output_is_unchanged"   (in a `git archive HEAD` copy, /tmp/base207)
4 failed, 1 passed in 18.52s
exit: 1

$ uv run --group dev pytest -q "tests/test_archive.py::test_close_output_is_unchanged"   (after the `_normal()` fix)
5 passed in 7.23s
exit: 0

$ uv run --group dev ruff check . && uv run --group dev ruff format --check .
All checks passed!
331 files already formatted
exit: 0

$ uv run --group dev pytest -q tests/test_sdlc.py tests/test_archive.py tests/test_metrics.py tests/test_retro.py tests/test_skills.py -k "origin"
17 passed, 1380 deselected in 13.66s
exit: 0

$ uv run --group dev pytest -q tests/test_archive.py::test_close_output_is_unchanged tests/test_feature_map.py
14 passed in 4.19s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 207
3635 passed, 29 skipped in 224.14s (0:03:44)
✔ Validation passed
exit: 0
