---
id: 044
slug: status-ranks-the-backlog
kind: spec
created: 2026-11-08
updated: 2026-11-08
---

# 044 — Status ranks and groups the backlog, so choosing the next change takes one read · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. Priority line.** `Priority: high|med|low` is read on any `[idea]` or `[bug]` entry
   (`Priority` joins `BODY_KEYS`). Absent or `med`, the entry ranks exactly as today. Any other
   word, or a `Priority:` on a `[nit]` (nits rank by `Cost:`/`Value:`), is a `check` problem.
   Tests pin both.
2. **R2. Rank order.** `next_up()` ranks: `high` entries (bugs by severity first, then oldest) →
   bugs by severity → each open milestone's first ready grouped seed → next in series → cost-`S`
   nits by theme → other ideas oldest first → `low` entries oldest first. `NEXT_RULES` gains
   `priority` first and `low` last, each with its description; a test builds one entry per rule and
   asserts the order. A `high` idea that is also a milestone's grouped seed is listed once, under
   `priority`.
3. **R3. Theme on ideas and bugs.** The optional `Theme:` line nits carry is read on ideas and bugs
   too. Each `next_up` item carries its `theme` (or `None`).
4. **R4. Ten shown, each with its reason and theme.** `■ Next up` prints the first 10 items
   (`NEXT_SHOWN = 10`), each line with its reason (today's label, plus `priority high` / `priority
   low`), its `[theme]` when it has one, its age and its command. A test with 12 candidates asserts
   10 lines and `(+2 more: status --all)`.
5. **R5. A themes block.** Below the ranked lines, `Themes:` prints one line per theme: its open
   entries by kind (`tests  9 (7 nits, 2 ideas)`, M-cost nits included) and the oldest's age,
   themes ordered by their best-ranked member, `(no theme)` last. A further line counts seeds
   waiting on `After:` (`3 waiting on earlier seeds`). Tests pin the counts and order.
6. **R6. `status --all`.** Prints every candidate, grouped by theme, each group in rank order, with
   no 10-line cap. Read-only like `status`. A test asserts every ready entry appears exactly once.
7. **R7. Last activity per open change.** Status computes each open change's `touched`: the newest
   of its branch's last commit time and the mtimes of the files `git status` lists as changed in its
   worktree. The open-change line prints `· touched 12m ago`; one older than `QUIET_HOURS = 24` is
   marked `quiet`. A test sets file mtimes and asserts both states. Paths are compared `as_posix()`,
   and no git call names `main`.
8. **R8. The status skill's order.** Recommends, in order: `check` problems → Ready to close → a
   **quiet** open change at `stage: build` or later, or one others depend on → release → retro →
   the first `Next up` line. An open change that isn't quiet is reported as in flight in the shape
   line, never as the recommendation. Runners-up may name a theme from `Themes:` when its entries
   go together.
9. **R9. Entry-writing skills offer theme and priority.** `/sdlc:idea` and `/sdlc:bug` show
   `Theme:` in their drafts, proposed from the themes already in the register (the person may
   change or drop it), and `Priority:` only when the person names one. `/sdlc:triage` keeps either
   line when the entry it files carries one. `tests/test_skills.py` still passes; no new bash
   commands.
10. **R10. Docs say it.** `templates/inbox.md`'s note names `Theme:` and `Priority:` as optional on
    ideas and bugs; `docs/REFERENCE.md`'s **What comes next** describes the new order, the 10
    lines, the themes block and `--all`; `README.md`'s mention matches.
11. **R11. Old registers read as before.** A register with no `Priority:` and no `Theme:` lines on
    its ideas gives the same relative order as before this change, every idea under `(no theme)`;
    a test pins it from the existing `test_next_up_orders_by_rule` fixture.
12. **R12. The no-theme nudge.** When at least `THEMELESS_NUDGE = 5` open ideas and bugs (not
    being built; nits never count) have no `Theme:` line, `■ Next up` ends with
    `    31 ideas and bugs have no theme: /sdlc:idea --themes proposes them`. Below that it's left
    out. A nudge like every other status line: nothing runs. A test pins it at 5 and its absence
    at 4.
13. **R13. `/sdlc:idea --themes`.** A mode of `/sdlc:idea` (`argument-hint` names it; `--themes`
    alone, so it can never be read as an idea's prose, which is anything that isn't it or an
    entry's id), that reads the
    register and proposes a `Theme:` for every open idea and bug lacking one (entries being built
    excepted): reusing words the register's `Theme:` lines already hold (nits' included), coining
    one only where none fits, each one word or a short kebab-case phrase. It shows one table (id,
    kind, title, proposed theme) the person may change, drop or merge any row of; behind the
    skill's existing single WAIT it adds a `Theme:` line to each approved entry, after its last
    body line, changing nothing else, and commits with `inbox-commit` as one `Update <id>, …`
    commit. From a change's worktree it says why and stops: splicing from a worktree would put back
    that worktree's older copy of each entry. It touches `[bug]` entries only to add `Theme:`, and
    `skills/bug/SKILL.md` says so as the one exception to "a `[bug]` is `/sdlc:bug`'s".
    `tests/test_skills.py` still passes (one WAIT, every bash command covered).
14. **R14. `inbox-commit` keeps a themes pass whole.** A test runs `inbox-commit` from the main
    checkout over a register where 3 entries (2 ideas, 1 bug) gained a `Theme:` line, and asserts
    one commit subjected `Update <id>, <id>, <id>` whose diff adds only those 3 lines.

## Design

- **Reading entries.** `parse_entries()` already collects `Key: value` lines through `BODY_RE`;
  adding `"Priority"` to `BODY_KEYS` makes it readable. `entry_priority(e)` returns `high`, `med`,
  `low` or `None` (absent). `Theme` is already a body key, read from `e["fields"]`. Problems join
  the register checks `check` already runs over the inbox (the same path as `nit_entries()`'s
  problems).
- **`next_up()`.** `ready` is split into `high`, `low` and the rest. A `priority` rule runs first
  over `high` (sorted bugs-first by `severity_rank`, then date), the existing rules run over the
  rest unchanged (so R11 holds by construction), and a `low` rule runs last. Each item gains `id`,
  `kind` and `theme`. The returned dict gains `themes` (per theme: counts by kind, oldest date, best
  rank, built from every open entry: nits of every cost, ready and waiting ideas and bugs, plus `(no theme)`),
  `waiting` (count of `waiting` seeds) and `all` (every ready candidate grouped by theme, for
  `--all`). Nothing but `print_status` and the tests reads this dict, so its new fields carry no
  compatibility burden.
- **Printing.** `print_status` prints 10 lines, then `Themes:`, then the waiting count, then the
  existing milestone and `⚠` lines. `--all` is an argument on the `status` subparser that swaps the
  10 lines for the grouped list.
- **`touched`.** A helper `last_touched(home, rec, trunk)` finds the change's checkout through the
  worktree list `change_dirs()` already walks, takes the branch's last commit time (`git log -1
  --format=%ct <branch>`) and the newest `stat().st_mtime` over `git status --porcelain -z` paths in
  that checkout (a missing path skipped). It runs only in `cmd_status`, beside `behind_trunk`, never
  in `analyze()`, so `check` stays as fast as it is.
- **The skill.** `skills/status/SKILL.md` Step 3's precedence list is rewritten per R8; Step 1's
  description of `Next up` follows R2, R4 and R5. Step 3 keeps "one recommendation, at most two
  runners-up": the script already prints the ten.
- **The nudge.** `next_up()` counts `themeless` (open ideas and bugs, `ready` or `waiting`, with no
  theme) while building `themes`; `print_status` prints the nudge after the waiting count.
- **The pass.** Skill prose only, a section of `skills/idea/SKILL.md`, *Themes for what has none*,
  reached from Step 0 when the argument is `themes`. It uses the commands the skill already runs
  (`config`, `inbox-commit`), so no new allow rule. The theme judgment is the agent's; the script
  only counts, and `Themes:` groups whatever the person approved.

## Contracts touched

- **Always Tier 2: a change to what something a host already has means.** `Priority:` is a new
  optional key whose absence keeps today's order (R11); `Theme:` keeps its nit meaning and is newly
  read on ideas and bugs. `Next up`'s order and length change in status's printed output, which no
  host file or trailer records.
- **The inbox is read as text.** `Priority` and `Theme` are `Key: value` body lines through
  `BODY_RE`, never YAML; no entry is rewritten.
- **Status is read-only, and the skill never reads the register.** All ranking, theming and
  `touched` stays in `sdlc.py`; `--all` writes nothing, and the existing `status *` allow rule
  covers it.
- **`git.base`.** `touched` passes `trunk`, never a literal `main`
  (`test_no_git_call_names_main_itself`).
- **Windows** (`test_windows.py`): mtimes come from `Path.stat()`, git calls name
  `encoding="utf-8"`, paths are compared `as_posix()`; new tests that need no shebang fakes are
  marked `portable`.
- **`templates/` is irreversible** (`[review] irreversible`). The only change there is
  `inbox.md`'s note, so the ship commit carries `How to recover:`; `test_defaults.py`'s shape holds
  (the note stays one `>` block).
- **Status stays read-only.** The nudge names a command and runs nothing; all writing goes
  through `/sdlc:idea`'s WAIT and `inbox-commit`, the only code that commits the inbox on its own.
- **One WAIT per writing skill.** `/sdlc:idea` keeps exactly one heading containing `WAIT`; the
  themes mode goes through it, its question `Add these <n> Theme: lines to .sdlc/work/inbox.md and
  commit them as "Update <ids>"? (yes / edit a row / no)`.
- **Who edits a `[bug]`.** `/sdlc:bug` still owns severity, retiring and retagging; the themes
  pass adds one optional line, nothing a bug's meaning rests on.
- **Nothing local.** The intent describes the host session without naming it; spec and tests use
  neutral data (`reopen-drafts`).

## Alternatives rejected

- **An `Urgent: <why>` flag.** The person chose graded `Priority:`, which can also push an entry
  down (`low`), which a flag can't.
- **Themes inferred from `Paths:`.** Most ideas carry no `Paths:`, so nearly everything would land
  in one bucket.
- **Transcripts to tell whether a session is live.** Heavier, and off when `metrics.transcripts`
  is false; file mtimes and the last commit cover the case at one stat per changed file.
- **A config key for the quiet window.** A new key for a number nobody has asked to tune;
  `QUIET_HOURS` stays a constant until someone does.
- **Readiness/effort groups** (ship today / needs you / blocked), and inferring an entry's origin
  (a review's finding vs. the person's own seed) to sort them. Deferred at the person's call: it
  needs a signal ideas don't carry, and status mustn't grow long or slow. Filed as an idea for a
  deterministic answer or a skill of its own.
- **One change taking a whole theme's ideas.** `idea:` names one seed, and ship deletes only that
  one. The themes block makes a group visible; building a group as one change is its own design,
  in the same seed.
- **Status writes themes.** Status has no WAIT and is the most-run skill; an inbox commit there
  would change the register unasked.
- **Status proposes themes in its report without writing them.** Breaks its never-read-the-register
  rule, costs a full register read every run, and gives themes that can change between runs.
- **A `/sdlc:themes` skill.** One more command for a pass that is mostly a one-time backfill;
  `/sdlc:idea` already reads the register and commits edits to it.
- **The pass from a worktree.** Splicing would restore stale copies of the entries it names.

## Verification

```bash
./check.sh                                                     # the full gate
uv run --group dev pytest -q tests/test_next_up.py tests/test_bugs.py tests/test_inbox.py tests/test_skills.py
uv run --quiet --script scripts/sdlc.py status                 # from this worktree, against the main checkout's register
uv run --quiet --script scripts/sdlc.py status --all
```

Healthy: this repo's register shows 10 `Next up` lines with reasons; a `Themes:` block with every
idea under `(no theme)` until themed and the nit themes as today; the M4 milestone seed still near
the top (no `high` entries yet); and 044's open-change line reads `touched …m ago`, not quiet.
After the merge, from the main checkout: `/sdlc:idea --themes`, approve, then `status`; the nudge is
gone, `Themes:` shows the ideas grouped, and `(no theme)` holds only what the person dropped.
