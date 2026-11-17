---
id: 075
slug: factory-dashboard
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 075 — A dashboard of every open change, and UI and UX reviewers · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

**Core**

- `scripts/board.py` (new): loaded by path like `retro.py` (`_load_retro()`), bound
  `mod.sdlc = _Names(globals())`, but lazily through `_load_board()` in `board`'s dispatch, so no
  other command loads it (R1). `state(root)` over `change_dirs(root)`'s open changes: the
  `load_change()` record plus `unfilled` (`is_unfilled`), `undone` (`open_items`), findings by
  disposition (`findings_entries`), checks count (`acceptance`), `behind` (`behind_trunk`),
  `touched_ago` (`last_touched`, as `main()` does for status), `files`, `mode`, `next`
  (`next_action()`: plan T1 → plan mode, plan T2 → `/sdlc:spec`, design → plan mode, build →
  build then `/sdlc:ship`, test → `/sdlc:ship`, factory READY → `/sdlc:ship` or
  `/sdlc-factory:land`), `issue` (built from `origin`'s GitHub URL and the id only when
  `ids_mode()` is `github`: nothing records it, and no network call), `problems` (each reader
  wrapped, R6), and a `"board": "sdlc"` marker. Factory readers (R5): copies of `VERDICT_RE`,
  `CHANGE_RE`, `KEPT_RE`, `DROPPED_RE`, `DECISION_RE`, `LEDGER_RE`, and `_cost()` over 074's
  `runs/costs.jsonl`. Server: `ThreadingHTTPServer` on `127.0.0.1`, three GET routes, 405 for any
  other method, 404 otherwise (R2); `/file` resolved inside a listed change's folder (R3); a busy
  port probed for the marker (R1). `cmd_board(root, port)`.
- `scripts/board.html` (new): one self-contained file, light and dark tokens, columns per R7,
  chips, drawer, 2s poll, DOM built with `textContent` only (R8).
- `scripts/sdlc.py`: `board` subparser (`--port`, default 5170) and its dispatch. Not in
  `READ_ONLY`, `ALLOW_RULES` or `OWN_SCRIPT_CMDS`.
- `skills/dashboard/SKILL.md` (new, R10): runs `config`, starts `board` in the background, prints
  the URL and how it stops. No WAIT.
- `README.md`, `docs/REFERENCE.md`: `/sdlc:dashboard`.

**Factory**

- `plugins/factory/scripts/factory.py`: `REVIEWERS`, `ROLES` and `SCALED` gain `ui` and `ux`
  (`UI_REVIEWERS`), `DEFAULTS["reviewers"]` unchanged; `_ui(root)` from `_base_factory()` with
  defaults and warnings, `DEFAULTS["ui"]` (R11); `_rounds_at_depth()` adds `ui`, `ux` when `[ui]`
  is complete and the diff touches its `paths` or a round already ran them, and `depth()`'s
  `beyond` leaves them out (R12); a pinned `_sh()` copy; `shots()` and `cmd_shots` (R14), the
  reports folder's ignore logic factored out of `cmd_report_dir` into `_reports()`; `cmd_agent`
  takes the shots before a `review` or `land-review` by `ui`/`ux` and refuses on failure (R15);
  `max_runs()` counts the two with `[ui]` complete, and `cmd_start` emits `ui` (R17); a `shots`
  subparser.
- `plugins/factory/agents/reviewer-ui.md`, `reviewer-ux.md` (new, R16): `tools: Read, Grep, Glob`.
- `plugins/factory/skills/build/SKILL.md`: Step 1 shows `[ui]`; both WAIT questions gain the UI
  clause, left out without `[ui]` (R17).
- `plugins/factory/README.md`: the agents table, `[ui]` with a Playwright example,
  `.sdlc/reports/shots/`.
- `.sdlc/factory.toml` (new, R19): `[ui]` only.

**Tests**

