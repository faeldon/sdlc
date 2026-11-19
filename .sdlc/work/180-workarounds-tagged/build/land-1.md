All six conflicted files are resolved and the markers are gone. The four test files I ran (`test_modules.py`, `test_retro.py`, `test_skills.py`, `test_train.py`) pass. I didn't run the full gate.

Both sides added code at the same spot in each file, so I kept both everywhere:

- **`scripts/factory_records.py`**: 175's `CONFLICTS`, `LAND_TRAIN`, `TRAIN_GATE_RE` and `LAND_ACCEPT` stay. 180's `LAND_ASK_RE` follows them.
- **`docs/REFERENCE.md`**: 175's `pipeline` paragraph comes first, then 180's `simplicity.workarounds` paragraph. Neither is reworded.
- **`tests/test_modules.py`**:
  - The allowed-names set holds 175's `read_gate_attempts`, `resolved_files` and `pipeline_counts` plus 180's `ejections`, `land_asks` and `LAND_ASK_RE`.
  - `RECORD_FILES` holds `land-train.md` and `land-accept.md` from 175 and `.ask.md` from 180 (`ejections.jsonl` was already there).
- **`tests/test_retro.py`, `tests/test_skills.py`, `tests/test_train.py`**: the new tests from both sides are all kept, 175's first, then 180's. I ran `ruff format` on these three to fix blank lines at the joins. It only changed spacing.

I dropped nothing from either spec.

I didn't check that 175's `pipeline` and 180's `simplicity`/`overrides` code in `scripts/retro.py` fit together. Git merged that file without conflict, and no test I ran failed on it.

`.sdlc/work/180-workarounds-tagged/runs/resolver.sessions` is a new file in the worktree that isn't mine. It's presumably the harness's record of this session, so I left it alone.

## Evidence

$ uv run --group dev ruff check tests scripts
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
346 files already formatted
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_modules.py tests/test_retro.py tests/test_skills.py tests/test_train.py
712 passed, 1 skipped in 79.13s (0:01:19)
exit: 0

(The pytest run was before the format-only change to the three test files. `ruff format --check .` was run after it.)
