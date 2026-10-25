---
id: 024
slug: bugs-register
kind: spec
created: 2026-10-25
updated: 2026-10-25
---

# 024 — One inbox for seeds, bugs and nits · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

**The inbox**

1. `work/inbox.md` is the one register of change requests. Each entry is
   `## [<id>] [<tag>] <title>`, a short description, then body lines written as `After:` is. Tags:
   `seed`, `building`, `bug`, `nit`. Body lines: any entry `After:`; a bug `Severity:`, `Paths:`,
   `Introduced by: <NNN-slug>`; a nit `Theme:`, `Paths:`, `Cost:`, `Value:`,
   `Raised by: <NNN-slug> (<pass>)` (the raising change's number, which the old `NNN-n` id carried).
   Read as text, fenced lines skipped. `templates/inbox.md` replaces `templates/ideas.md` and
   `templates/nits.md` in `DOC_TEMPLATES` and passes the shape test.
2. `work/ideas.md` is a shim: with no `work/inbox.md`, every reader reads it in its place, and the
   same for a host override at `.sdlc/templates/ideas.md`. An entry in `.sdlc/deprecations.toml`,
   `remove_in = "2.0.0"`, with its test. With both files present, `check` reports it and
   `work/inbox.md` is read. `work/nits.md` gets no shim: it was never released.
3. `sdlc.py migrate-inbox` (writes, never commits, not in `READ_ONLY`) `git mv`s `work/ideas.md` to
   `work/inbox.md` (history follows), gives each bare-date entry an id (R5), turns each
   `work/nits.md` entry into a `[nit]` entry dated by its `raised` and removes `work/nits.md`, and
   rewrites the references naming an open entry to ids (`After:`, the direction doc's `Groups:`,
   this checkout's open changes' `idea:`). It refuses while any of those files is dirty; a rerun
   changes nothing. `/sdlc:setup` offers it behind setup's WAIT; this change runs it on this repo.
   Tests: seeds, one `After:`, one `Groups:` and two nits become the expected inbox; a rerun is a
   no-op; a shipped title is left.
4. `retro-commit` takes `work/inbox.md` (or `work/ideas.md` while the shim reads it). `release`,
   `publish` and measuring never read the inbox; tests pin it, as they did for nits.

**Ids and references**

5. Every entry's id is `YYYY-MM-DD-n`: `n` one past the highest for that date across the inbox in
   the main checkout and in each open change's worktree (its own `work/`, uncommitted included), and
   every commit on any branch (`git log --all -p --since=<date>` over the register's paths), so an
   id deleted the same day is never handed out again. `sdlc.py next-entry [--count N]` (read-only,
   in `READ_ONLY`). Every skill writing an entry (`/sdlc:bug`, ship's seeds and nits, retro's seeds)
   takes ids from it after its `base`. Tests: another worktree's id skipped, a same-day deleted id
   skipped, a new date starts at 1.
6. `check` reports an id used twice.
7. A reference is an id or a title, by shape, in `idea:`, `fixes:`, `After:` and `Groups:`: an
   unquoted `YYYY-MM-DD-n` is an id, a quoted string a title, a bare `006` a change id (on
   `Groups:` lines entry ids are taken first, so `2026` is never read as one). Ids match ids, titles
   match titles; title references are read for good, since shipped intents in history carry them
   (permanent reading, not a shim). `idea:` stays the released key, meaning the entry a change came
   from, of any kind. Tests for each form in `_seed_lines`, the orphan check, Next up's building set
   and `After:` waits, and the milestone verdicts.
8. Next up's commands are `/sdlc:intent <id>`, or by title for an entry without one.

**Nits as entries**

9. `[nit]` entries replace `work/nits.md`: `nits [--touching|--change]` reads them, keeping its JSON
   shape with `id` now the entry id; `nits_summary`, Next up's `nits` rule and retro's `nits` read
   them; `check` reports a nit missing `Theme:`, `Paths:` or `Raised by:`, or with `Cost:`/`Value:`
   outside the process doc's rubric. Ship writes new nits as entries with ids, and its `Retired
   nits:` paragraph lists ids. `tests/test_nits.py` is ported.

**Bugs**

10. Severity words come from the process doc's `- **severity:**` bullet in its section headed
    `Bugs…`, most severe first; from the host's doc, else `defaults/SDLC.md`'s (`high` · `med` ·
    `low`). `check` reports a `[bug]` with no `Severity:` or one outside the list, and an
    `Introduced by:` naming no change. Tests: a host's `critical, minor` sorts so; a doc without the
    bullet sorts by the default.
11. `sdlc.py bugs` (read-only, in `READ_ONLY`): open bugs as JSON with age and problems;
    `--touching <path>…`; `--introduced <path>…` lists the closed changes that last touched those
    paths.
12. A new `/sdlc:bug` skill, from the main checkout behind one WAIT, files, retires or retags an
    entry. Filing takes its id from `next-entry` and a severity from the list, offers the
    `--introduced` candidates and writes `Introduced by:` only when the person confirms one, and
    words it so it names no host. Retiring takes `duplicate` · `not-a-bug` · `wontfix` ·
    `cant-reproduce`. Retagging turns a seed into a bug or back, keeping the id. It never pushes,
    and joins the writing-skills test list and `AGENTS.md`.
13. `sdlc.py bug-commit` (not read-only) commits only the inbox, on the base branch in the main
    checkout, as `File <id>`, `Retire <id>` or `Update <id>`, with
    `Sdlc-Retired: <id> severity=<w> reported=<date> reason=<word>` per retired bug. It makes
    `cmd_retro_commit`'s refusals, plus a removed entry without `--reason <id>=<word>`. Tests for
    each refusal and subject.
14. `status` prints `■ Bugs` (open by severity, oldest age); Next up's `bug` rule sorts by severity
    rank, then date.

**The fix cycle**

15. `/sdlc:intent <id>` on a `[bug]` writes `fixes: [<id>]` and pre-fills the Problem from the
    entry. `fixes:` is read with `frontmatter_list()`. `check` reports an open change whose `fixes:`
    names no `[bug]` in its own checkout's inbox. Status leaves out bugs named by an open change's
    `fixes:`.
16. `sdlc.py ship` deletes the `idea:` entry and each `fixes:` entry, re-finding lines after each
    deletion, so every other entry stays byte for byte; an id with no entry is reported, never
    refused. Ship's WAIT names them.
17. `/sdlc:close` writes `Sdlc-Fixes: <id> severity=<w> reported=<date>
    introduced_by=<NNN-slug|unknown>` per `fixes:` id, its fields from the newest commit on the
    branch whose inbox held the entry, else `unknown`; it never refuses over this, and a dropped
    change writes none. `metrics.parse_trailers()` keys `Sdlc-Fixes` and `Sdlc-Retired` by id, and
    every existing key parses as before.

**Retro and docs**

18. `retro` reports `bugs`: reported in the window by severity (open bugs, `Sdlc-Fixes`,
    `Sdlc-Retired`, each id once, by `reported`), fixed by severity, retired by reason,
    report-to-fix days (median, max), open by age, and escapes per `introduced_by` change with its
    tier plus `unattributed`. The retro skill weighs escapes against tier. A test with one fix, one
    retired and one open bug asserts every count.
19. Docs: both process docs gain the inbox (kinds, ids), a `#### Bugs` section beside Nits (what a
    bug is, the severity bullet, the cycle) and the nit rubric naming entry lines;
    `docs/REFERENCE.md`, `README.md`, `AGENTS.md`, `docs/CONTRIBUTING.md`, `templates/notes.md`,
    `templates/direction.md`, the factory's notes text, and the intent, spec, ship, close, retro,
    status, setup and uninstall skills name `work/inbox.md`. `.sdlc/setup.json` is re-recorded, so
    `drift` is empty.

## Design

**Why one inbox.** The intake seeds turn outside reports (from other sessions, then GitHub issues,
then in hosts) into entries, and triage decides what each one is. A bug that's really a feature
request, or a request that's really a defect, is then a retag, never a move between files, so its
id holds, and the issue, the session's report, `After:` lines and open changes' `idea:` and
`fixes:` keep pointing at it. Ids, not titles, for the same reason: triage rewords titles into
neutral terms (the nothing-local rule), and title links break silently on that. Nit 019-1, a
mistyped `After:` title, is that failure today. One shape and one reader replace two: a kind is a
tag and its facts are body lines, so a new kind costs a tag and its lines, never a file. The intake
seed's `Source: <tracker ref>` line fits the same way; this change neither reads nor writes it.

**What nits give up.** `NNN-n` could never collide between parallel ships; a date id can when two
ships on the same day allocate before either's entry is written. Allocation reads every open
worktree's uncommitted inbox, so on one machine the window is seconds; two appends at the
register's end usually conflict at `base`; and `check` reports a duplicate that gets through.
`Raised by:` keeps the change number a reader used to find in the id.

**Code.** One `ENTRY_RE` (`## [(\d{4}-\d{2}-\d{2})(?:-(\d+))?] [tag] title`); one
`inbox_entries()` (once `idea_entries()`) returning entries with `id`, `tag` and body fields plus
problems, the kind-specific checks following `nit_entries()`' rules; `entry_ref()` and
`ref_matches()` for references; `register_path(root)` the one place that knows the shim; ship's
deletion reusing `_drop_seed()`; `next_entry_id()` following `next_id()` and
`_worktree_highest()`; `bug-commit` following `cmd_retro_commit()`; `_fix_trailers()` joining
measure's in `cmd_close`.

**Where each fact lives.** An open entry: the inbox. A fixed bug: its `Close` trailers. A retired
bug: its `Retire` trailer. A paid-down nit: its ship commit's `Retired nits:` paragraph, as today.

## Contracts touched

- **What `sdlc.py` reads or writes in a host** (why this is Tier 2): the register's name and shape,
  how references resolve, a new frontmatter key, a section read from the process doc, and
  `bug-commit`'s commits. Kept working: `work/ideas.md` and its template override (shim until
  2.0.0), bare-date headings and title references (permanently). Moves for a host: Next up commands
  become ids, new entries get ids, and nits move into the inbox (`nits.md` was never released).
  Impact `minor`; the 1.2.0 release is held until this lands, so `nits.md` and the bare `[bug]` tag
  never ship.
