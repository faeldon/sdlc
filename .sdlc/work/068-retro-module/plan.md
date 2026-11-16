---
id: 068
slug: retro-module
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 068 — Move retro's history readers out of sdlc.py · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/retro.py` (new): retro's 37 names, the 5 constants only it reads, and the `indicators`
  loader, moved verbatim apart from an `sdlc.` prefix on each name that stays in `sdlc.py`.
- `scripts/sdlc.py`: loses those spans, and gains `_Names` and `_load_retro()` where
  `_load_indicators` stood. `main()` dispatches `retro` and `retro-commit` to the module.
- `tests/*.py`: `sdlc.<moved>` becomes `sdlc.retro.<moved>`, and the `EVIDENCE_*` patches target
  `sdlc.retro`.
- `tests/test_retro.py`: three new tests (R1/R7, R4, R5).
- `tests/test_sdlc.py`, `tests/test_work_folder.py`, `tests/test_skills.py`,
  `tests/test_windows.py`: the guards read `retro.py` too (R6).
- `AGENTS.md`: "Mechanism vs. judgment" and the Retrospectives paragraph (R9).
- `.sdlc/work/068-retro-module/checks.md` (new) and `notes.md` (new).

## Work order

1. A throwaway tool in the session's scratchpad, never committed, does the move by `ast`:
   - it takes each moved node's span, its comments above included;
   - it prefixes each Load of a name that stays in `sdlc.py` with `sdlc.`;
   - it prints each name a function binds itself, and each module-level read of an outside name,
     for a hand check;
   - it writes `retro.py` (docstring, `sdlc.py`'s imports, `sdlc = None`, then the blocks in
     order) and rewrites `sdlc.py`.
2. Hand fixes:
   - `_load_indicators()` loads `Path(__file__).with_name("indicators.py")`;
   - fix the printed names;
   - `ruff check --fix` and `ruff format` on `scripts/`.
3. Rewrite the tests' lookups, then run `test_retro`, `test_bugs` and `test_nits`.
4. Add the new tests and extend the guards.
5. Update `AGENTS.md`, and write `checks.md` and `notes.md`.
6. Run the acceptance check by hand, `wc -l scripts/sdlc.py`, then `./check.sh`.

## Tests

- R1, R7: `test_retro_lives_in_its_own_file`. Both files' ASTs: each moved name is defined in
  `retro.py` only, and `sdlc` has no attribute for a moved function.
- R2, R3: the existing status, release, retro, bugs and nits tests, unchanged but for their
  lookup. The `checks.md` acceptance check diffs `retro`, `retro --report` and `retro --metrics`
  against the merge base's script, run from a `git archive` copy.
- R4: `test_retro_reads_sdlcs_names_when_it_runs`. It monkeypatches `sdlc.last_retrospective` and
  sees `sdlc.retro.retro()` call it.
- R5: `test_retro_has_no_entry_point_of_its_own`, and the acceptance check's `uv run --script` from
  a copy.
- R6: the guards for `main`, the work path and `gh` are parametrized over both files, each with a
  planted find in `retro.py`'s text. The push guard reads both files. `test_windows.py`'s
  `SCRIPTS` lists `retro.py`.
- R8: `wc -l` and `./check.sh`.
- R9: reading the diff of `AGENTS.md`.

## Rollback

`git revert <sha>` puts the code back in `sdlc.py`. Nothing outside the plugin's repo changes:
hosts run the same commands, and no file the plugin writes changes shape.
