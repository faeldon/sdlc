I built the change and left it uncommitted for `/sdlc:ship`. `./check.sh` now takes 42.8 s instead of 3:54, with 1849 tests passed. It also passes with a `.sdlc/reports/` folder holding a home-directory path, which is what made it fail in the main checkout. I ran everything below again just now.

**Slices**
1. **The scan.**
   - `scanned()` in `tests/test_nothing_local.py` now gets its file list from `git ls-files -z --cached --others --exclude-standard`. That covers every tracked file and every untracked file that isn't ignored, so a new file is checked before its first commit and nothing git ignores is read.
   - I removed `SKIP_DIRS`: git never lists `.git/`, and `.gitignore` already covers the caches.
   - I kept the filter that skips `.claude/worktrees/`, for a repo that doesn't ignore that folder.
   - The tests that build a temporary folder now run `git init` in it first, through a new `_repo()` helper.
   - Run over the main checkout, the scan reads 205 files and finds nothing.
2. **Running in parallel.**
   - `pytest-xdist>=3` is in `pyproject.toml`'s `dev` group and in `uv.lock`. `sdlc.py`'s PEP 723 block is unchanged.
   - `check.sh` runs `pytest -q -n auto`. When no tests are collected it still exits 5, so the gate still fails.
   - CI's Linux job also runs `-n auto`. The Windows `-m portable` job is unchanged, and that run passes both serially and with `-n auto`.
   - No test failed in parallel, so none had to be fixed or marked serial. In the first round the parallel suite ran clean three times (37.2 s, 38.9 s, 44.6 s), and the gate passed in a fresh clone with the diff applied.
3. **Docs.** The gate's command lines in `AGENTS.md` and `docs/CONTRIBUTING.md` now show `-n auto`, and CONTRIBUTING says the tests run in parallel.

**Tests added:** `test_an_ignored_file_is_not_read_but_an_untracked_one_is`. It plants a home path in an ignored `.sdlc/reports/` file and another in a new untracked file, and passes only if just the untracked one is reported. Before the scan change it failed for that reason. **Acceptance checks:** three in `checks.md`, all passing:
- `check.sh` runs pytest with `-n auto`.
- xdist is in the `dev` group and `uv.lock`, but not in the script.
- CI's two pytest lines are as described above.

**Gate:** 1849 passed (1848 before the change, plus the new test). **plan.md** is new, because the Approach touches more than a couple of files, and the build followed it. **notes.md** has the before and after timings and how each open question was settled. It has one unticked line: `tests/test_board.py`'s `_free_port()` releases the port before the server binds it. In a parallel run another test could take the port in that gap; no run has hit it.

**Decisions**
- DECISION: [default] Run CI's Linux job with `-n auto` too, and leave Windows serial? Going ahead with that: the Linux runners have 2 to 4 cores, which still helps, and the Windows job passes either way.
- DECISION: [default] Scan through git rather than adding `.sdlc/reports` to the skip list? Going ahead with git, as the Approach says, because it covers any ignored local output, not just that folder.

## Evidence

$ ./check.sh   # before the change, serial (first round)
1848 passed in 231.63s (0:03:51)
./check.sh  90.85s user 105.48s system 83% cpu 3:54.24 total
exit: 0

$ ./check.sh   # after, with .sdlc/reports/cases-x/aggregate-result.json holding a planted home-directory path
All checks passed!
1849 passed in 41.39s
✔ Validation passed
✔ Validation passed
./check.sh  123.05s user 265.36s system 907% cpu 42.811 total
exit: 0

$ uv run --quiet --group dev pytest -q tests/test_nothing_local.py
8 passed in 0.32s
exit: 0

$ uv run --quiet --group dev pytest -q -n auto -k zzz_no_such_test
no tests ran in 4.14s
exit: 5

$ uv run --quiet --group dev pytest -q -m portable
160 passed, 1689 deselected in 33.41s
exit: 0

$ uv run --quiet --group dev pytest -q -m portable -n auto
160 passed in 7.08s
exit: 0

$ grep -q '^uv run --quiet --group dev pytest -q -n auto$' check.sh
exit: 0

$ grep -q '"pytest-xdist>=3",' pyproject.toml && grep -q '^name = "pytest-xdist"$' uv.lock && ! grep -q xdist scripts/sdlc.py
exit: 0

$ grep -q 'run: uv run --group dev pytest -q -n auto$' .github/workflows/check.yml && grep -q 'run: uv run --group dev pytest -q -m portable$' .github/workflows/check.yml
exit: 0

$ uv run --quiet --group dev python -I -c "...print(len(scanned(main)), forbidden(main, main/LOCAL))"
205 []
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0

I fixed the round-1 gate failure and the gate is green again: 1849 passed in 41.8 s.

**What failed:** `test_nothing_in_the_repo_is_forbidden`. The new scan reads this change's own folder, which will be committed, and it found a home-directory path in two files there:
- **My round-1 report** (`build/round-1.md`) quoted the path I'd planted in `.sdlc/reports/` (the `/Users/` shape). That is what the gate caught.
- **The gate's record** (`build/round-1.gate.md`) was carrying this machine's real home path. Under `-n auto`, every failing test prints a worker line ending in the venv's absolute path, and `factory.py gate` copies that output into the record. Left alone, the next gate would have failed on the record itself.

**The fix:** In both files I replaced the paths with placeholder text (`holding a planted home-directory path`, `<path-to-clone>`), and changed nothing else. The gate record's `Verdict:`, `Build:` and `Exit:` lines are untouched and still parse as before (FAIL, build `89f17e2274f353e3`, exit 1). I made no change to the code or to the gate's config. No home paths are left in the change folder, and this report contains none.

**notes.md** has a new unticked line: any failing parallel gate will write the machine's home path into its record again. The fix belongs in `factory.py gate`, which should replace the checkout's root and the home directory with placeholders in the output it saves. That works for any host but is outside this change.

**Decision**
- DECISION: [default] Is it acceptable to edit the factory's gate record by hand to remove a home path? Going ahead: the file ships in this public repo, and only the copied output changed, not the attempt's record lines. The lasting fix is the `factory.py gate` change in notes.md.

## Evidence

$ ./check.sh
All checks passed!
1849 passed in 40.38s
✔ Validation passed
✔ Validation passed
./check.sh  122.36s user 232.76s system 849% cpu 41.808 total
exit: 0

$ uv run --quiet --group dev pytest -q tests/test_nothing_local.py
8 passed in 0.71s
exit: 0

$ grep -rncE '<home-path patterns>' .sdlc/work/082-parallel-gate/ | grep -v ':0$'
exit: 1

$ uv run --quiet --group dev python -I -c "...print(read_gate(Path('.sdlc/work/082-parallel-gate'), 1))"
{'attempts': [{'verdict': 'FAIL', 'build': '89f17e2274f353e3', 'exit': '1'}], 'fails': 1}
exit: 0
