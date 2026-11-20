I built both halves of the change and left them uncommitted. Together the eight slow tests now take about a third of their old time. The retrospective's drift list goes from twelve tests to one.

## Slices built

**1. Drift reads what a test loads** (`scripts/indicators.py`, `scripts/retro.py`, `docs/REFERENCE.md`, `skills/retro/SKILL.md`)
- A test's code is now the code files its last change touched *that the test loads*. A test loads a code file when:
  - it names the file in a string or as a path (never in backticks, never a bare word with no suffix, matched on the path's trailing segments);
  - or one of its import lines names the file's stem (`import`, `from … import`, `require(…)`, `use`, `#include`);
  - or a helper it imports loads it.
- A data file under the tests (`.json`, `.txt`, `.md`, `.yaml`…: goldens, fixtures, prompts) is never read and is no one's code, so it never drifts.
- Retro reads each test as the base branch holds it, through `git show`. It reads only tests that would have drifted under the old rule. It stays read-only.
- Running it on this repo exposed two more problems, both fixed:
  - My first, looser rule matched prose mentions and files with no suffix.
  - `test_bugs.py` and `test_next_up.py` were last touched by 187, a change of more than 50 files. Pairing skipped it, so drift dated them back to 176. Such a change now still counts as a test's last change; it just gives the test no code.

**2. The slow tests** (`tests/test_train.py`, `tests/test_land.py`)
- Setup turned out to be under a second of each test's time. The cost is the train's own steps, so a shared fixture would have saved nothing. Instead I merged and dropped tests:
  - **Removed:** `test_every_ejection_names_its_cause`. Its three trains checked what the `train --run` tests already check (mutations below).
  - **Merged:** `test_train_run_resumes_after_a_kept_change` into `test_train_run_stops_at_a_kept_change_and_resumes` (renamed).
  - **Merged:** `test_train_run_lands_a_batch_of_three` into `test_a_killed_train_run_resumes`.
  - **Merged:** `test_a_train_stops_past_land_moves` into `test_a_move_mid_train_re_stacks_the_rest_and_counts_once`, which now runs with `[land] moves = 1`.
  - **Halved:** `test_a_train_fix_already_made_goes_on_to_the_gate` keeps only its `train --run` half. It reads the fix → gate → review order from the loop's progress lines.
  - **Shrunk:** `test_land.py`'s batch test lands two changes instead of three; one carries both the checks and the note.
- **Timing**, old and new run back to back, eight tests plus the two that absorbed them:

  | | Wall | CPU |
  |---|---|---|
  | Old | 356.8 s | 258.9 s |
  | New | 126.8 s | 110.9 s |
  | New as share of old | 36% | 43% |

  Single-test times swing a lot with this machine's load, so only the paired totals mean much.
- **Mutations** of each ejection cause the removed test checked (rerun with `cat /tmp/prof200/mutate.txt` under Evidence):
  - Gate, review, the failed-step refusal, `--eject` keeping the cause, and the reading's `ejected` cause: each fails a remaining test.
  - The readiness refusal fails none. The removed test never reached that path either, so no coverage was lost. It is in `notes.md`.

## Tests added
- **`test_indicators.py`:**
  - `test_a_test_drifts_only_with_the_code_it_loads`
  - `test_a_golden_never_drifts`: never drifts, never read.
  - `test_loads_follows_a_helper_the_test_imports`: a helper that is only mentioned, never imported, is not followed.
  - `test_loads_reads_names_and_imports`: 17 cases of naming and not naming.
  - `test_a_test_touched_by_a_change_too_large_to_pair_starts_again`
- **`test_retro.py`:** `test_drift_reads_the_test_at_the_base_branch` proves it reads the base branch, not the working tree.
- The existing drift tests now carry test texts.

Each new test failed first for the expected reason: no `read` parameter, no `loads`, or the large-change, prose, `branch` and `./` cases.

## `plan.md`
Written first. Since then it records the stricter naming rules, the large-change rule, and why each was needed.

## `notes.md`
- **The twelve tests the old rule named, and what became of each:**
  - The four goldens no longer drift.
  - `test_bugs.py`, `test_next_up.py` and `train_driver.py` now date from 187.
  - `test_decision_alternatives.py`, `test_prompts.py`, `test_indicators.py` and `test_surface.py` were named for code they don't load.
  - `test_function_heat.py` still drifts, rightly: it loads `retro.py` for one constant. It is kept as it is.
- **Two open `- [ ]` lines:**
  - The train's reading makes about 1,500 git calls per driven train of three, which is most of each train test's time.
  - The readiness-refusal cause has no test that fails without it.

- UNTESTABLE: none

No decisions raised.

## Evidence

$ uv run --group dev pytest -q tests/test_indicators.py
93 passed in 0.12s
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py -k "drift or due"
6 passed, 276 deselected in 14.37s
exit: 0

$ uv run --group dev pytest -q --durations=0 tests/test_train.py::test_a_killed_train_run_resumes tests/test_train.py::test_train_run_stops_at_a_kept_change_and_resumes
2 passed in 106.80s (0:01:46)
exit: 0

$ uv run --group dev pytest -q --durations=0 tests/test_train.py::test_a_move_mid_train_re_stacks_the_rest_and_counts_once
1 passed in 72.73s (0:01:12)
exit: 0

$ uv run --group dev pytest -q --durations=0 "tests/test_land.py::test_a_batch_with_checks_a_note_and_an_irreversible_path_lands_through_factory_alone"
1 passed in 49.50s
exit: 0

$ cat /tmp/prof200/mutate.txt
== M1 gate: exit 1
    FAILED tests/test_train.py::test_train_run_ejects_a_gate_fault_and_lands_the_rest
== M2 review: exit 1
    FAILED tests/test_train.py::test_train_run_stops_at_a_kept_change_and_resumes
== M3a refusal(failed): exit 1
    FAILED tests/test_train.py::test_train_run_stops_at_a_refusal - AssertionErro...
== M3b refusal(ready): exit 0
    5 passed, 83 deselected in 38.53s
== M4 eject keeps cause: exit 1
    FAILED tests/test_train.py::test_train_run_stops_at_a_kept_change_and_resumes
== M5 reading ejected cause: exit 1
    FAILED tests/test_train.py::test_train_run_stops_at_a_kept_change_and_resumes
    FAILED tests/test_train.py::test_train_run_ejects_a_gate_fault_and_lands_the_rest

$ /usr/bin/time -p uv run --group dev pytest -q -p no:cacheprovider --durations=0 <the eight and the two that absorbed them, from HEAD's copies>
10 passed in 356.75s (0:05:56)
real 356.99
user 96.33
sys 162.53
exit: 0

$ /usr/bin/time -p uv run --group dev pytest -q -p no:cacheprovider --durations=0 tests/test_train.py::test_train_run_ejects_a_gate_fault_and_lands_the_rest tests/test_train.py::test_train_run_stops_at_a_kept_change_and_resumes tests/test_train.py::test_a_killed_train_run_resumes tests/test_train.py::test_a_train_fix_already_made_goes_on_to_the_gate tests/test_train.py::test_a_move_mid_train_re_stacks_the_rest_and_counts_once tests/test_land.py::test_a_batch_with_checks_a_note_and_an_irreversible_path_lands_through_factory_alone
6 passed in 126.78s (0:02:06)
real 127.03
user 41.73
sys 69.14
exit: 0

$ uv run --group dev pytest -q -n 6 -p no:cacheprovider tests/test_retro.py tests/test_indicators.py tests/test_modules.py tests/test_windows.py tests/test_skills.py tests/test_feature_map.py tests/test_nothing_local.py tests/test_defaults.py
1021 passed in 108.84s (0:01:48)
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
327 files already formatted
exit: 0
