---
id: 075
slug: factory-dashboard
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 075 — A dashboard of every open change, and UI and UX reviewers · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

**The board (core `sdlc`)**

1. `sdlc.py board [--port N]` serves on `127.0.0.1` only, port 5170 by default. A port held by a
   board already: print its URL, exit 0. Held by anything else: refuse, naming the port. The code
   is `scripts/board.py`, loaded by path as `retro.py` is, only when `board` runs; `status` and
   every other command load nothing new. A test starts it on a free port and reads `/`.
2. Three GETs and nothing else: `/` (the page), `/state.json` (rebuilt each request),
   `/file?change=<NNN-slug>&path=<rel>` (one file of that change's folder, as text). Anything else
   is 404 or 405; a test asserts a POST is refused.
3. `/file` serves only a regular file inside a listed change's folder: `..`, an absolute path, a
   symlink leading out, an unknown change, or a file outside `.sdlc/work/<change>/` is 404. A test
   tries each.
4. `/state.json` lists every open change `change_dirs()` finds (the set `status` lists), through
   `load_change()`, `is_unfilled()`, `open_items()`, `findings_entries()`, `acceptance()`,
   `open_questions()` and `behind_trunk()`: `id`, `slug`, `title`, `tier`, `stage`, `serves`,
   `depends_on`, `artifacts` (with which are unfilled), open questions, undone notes, findings by
   disposition, checks count, `behind`, `touched_ago`, the issue URL when recorded, `files` (the
   folder's relative paths), `mode` (`factory` when the folder has `runs/`, else `manual`), and
   `next`, the command a person runs next, from tier and stage as `new` and `status` word it. A
   test builds a Tier 1 and a Tier 2 change by hand and asserts each field.
5. A factory change's entry adds `rounds` (each reviewer's verdict and its count of `CHANGE:`
   lines, the verifier's kept and dropped counts, the builder reports), `decision` (READY or
   ESCALATE), `pending` and `assumed` (unticked blocking and default lines in `decisions.md`), and
   `cost` (`usd`, `by_role`, `by_model`, `duration_ms`, `unknown` from 074's `runs/costs.jsonl`, or
   null without one). Core reads these with copies of `factory.py`'s parsing (`VERDICT_RE`,
   `CHANGE_RE`, `KEPT_RE`, `DROPPED_RE`, `DECISION_RE`, `LEDGER_RE`, the `costs.jsonl` line shape),
   each pinned to the factory's by a test, as the factory's copies of `sdlc.py` are. A fixture
   holds round 1 CHANGES, round 2 PASS, READY, one open blocking decision and no cost.
6. A malformed file never breaks the board: the change still gets an entry, and its `problems` say
   which file couldn't be read. A fixture covers it.
7. The page, `scripts/board.html`, is self-contained (no external script, font or stylesheet),
   polls `/state.json` every 2s, and places each card in a column: Plan, Design, Build, Test (by
   stage); **Ready to ship** (stage `test` with READY); **Needs you** (a pending blocking decision,
   ESCALATE, or `problems`). Each card shows id, title, tier, a manual or factory badge, its
   artifacts, open questions, undone notes, findings, behind-main and touched-ago, the `next`
   command, and for factory changes the round chips, decisions and cost labelled API-equivalent
   ("—" without it). A click opens a drawer of its files; a file click shows its text.
8. The page never sets `innerHTML` from state or file text: it builds with `textContent` and DOM
   nodes, and a test checks `board.html` for it.
9. The board writes nothing; a test serves fixture worktrees and asserts `git status` unchanged.
10. `/sdlc:dashboard` runs `sdlc.py config`, starts `sdlc.py board` in the background, prints its
    URL and says it stops when its background task does or the session ends. No WAIT, not in
    `GATED`; `test_skills_were_found` lists it; it holds the skill invariants. Its
    `allowed-tools` grants `board`, which stays out of `READ_ONLY` and `ALLOW_RULES`, so no host's
    settings change and no model starts a server unasked. README and `docs/REFERENCE.md` name it.

**The UI and UX reviewers (the factory)**

11. `factory.toml`'s `[ui]`, read from the base branch's copy as `mode` is: `serve` (with
    `{port}`), `url` (default `http://127.0.0.1:{port}`), `pages` (`["/"]`), `paths` (UI globs),
    `shoot` (with `{url}`, `{width}`, `{height}`, `{out}`), `widths` (`[[1280, 800], [390, 844]]`),
    `timeout` (60). Unset `serve`, `shoot` or `paths`: no UI review, and a test shows `verdicts`
    unchanged. A bad key, or a checkout's `[ui]` differing from the base branch's, warns as `mode`
    does.
12. `ui` and `ux` join a round, at either depth, once `[ui]` is complete and the diff touches a
    `paths` glob (`risk_paths()`); a round that ran them keeps them in later rounds; `depth()`
    ignores them, so a light run stays light. Each case has a test.
13. `ui` and `ux` are in `SCALED`; `factory.models` overrides them.
14. `factory.py shots <NNN> --round N` picks a free port, starts `serve` through the pinned
    `_sh()` copy in its own process group, waits up to `timeout` for the port, runs `shoot` once
    per page and width (each with a timeout), stops only the group it started on every path out,
    and writes PNGs and `shots.json` (each command, exit, output tail) to
    `<worktree>/.sdlc/reports/shots/<NNN-slug>/round-<N>/`. A rerun of the round reuses the shots
    that succeeded. Tests use a fake server and a fake shooter in Python.
