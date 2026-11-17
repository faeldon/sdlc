# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Timings, 2026-11-17, 18 cores

| Run | Tests | pytest | `./check.sh` |
| --- | --- | --- | --- |
| Before, serial, from the worktree | 1848 passed | 231.6 s | 3:54 |
| After, `-n auto`, from the worktree, `.sdlc/reports/` planted with a home path | 1849 passed | 43.0 s | 44.7 s |
| After, `-n auto`, a fresh clone with the diff applied (no `.venv`) | 1849 passed | 44.2 s | passed |
| Parallel suite alone, three runs | 1849 passed each | 37.2 s, 38.9 s, 44.6 s | |
| `-m portable`, serial / `-n auto` | 160 passed each | 36.3 s / 10.9 s | |

The one test more after is the new `test_an_ignored_file_is_not_read_but_an_untracked_one_is`. No
test failed in parallel in any run, so none needed fixing or marking serial. `-n auto` with no tests
collected still exits 5.

## The open questions, as built

- The scan lists files through `git ls-files --cached --others --exclude-standard`, so any ignored
  local output is skipped, not just `.sdlc/reports/`; `SKIP_DIRS` went with it, since git never
  lists `.git/` and `.gitignore` covers the caches. The worktree filter stays, for a repo that
  doesn't ignore `.claude/worktrees/`. Run over the main checkout, it reads 205 files and finds
  nothing.
- CI's Linux job runs `-n auto` too; the Windows job stays serial, as it was, and its run passes
  either way here.
- Shared state: the board tests pick a free port and bind it after (`_free_port()`), a small race
  in parallel that no run tripped.
- [x] `tests/test_board.py`'s `_free_port()` releases the port before `board.serve()` binds it; in
  parallel another worker could take it between. Serving on port 0 and reading the bound port back
  would close the window. → seed: 2026-11-17-14
- [x] Every gate's record, green or red, carries the machine's home path into the change folder,
  which the scan then reads, so the next gate is red on the record itself. `claude plugin validate`
  prints absolute paths on every run, under `-n auto` every pytest failure prints xdist's worker
  line, `[gwN] <platform> -- Python <version> <venv's absolute path>`, and `factory.py gate` copies
  the output's tail into `build/round-<N>.gate.md`. Round 1 hit it, along
  with this change's own report quoting a planted path; both were redacted by hand to
  `<path-to-clone>`, the attempt's `Verdict:`, `Build:` and `Exit:` lines untouched. A fix for any
  host: `factory.py gate` writes the checkout's root and the home directory as placeholders in
  the tail it records. → dropped: filed as bug 2026-11-17-13 by the review of 082-parallel-gate
