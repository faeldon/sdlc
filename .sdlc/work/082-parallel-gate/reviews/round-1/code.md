I'm finishing the review. The gate record in the change folder fails the scan again, so I'm writing the verdict now.

VERDICT: CHANGES

- CHANGE: .sdlc/work/082-parallel-gate/build/round-1.gate.md:104: The gate record again holds the machine's home path, at lines 104, 106, 122 and 124. These are `claude plugin validate` output from Attempt 1. The record was redacted by hand earlier, but it is back in this tree. As a result `tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden` fails here, with 4 extra hits, and the file would reach GitHub on commit. The fix is to replace the worktree path with `<path-to-clone>` in those lines and leave the `Verdict:`, `Build:` and `Exit:` lines alone. Then rerun the scan test. Check why the redaction was lost, for example a gate rerun that rewrote the file. If a rerun did it, the unticked `factory.py gate` fix in notes.md is what stops it recurring. That fix is worth doing, or filing as a seed, before the next gate run.

## Notes

- **Requirements:** every outcome has code behind it. `-n auto` is in `check.sh`, the CI Linux job and both docs. `pytest-xdist>=3` is in `pyproject.toml` and locked in `uv.lock`. `scanned()` now lists files through git, which covers tracked and untracked-not-ignored files. The new `test_an_ignored_file_is_not_read_but_an_untracked_one_is` would fail under the old `rglob` scan, so it does check the change.
- **Optional:** `docs/CONTRIBUTING.md` now has a long line after the wording edit, "…none depends on running alone or in order. `pyproject.toml` only gives the tests an…". Rewrap it.
- **Optional:** `test_board.py`'s `_free_port()` race is already recorded unticked in notes.md, and ship will dispose of it. I did not review it further.
- **Optional:** `scanned()` calls `git ls-files` with `check=True` and no handling. Outside a git repo it raises a bare `CalledProcessError`. That is acceptable for a test helper, since the tests `git init` first.
- **Done well:** the plan is followed closely. The scan keeps the worktree filter. Dropping `SKIP_DIRS` is justified because git never lists `.git/` and `.gitignore` covers the caches. The timings, the three parallel runs and the clean-clone check are recorded. The acceptance checks are narrow and sensible.
- **Ran:** `pytest tests/test_nothing_local.py` gave 7 passed and 1 failed (the gate-record hits above). `ruff check` and `ruff format --check` were clean. I confirmed the `pytest-xdist` entries in `uv.lock`. I did not run the full suite or `check.sh`, because the scan test already fails.