15. `agent --task review --role ui|ux` takes the shots first and names them in the prompt with the
    changed paths. Failed shots: it refuses with their tail and files nothing. A UI review never
    runs blind.
16. `agents/reviewer-ui.md` (looks: theme fit, spacing, contrast, overflow at phone width) and
    `agents/reviewer-ux.md` (flow: what the person sees and does, empty, error and loading states,
    labels): `tools: Read, Grep, Glob` only, the existing verdict shape, filed as
    `reviews/round-N/ui.md` and `ux.md`. The verifier, `settled` and `carry` treat them like any
    reviewer.
17. Build's WAIT names the UI review when the base branch's `[ui]` is complete ("and, on a diff
    touching `<paths>`, the ui and ux reviewers, which start `<serve>`"); without `[ui]` it is
    unchanged. `max_runs()` counts the two.
18. `sdlc.py`'s `_agent_sessions()` attributes `runs/reviewer-ui.sessions` and
    `runs/reviewer-ux.sessions` at close; a test pins it.

**This repo**

19. `.sdlc/factory.toml` gets `[ui]`: `serve = "uv run --quiet --script scripts/sdlc.py board --port
    {port}"`, `paths = ["scripts/board.html", "scripts/board.py"]`, and a `shoot` running
    Playwright's screenshot through `uvx`. Live once on `main`, so the board is the reviewers' first
    subject.
20. README, REFERENCE and the factory README document the board, `[ui]` (with its Playwright
    example), the reviewers and `.sdlc/reports/shots/`. `./check.sh` passes.

## Design

**The board.** `board.py` holds a stdlib `ThreadingHTTPServer`, and `state(home)` calls `sdlc.<name>`
helpers through the live binding `retro.py` uses, so a test's stand-ins reach it. The factory
readers are a dozen lines of regex over files, beside their pinning test. Core can't compute the
factory's next step or depth (`loop_state()` needs the factory's config), so a factory card places
itself by stage, decision and pending, and shows chips for what its rounds hold. The page is read at
request time, so an edit to it is live on reload.

**The factory half.** `_ui()` is read like `_mode()`. `ui_review()` decides whether `ui` and `ux`
join, and `_rounds_at_depth()` adds them. `REVIEWERS` and `ROLES` gain `ui` and `ux`; `depth()`'s
`beyond` check leaves them out. `shots` runs `Popen` with `start_new_session` and stops the group
with `killpg`, or on Windows with `CREATE_NEW_PROCESS_GROUP` and `taskkill /T /F /PID <own pid>`,
and checks readiness with a TCP connect. `agent` calls `shots` before `_claude()`, so the build
skill gains no step and no rule.

## Contracts touched

- **Mechanism vs. policy:** no browser or dev server is named in code; both are host commands in
  `[ui]`, unset by default.
- **The core knows nothing of the factory's code:** it reads the files a run leaves, as ship
  already does, through pinned copies, and never imports or runs `factory.py`.
- **Light footprint (O5):** `board.py` loads only for `board`; nothing is added to `READ_ONLY` or a
  host's settings; setup writes nothing new.
- **Something run unasked (always Tier 2):** the board starts only from the person's skill call, on
  localhost; the dev server only from the base branch's `[ui]`, after build's WAIT names it; the
  reviewers have no Bash.
- **A WAIT's meaning:** build's question gains a clause, only with `[ui]` set. Flagged.
- **Agents that judge have no Write;** `checks.md` stays the builder's and `accept`'s; shots go
  under `.sdlc/reports/`, which ignores itself, so none reaches a commit.
- **Windows:** local imports, `encoding="utf-8"`, `newline="\n"`; the board, `/file` and state
  tests are `portable`.
- **Unchanged:** the verdict shape and `runs/<role>.sessions`.

## Alternatives rejected

- **The board in the factory:** hosts without it get nothing, and by-hand changes would be
  second-class. Chosen core.
- **Core calling `factory.py` for next step and depth:** inverts the plugins' independence; the
  factory's cache may not be there.
- **A static page:** stale between steps; chosen live.
- **Serving the worktrees' file tree:** exposes everything; three routes over change folders expose
  only what the board reads.
- **Reviewers that drive a browser themselves:** untestable without a model, and an agent killing
  processes.
- **Shots in the change folder:** ship would commit PNGs.
- **Land state on cards:** `land-check`'s verdict, not a file. Deferred.

## Verification

- `uv run --group dev pytest -q`: board state for by-hand and factory fixtures, routes and `/file`
  safety, the pinned copies, `[ui]` defaults and joining, `shots` with fakes, the refusal on failed
  shots, `_agent_sessions()`. `./check.sh` green.
- By hand: `/sdlc:dashboard` from the main checkout, open `http://127.0.0.1:5170`: today's open
  changes in their stage columns with their next commands, files opening. `factory.py shots 075
  --round 1` with this repo's `[ui]`: two PNGs and `shots.json`, and `lsof -iTCP:<port>` empty
  afterwards.