- `tests/test_board.py` (new).
- `tests/test_factory.py`, `tests/test_land.py` (compare with `DEFAULTS["reviewers"]`, not
  `REVIEWERS`), `tests/test_skills.py` (`dashboard` in `test_skills_were_found`, `AGENT_TOOLS` for
  the two agents), `tests/test_windows.py` (pin `_sh`), close's tests (R18).

## Work order

1. Factory core: `REVIEWERS`/`ROLES`/`SCALED`, `_ui()`, joining in `_rounds_at_depth()`,
   `depth()`'s `beyond`, `max_runs()`; their tests, and `test_land.py`'s fix.
2. `_sh()` copy and pin; `_reports()`; `shots()` and `cmd_shots` with the fake server and
   shooter; then `cmd_agent`'s shots and refusal.
3. The two agents, `AGENT_TOOLS`, the build skill's Step 1 and WAIT clause, the factory README,
   R18's test.
4. `board.py` state and factory readers, with the by-hand and factory fixtures and the regex pins.
5. The server, its routes and `/file` safety, the busy port, `git status` unchanged.
6. `board.html`, the `innerHTML` test.
7. `sdlc.py`'s subparser, `/sdlc:dashboard`, `test_skills_were_found`, README, REFERENCE.
8. `.sdlc/factory.toml`; `./check.sh`; the manual checks below.

## Tests

- R1: board starts on a free port and serves `/`; busy by a board → URL, exit 0; busy by another
  listener → refused naming the port; `status` doesn't load `board.py`.
- R2: each route answers; POST → 405; unknown path → 404.
- R3: `..`, absolute, symlink out, unknown change, outside the folder → 404 each.
- R4: a T1 and a T2 change by hand: every field, `mode: manual`, `next`.
- R5: the factory fixture (round 1 CHANGES, round 2 PASS, READY, an open blocking decision, no
  cost): rounds, decision, pending, `cost: null`; with a `costs.jsonl`, the sums; each regex copy
  equal to `factory.py`'s.
- R6: a review with no verdict line → the entry with a `problems` line.
- R7, R8: `board.html` has no external `src`/`href` and no `innerHTML` taking data. Manual: the
  columns and drawer by eye.
- R9: serve fixture worktrees, hit every route, `git status --porcelain` unchanged.
- R10: `test_skills.py`'s skill invariants over `skills/dashboard`.
- R11: no `[ui]` → `verdicts` as today; a bad key and a differing checkout warn.
- R12: a UI path joins `ui`, `ux` at light and full; a later round without the path keeps them; a
  light run with UI reviews stays light.
- R13: `model_for("ui"|"ux")` at T1 light, T2, and with `factory.models`.
- R14: fake server and shooter: PNGs and `shots.json`; the port free afterwards; the server
  stopped when the shooter fails and when the server never answers; a rerun reuses good shots.
- R15: a failed shot → `agent` refuses with the tail, no `ui.md`.
- R16: `AGENT_TOOLS` pins `Read, Grep, Glob`.
- R17: `max_runs` with `[ui]`; the WAIT text holds the clause and keeps its 2–4 answers.
- R18: `_agent_sessions()` maps `reviewer-ui`/`reviewer-ux` sessions.
- R19, R20: `./check.sh` green. Manual: `factory.py shots 075 --round 1` with this repo's `[ui]`
  (needs `uvx` and `playwright install chromium`): two PNGs and `shots.json`, and
  `lsof -iTCP:<port>` empty afterwards; `sdlc.py board --port 5199` from the main checkout shows
  the open changes in their columns, opens their files, refuses a POST and a `../` path.

## Rollback

`git revert <sha>` undoes all of it. It does not stop a board left running in a session (stop its
background task, or end the session) or delete screenshots already under `.sdlc/reports/shots/`,
which ignores itself (`rm -rf .sdlc/reports/shots`). A host that set `[ui]` in its
`factory.toml` keeps the table, which a reverted factory warns about as an unknown key until it is
removed.
