---
id: 077
slug: ship-resolves-conflicts
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 077 — Ship resolves a conflict with the base branch itself · plan

## Context

`/sdlc:ship` stops whenever `sdlc.py base` (`cmd_base()`, `scripts/sdlc.py:3278`) refuses on a
conflict, and the person always answers "go ahead". On 2026-11-17 this cost a round trip each for
071 (README vs 070) and 074 (five files vs 072). Spec R1–R13 in
`.sdlc/work/077-ship-resolves-conflicts/spec.md`: a new `sdlc.py resolve` does the git half, ship's
new side file `conflict.md` does the merging, and the WAIT names the resolution.

**One correction to the spec, made in this build:** the spec deletes `refs/sdlc/start/<branch>`
when a resolution finishes, but R7's "gate fails after a resolution → `resolve --abort`" needs to
undo a *finished* resolution too. So all three refs live until close, and `--abort` works any time
before ship commits (it refuses once HEAD has moved past where the resolution ended). The spec's
Design paragraph is edited to say so.

## Files to change

- `scripts/sdlc.py`
  - `cmd_base()`: add `resolvable` to the report: `True` on the three conflict refusals (dirty +
    own commits, rebase conflict, ff over uncommitted work), `False` elsewhere. Nothing else moves.
  - new `cmd_resolve(root, ident, mode)` with `mode` in `start|continue|abort`, beside `cmd_base()`.
  - new `_settle_last_id(tree)`: `.sdlc/last-id` conflicted → keep the higher number, stage it
    (mirrors `factory.py`'s `_settle_counter()`; `_read_number()` reused).
  - new `conflicts_resolved(path)` reader beside `findings_fresh()` (`:1229`), and a `conflicts`
    argument to `ship_question()` (`:6503`) adding `with the conflicts in A and B resolved`
    (shortened with `RISK_SHOWN`, as the sensitive clause is); `cmd_ship_question()` passes it.
  - `cmd_close()`'s `delete_branch()` (`:3976`): also delete
    `refs/sdlc/{aside,start,end,pending}/<branch>`, each said not refused, as `BASE_REF` is.
  - `OWN_SCRIPT_CMDS` (`:4150`) gains `"resolve"`; argparse `resolve` with `--continue`/`--abort`
    (mutually exclusive), dispatched in `main()` beside `base` (`:8286`).
- `skills/ship/SKILL.md`: Step 0's `refused` paragraph: `resolvable: true` → read `conflict.md`;
  otherwise stop as today. Name `conflict.md` among the side files. One new `allowed-tools` rule:
  `'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py resolve *)'` (`git log *`
  and `git diff *` exist already).
- `skills/ship/conflict.md` (new): `## Step 0` only: run `resolve <NNN>`; for each conflicted file,
  read both sides (`git log -p <from>..<base> -- <file>` for theirs, the aside commit for ours),
  merge by R8's rule, then `resolve <NNN> --continue` until `clean`; stop + `--abort` on a second
  refusal on the same files; tell Step 1 that a failing gate after a resolution also runs
  `--abort` and stops; tell Step 3 to read each resolved file against both sides (R10). No gate,
  no commit, no `sdlc.py ship` (side-file rule).
- `tests/test_sdlc.py`: R1 pin, R2–R6, R9 (unit, beside `test_base_*` at `:1121`, reusing
  `_repo`, `_opened`, `_commit_on_main`, `_base`).
- `tests/test_adoption.py` or a new `tests/test_resolve.py`: R13 end to end through
  `uv run --script` (071 shape, 074 shape with `inbox.md` + untracked folder, committed shape).
- Docs (R12): `AGENTS.md` "Bringing a branch up to date" (three writes before the WAIT, `resolve`
  named), `docs/REFERENCE.md:324`, `guide/process.md:218`; then `sdlc.py record` so
  `.sdlc/setup.json` matches.
- `.sdlc/work/077-ship-resolves-conflicts/spec.md`: the refs correction above.

## `cmd_resolve` in detail

Refs (all under the change's branch name; the first three kept until close):
`refs/sdlc/start/<b>` = HEAD before; `refs/sdlc/aside/<b>` = the temporary commit, only when there
was uncommitted work; `refs/sdlc/end/<b>` = HEAD when the resolution finished;
`refs/sdlc/pending/<b>` = a blob listing the files resolved so far, only while one is under way.

- **start**: refuse outside a change worktree, without a base branch (`trunk_refusal()`), or with
  a rebase already in progress (point at `--continue`/`--abort`). Write `start`. If `_dirty_paths()`:
  `add -A` + `commit -q --no-verify -m "sdlc: set aside for resolve"` (git's configured user),
  write `aside`. `rebase -q <trunk>`; `_settle_last_id()`; if the rebase stopped only on
  `last-id`, continue it. Emit `{state: conflict|clean, conflicted, base, undo}`; on `clean`, finish
  (below).
- **continue**: refuse when no rebase is in progress and no unfinished `start`. Refuse while any
  conflicted file holds `<<<<<<<`, naming them. `add` each, `rebase --continue` (`GIT_EDITOR=true`);
  on a new stop, `_settle_last_id()` and emit `conflict` with the next files.
- **Which files were resolved, across stops:** kept in git, never in the tree. Each stop's
  conflicted files are written as a blob (`git hash-object -w --stdin`) under
  `refs/sdlc/pending/<b>`, read back with `cat-file -p` and extended at each stop. Not in
  `conflicts.md` mid-rebase: once a change has resolved before, that file is tracked, and a tracked
  file modified mid-rebase makes `rebase --continue` refuse (074's F1, the same shape). Deleted on
  finish and on abort.
- **finish** (from start or continue): if `aside`: `reset -q <aside>^` (mixed: the work is
  uncommitted again on the new base). Write `end`. Append to `conflicts.md`
  `## <date> onto <trunk> <short sha>` with a `- <path>` line per file from `pending`
  (`newline="\n"`), `last-id` never listed; delete `pending`. Emit `{state: clean, resolved, base,
  undo}`. A test covers a second resolution on a change whose `conflicts.md` is already committed.
- **abort**: refuse once HEAD has moved past `end` (ship committed). Mid-rebase: `rebase --abort`
  (HEAD back at aside or start). After finish: commit the current tree as a temporary commit kept
  under `refs/sdlc/end/<b>` (so the resolved work is never thrown away), `reset --keep <aside or
  start>`. Then, with `aside`, `reset -q <start>` (mixed). Delete `pending`; after finish, drop the
  section finish appended to `conflicts.md`. Emit `{state: aborted, at}`.
- `undo` in every report: `sdlc.py resolve <NNN> --abort`, and the aside commit's sha.
- Never `stash`, `--force`, `--hard`, a merge, or `main` in a git call; every subprocess UTF-8.

## Work order

1. `resolvable` in `cmd_base()` + its pin test (R1). Gate.
2. `cmd_resolve` start/finish for the clean and single-stop shapes, `_settle_last_id`, refs, tests
   (R2, R3, R5, R6).
3. Multiple stops, the marker refusal, `--abort` mid and after finish, tests (R3, R4).
4. `conflicts_resolved()` + the `ship_question()` clause + test (R9); close deletes the refs.
5. Ship's SKILL.md and `conflict.md`, the `allowed-tools` rule; `test_skills` passes (R7, R8,
   R10, R11).
6. End-to-end tests (R13); docs, `sdlc.py record`, spec correction (R12). `./check.sh`.

## Verification

- `./check.sh` green; `pytest -q tests/test_sdlc.py -k "resolve or base"`; the R13 tests.
- `pytest -q tests/test_factory.py tests/test_land.py`: 072's landing untouched by `resolvable`.
- At ship: `preflight`'s `cases` scope will include `ship`, so ship runs `sdlc.py run-cases --tag
  ship` (paid, the person's call there).
- Manual (scratch repo): two worktrees edit one file; close the first, `/sdlc:ship` the second;
  expect the resolution, the WAIT clause, one commit with both edits, refs gone after close.
