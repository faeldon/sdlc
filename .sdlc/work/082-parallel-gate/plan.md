---
id: 082
slug: parallel-gate
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 082 — Run the gate's tests in parallel, and let it pass in the main checkout · plan

> The plan for a Tier 1 change whose Approach touches more than a couple of files, written after
> reading `check.sh`, `pyproject.toml`, `.github/workflows/check.yml` and
> `tests/test_nothing_local.py`.

## Files to change

- `tests/test_nothing_local.py`: `scanned()` lists files through
  `git ls-files -z --cached --others --exclude-standard` (what could reach GitHub), filtered by
  suffix and on-disk existence as now; `SKIP_DIRS` goes, since git never lists `.git/` and
  `.gitignore` covers the caches. The `WORKTREES` filter stays: an unregistered copy under
  `.claude/worktrees/` in a repo that doesn't ignore it still isn't scanned. The `tmp_path` tests
  `git init` their folder first (a `_repo()` helper), and one new test proves an ignored file is
  not read while an untracked, unignored one is.
- `pyproject.toml`: `pytest-xdist>=3` in the `dev` group (a test dependency only: the PEP 723
  block of `sdlc.py` is unchanged).
- `uv.lock`: `uv lock`.
- `check.sh`: the pytest line becomes `pytest -q -n auto`; the exit-5 comment stays true, since
  xdist keeps pytest's exit codes.
- `.github/workflows/check.yml`: the Linux job's pytest gets `-n auto` (runners have 2 to 4 cores,
  which still helps); the Windows job is left serial (`-m portable`), its run works either way.
- `AGENTS.md`, `docs/CONTRIBUTING.md`: the "tests only" command lines gain `-n auto`.
- `.sdlc/work/082-parallel-gate/notes.md` (new): the before/after timings and the flake runs.

## Work order

1. The scan through git: red test (ignored file read today), then `scanned()`, then the existing
   `tmp_path` tests on a `git init` folder. Gate green, serially.
2. Parallel: add xdist, lock, `-n auto` in `check.sh` and CI's Linux job; run the suite in
   parallel three times, fix any test that fails only in parallel.
3. Docs' command lines; time `./check.sh` from the worktree and the main checkout's state
   (a `.sdlc/reports/` holding a home path), record in `notes.md`.

## Tests

- Outcome 3 (passes with `.sdlc/reports/` holding results; reads every file that could reach
  GitHub, nothing ignored): `test_an_ignored_file_is_not_read_but_an_untracked_one_is`, plus
  the existing planted tests and `test_the_scan_reads_the_plugin`.
- Outcome 1, 2, 4 (parallel, same results, xdist locked): `./check.sh` itself, run three times in
  parallel with the same pass count as the serial run; the `-n auto` line in `check.sh` and the
  dependency are acceptance checks in `checks.md`, since only a revert removes them.
- Outcome 5 (CI): `uv run --group dev pytest -q -m portable` run with and without `-n auto` here;
  CI itself runs on the push close makes.

## Rollback

`git revert` undoes all of it; nothing is written outside the repo. The lock change leaves
`pytest-xdist` in uv's cache, which is harmless.
