---
id: 048
slug: architecture-indicators
kind: plan
created: 2026-11-12
updated: 2026-11-12
---

# 048 — Architecture indicators for the retro loop · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/indicators.py` (new): the counting, pure functions over git's output text, loaded by path.
- `scripts/sdlc.py`: `_load_indicators()`, three `[retro]` keys (`KIND_LISTS`), `ARCH_LOOKBACK`
  (the lists' cap is `indicators.TOP`), `_kind()`, `_change_rows()` (the numstat `retro()` already
  ran, shared with the look-back), `_line_counts()`, `_architecture()`, per-change
  `added`/`deleted`/`by_kind` in `retro()`.
- `skills/retro/SKILL.md`: Step 0 describes `architecture`; the architecture pass cites it.
- `docs/REFERENCE.md`: the three keys, `retro.indicators` among commands run, the `architecture` fields.
- `guide/process.md`: the retro loop names the indicators.
- `AGENTS.md`: the map names `scripts/indicators.py`.
- `.sdlc/setup.json`: re-recorded (`sdlc.py record`).
- `tests/test_indicators.py` (new), `tests/test_retro.py`, `tests/test_windows.py`,
  `tests/test_config_resolution.py` (its pin of `config`'s `[retro]` gains the three keys).

## Work order

1. `scripts/indicators.py`: conventions (`is_test`, `is_doc`, `classify`), `numstat_rows`,
   `change_size`, `size_by_tier`, `grep_counts`, `hotspots`, `co_change` (pairs only from changes
   of at most `PAIR_FILES_MAX = 50` files), `largest`, `totals`. Test it in `tests/test_indicators.py`.
2. `scripts/sdlc.py`: loader; config keys (`test_paths`, `doc_paths` in `LIST_KEYS`, `indicators`
   in `COMMAND_LISTS`); `_kind(cfg)` from `risk_paths()` or the conventions; per-change size in
   `retro()`'s loop, keeping `files`/`lines` as they are; `_architecture()` (look-back of the last
   30 closed changes with numstat, `git grep -I -c ''` at the base branch and the last
   retrospective, `_evidence()` for `retro.indicators`); `architecture` in `retro()`'s output.
   Tests in `tests/test_retro.py`; `indicators.py` added to `tests/test_windows.py`.
3. `skills/retro/SKILL.md`, `docs/REFERENCE.md`, `guide/process.md`, `AGENTS.md`.
4. `sdlc.py record` from this worktree; `./check.sh`.

## Tests

- R1: `test_it_reports_every_key_and_writes_nothing` gains `architecture`; existing tests keep
  `files`/`lines`.
- R2: a change touching `src/a.py`, `tests/test_a.py`, `docs/a.md` → `added`, `deleted`, `by_kind`;
  `size_by_tier` medians per tier (unit).
- R3: each convention (unit); `test_paths`/`doc_paths` override through `.sdlc/config.toml` (retro).
- R4, R6: hotspot ranking, skip and `lines: None`; co-change empty at two, listed at three, a
  51-file change not paired (unit).
- R5: look-back reaches before the retrospective while `size` stays on the window (retro).
- R7, R8: `largest`/`totals` `then` from the retrospective commit, null without one (retro);
  `grep_counts` on a path holding `:` (unit).
- R9: `retro.indicators` runs with no product doc; unset, `host` is `[]` (retro).
- R10: a 200-file, 40-change fixture keeps `architecture` under 8 KB (retro).
- R11: `indicators.py` imports neither `subprocess` nor `sdlc` (unit, source scan).
- R12: `config` prints the keys; `sdlc.py drift` clean in the gate.
- R13: `tests/test_skills.py` invariants. Manual: read the retro skill's architecture pass.
- R14: manual: the docs name the keys and fields.
- Manual: `sdlc.py retro` in this repo prints `architecture` under 8000 bytes with `scripts/sdlc.py`
  among the top hotspots.

## Rollback

`git revert <sha>` undoes everything: the change is read-only output, three optional config keys
and docs. A host that set the new keys before a revert gets `drift` reporting them as keys the
plugin doesn't read; removing those lines from `.sdlc/config.toml` undoes that. Nothing is written
outside the repo.
