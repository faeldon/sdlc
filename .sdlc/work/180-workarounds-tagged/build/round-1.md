I've built change 180 and left it uncommitted in the worktree. All 13 requirements are in, and the full gate passed: 3254 tests, lint and format clean, and both plugins' manifests validate.

**What it does:** `retro` now prints a `simplicity.workarounds` block, worked out from git history alone:
- **`outside` and `hand_record`:** commits on the base branch that no change or command made. Ones that touch a record are counted apart from ones that touch only code.
- **`restored`:** register entries filed again after an earlier commit removed them.
- **`unknown`:** commits before a change whose start can't be found. These are not counted as outside, and a problem names the change.
- **`overrides`:** the landing train's ejections by cause, stopped trains, and fixes the person asked for at landing. Only factory-built changes are counted.

Each count carries its `n` and is null when `n` is 0.

On this repo, since the last retrospective, it finds:
- 64 commits on the base branch, none outside the loop.
- 3 restored entries, all in one `File` commit. I checked one in history: 166's `Close` retired 2026-11-18-68 and that commit filed it again. This is the case the intent describes.
- No ejections or stops, but no factory change in the window has the ejection record yet, so those zeros don't mean much.
- 4 fixes asked at landing, across 24 factory changes.

A full `sdlc.py retro` run leaves the tree unchanged.

**Slices built:**
1. **Commit walk (R1, R2, R7, R8):** `_workarounds()` in `scripts/retro.py`. I added two constants to `sdlc.py`: `SETUP_SUBJECTS` (setup's and uninstall's commit subjects) and `TRIAGE_SUBJECT`, which `_inbox_commit()` now uses.
2. **Restored entries (R3):** one pass over the register's history.
3. **Ejection row (R4, R5):** each row now names its train (when it began), added after 174's three fields. If the row can't be written, that becomes a `problems` entry and the eject or stop goes ahead.
4. **Overrides (R6, R11):** new readers `ejections()` and `land_asks()` in `factory_records.py`, plus `LAND_ASK_RE`. `spend_rows()` now uses the same `ejections()` reader.
5. **The rest:** the R10 docstrings, the R13 `unmeasured` entry, the R9 review bullet, and the R12 docs.

**Tests added:**
- `tests/test_retro.py`:
  - hand commit outside the loop, with and without (R1)
  - window starting after the adoption commit (R1)
  - record vs code (R2)
  - restored entry (R3)
  - change with no start leaves its commits unknown (R7)
  - null overrides with no factory change (R7)
  - overrides read from each factory change's commit, a dropped one included (R6)
  - the R13 entry
- `tests/test_train.py`: a stopped train's rows name it (R4); an ejection whose row can't be written still ejects (R5).
- `tests/test_archive.py`: `errors` never becomes a trailer (R10).
- `tests/test_modules.py`: `LAND_ASK_RE` pinned to `factory.land_ask_path()`; the new names added to its lists of record names and record files.
- `tests/test_skills.py`: `SETUP_SUBJECTS` pinned to the setup and uninstall skills.

174's `test_an_ejection_is_recorded_and_amended_in` passes unchanged.

Three of these passed the first time they ran, because the code came first:
- **R6:** I broke the stop count by hand and the test failed on it, so it does check something.
- **R10 and the module pins:** they lock in behaviour that already worked, as the spec intended.

The rest failed first for the reason expected. Partway through, my test constant `REGISTER` replaced an existing one with the same name in `test_retro.py`, which broke five ranking tests. I renamed mine `INBOX_PATH`, and all of `test_retro.py` passes again (197).

**Beyond the spec:**
- Under `train --run`, an eject's output reaches the person only through `undos`, so a recording problem would have been lost there. It now rides on the undo entry, and the land skill tells the agent to report it.
- The eject output now always has a `problems` key, empty when nothing went wrong.
- The walk asks git for unescaped paths (`core.quotePath=false`), following `.sdlc/REVIEW.md`'s warning about comparing escaped and unescaped paths.

**`plan.md`:** I wrote it before the code. Afterwards I updated it to name the helpers as built, the loop's `undos` and land-skill edit, the `ejected_at` rename inside `spend_rows()`, and the two acceptance checks. **`checks.md`** holds two checks, for R9 and R12, and both pass.

**`notes.md`:** one open item. `/sdlc:retro`'s passes don't read `simplicity.workarounds` yet, and the report shows it only once S14 lands.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q -n auto tests/test_retro.py -k "outside_the_loop or took_the_plugin or told_from or restored or leaves_its_commits or overrides_are or what_history_cannot or lists_the_entries_it_may_rerank or only_reranks"
18 passed in 33.84s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_train.py::test_a_stopped_trains_rows_name_it tests/test_train.py::test_an_ejection_that_cant_be_recorded_still_ejects tests/test_train.py::test_an_ejection_is_recorded_and_amended_in tests/test_archive.py::test_measures_errors_never_become_a_trailer tests/test_modules.py tests/test_skills.py::test_setup_subjects_are_the_skills_own
33 passed in 34.24s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_retro.py
197 passed in 43.52s
exit: 0

$ cd /tmp/base180 && uv run --group dev pytest -q tests/test_retro.py -k "lists_the_entries_it_may_rerank or only_reranks_and_appends"
9 passed, 180 deselected in 1.13s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 180
All checks passed!
313 files already formatted
3254 passed, 29 skipped in 238.86s (0:03:58)
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro (simplicity.workarounds, then git status compared)
outside count 0 n 64; hand_record count 0 n 64; restored count 3 n 69; unknown count 0; overrides ejections 0 / stops 0 / fixes 4 over n 24
unchanged
exit: 0

$ awk '/^### The ways this repo.s code fails/{f=1;next} /^## /{f=0} f' .sdlc/REVIEW.md | grep -q "^- \*\*A doc's claim the change made false\.\*\*"
exit: 0

$ grep -q 'simplicity.workarounds' docs/REFERENCE.md && grep -q 'simplicity.workarounds' skills/retro/SKILL.md && grep -q 'which train (train' plugins/factory/README.md && grep -q 'Done: 180' docs/RETRO-SCORECARD.md
exit: 0
