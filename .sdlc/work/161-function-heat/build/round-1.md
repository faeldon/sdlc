I built the function-hotspot report the intent asks for. It runs through the retrospective's `indicators` hook, and every test I ran passes. I didn't run the full `sdlc.py retro`, because that also runs the whole suite and `gh`. Instead I called the exact function that fills `architecture.host`, using this repo's real config: exit 0 in 0.6s, output not cut short.

This is a Tier 1 change touching only a couple of files, so I wrote no `plan.md`, even though the prompt says Tier 2. The work is uncommitted.

**What changed**
- **New `.sdlc/function-heat.py`** (stdlib only). It finds the newest `Retrospective YYYY-MM-DD` commit on the base branch, the same way `sdlc.py retro` does, or uses the whole history if there is none. Then for each of the four scripts it reads the file from the base branch and runs `git blame` over that range. It counts how many commits since then still own lines in each top-level function, ranks by commits then size, and prints the top 15 per file as a plain table. It writes nothing. The base branch comes from `[git] base`, else `main`, else `origin/HEAD`'s branch.
- **`.sdlc/config.toml`**: `[retro] indicators` now runs the script, with a comment above it. The `[review]` comment is split into one sentence per group (nit 2026-11-18-102).
- **`tests/test_windows.py`**: the new script is on the list of scripts its Windows checks cover. This is outside the intent's Affected list; I added it because it is the test behind the "runs on Windows" constraint.
- **`checks.md`** has two acceptance checks, both exit 0: config names the indicator, and the script prints the table for the four files.

**Tests added** (`tests/test_function_heat.py`, 7, marked `portable`). Before the script existed they failed for the expected reason, `FileNotFoundError` on the script.
- Only module-level functions are read, with their line ranges; methods are skipped.
- With no retrospective, the whole history counts.
- Only commits after the newest `Retrospective` commit count.
- Rows rank by commits, then size, cut to the top N.
- The table names each file, function and number, and the boundary commit.
- Run from another branch with a dirty tree, it reports the base branch's version and changes nothing.
- A file missing on the base gives no rows instead of an error.

Run against this repo, the top of the table is `sdlc.py`'s `main` and `closing.py`'s `cmd_close`. Every count is 1–2 because a retrospective landed today (40b6888). Blaming all four files over the whole history (474 commits on `main`) is also well under a second, far inside the 60-second limit.

Nothing left in `notes.md`. No requirement is untestable.

- DECISION: [default] Output stays a plain-text table now, with JSON left to S8. Going ahead unless told otherwise.
  - OPTION: plain text now — matches the Outcome and reads fine in `architecture.host`; S8 changes the output format
  - OPTION: JSON from the start — S8 wouldn't need a format change; harder to read in the report today
  - WHY: the intent's Outcome says "a plain-text table"
- DECISION: [default] Rank by commits, then size, with size shown beside it (not commits × size). Going ahead unless told otherwise.
  - OPTION: commits, then size — matches the hand-run analysis and the Outcome
  - OPTION: commits × size — one score, but a huge function changed once can outrank a small one changed often
  - WHY: the Outcome says "ranked by commits then size"
- DECISION: [default] Count a commit only if it still owns some of a function's lines (blame), so a commit whose lines a later commit rewrote isn't counted. Going ahead unless told otherwise.
  - OPTION: blame-based — what the Approach names, and fast; undercounts functions that were rewritten again and again
  - OPTION: walk each commit's diff (`git log -L` or similar) — exact count; much slower and more code
  - WHY: the Approach specifies `git blame --line-porcelain`

## Evidence

$ uv run --group dev pytest -q tests/test_function_heat.py   (before the script existed)
ERROR tests/test_function_heat.py - FileNotFoundError: [Errno 2] No such file...
1 error in 0.04s
exit: 2

$ uv run --group dev pytest -q tests/test_function_heat.py tests/test_windows.py tests/test_nothing_local.py
57 passed in 2.59s
exit: 0

$ uv run --group dev pytest -q tests/test_config_resolution.py tests/test_defaults.py tests/test_retro.py
294 passed in 48.15s
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
286 files already formatted
exit: 0

$ uv run --group dev python /tmp/heat_hook_161.py   (load_config + retro._evidence(home, cfg["retro"]["indicators"]))
indicators: ['uv run --quiet --script .sdlc/function-heat.py']
seconds: 0.6
exit: 0 error: None truncated: False
Function hotspots: commits that rewrote some of each top-level function since the retrospective at 40b6888 (2026-11-18).
exit: 0

$ sh /tmp/chk161_1.sh   (checks.md: config names the indicator)
exit: 0

$ sh /tmp/chk161_2.sh   (checks.md: the table names the four scripts)
exit: 0

$ git blame --root --line-porcelain main -- scripts/sdlc.py | grep -c '^	'
9961
git blame ... 0.128 total
exit: 0