- **Shims**: `work/ideas.md` has a `deprecations.toml` entry; `cmd_release` will refuse 2.0.0
  while it remains.
- **The trailer contract**: extended with `Sdlc-Fixes` and `Sdlc-Retired`; nothing redefined.
- **Frontmatter read as text**: `idea:` and `fixes:` ids go through `frontmatter_list()`.
- **Numbering**: entry ids are their own space, never drawn from change numbers or the tracker.
- **One WAIT per writing skill**: `/sdlc:bug` has one; ship, retro and setup name the new writes in
  their existing WAIT. `migrate-inbox` and `bug-commit` get no allow rule; `next-entry` and `bugs`
  join `READ_ONLY`.
- **Only publish pushes. Nothing names a host. Shipped docs' shape and the defaults mirror**: the
  process doc sections land in both copies, then `record`.

## Alternatives rejected

- **A separate `work/bugs.md`** (as first specced): buys only a severity slot and a countable kind,
  which a body line and a tag give, and makes reclassifying a move between files.
- **Keeping the name `work/ideas.md`**: it now holds bugs and nits, which aren't ideas; `inbox`
  says what it is, where requests arrive before anyone acts on them.
- **Keeping `NNN-n` for nits**: two id shapes in one file, and a nit filed by intake has no change
  to number it by.
- **Separate counters per kind**: a retagged entry could collide.
- **Forcing migration, or rewriting history's titles**: the shim and permanent title reading keep
  every host working untouched.
- **A fixed severity scale in code**: the process doc owns the words.
- **Retro guessing escapes from paths**: only a confirmed `Introduced by:` counts.

## Verification

- `./check.sh` passes after every phase.
- `uv run --group dev pytest -q tests/test_inbox.py tests/test_nits.py tests/test_next_up.py
  tests/test_retro.py tests/test_metrics.py`.
- `sdlc.py migrate-inbox` on this repo: `work/inbox.md` holds every seed and the four nits with
  ids, `work/nits.md` and `work/ideas.md` are gone (history follows the rename),
  `.sdlc/DIRECTION.md`'s open references are ids, `status` shows the same Next up with id commands,
  `check --strict` is clean.
- End to end in the adoption test's bare repo: file a bug, `/sdlc:intent <id>` writes `fixes:`,
  ship deletes it, close writes `Sdlc-Fixes`, `retro` counts it; and both migration runs on the old
  layout.
- `sdlc.py drift` is empty after `record`.
