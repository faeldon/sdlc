---
id: 077
slug: ship-resolves-conflicts
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 077 — Ship resolves a conflict with the base branch itself · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. R1. `sdlc.py base` keeps its current behaviour and output for every case it handles today:
   fast-forward, rebase, refusal. Its refusals gain one field, `resolvable: true`, when the
   refusal is a conflict `resolve` can take on. There are three such cases:
   - uncommitted work over files the base changed;
   - a rebase that conflicts;
   - commits of its own plus uncommitted work.

   Every other refusal (`trunk_refusal()`, no local base branch) reads `resolvable: false`. 072's
   `cmd_land()`, which reads `base`'s `action` and `reason`, is unaffected, and a test pins that.
2. R2. A new `sdlc.py resolve <NNN>` starts a resolution in the change's own worktree:
   - It commits any uncommitted work, untracked files included, as one temporary commit. That
     commit is kept under `refs/sdlc/aside/<branch>` before anything moves.
   - It rebases the branch onto the base branch and stops at the first conflict.
   - It prints `conflicted` (the files), `state` (`conflict`, or `clean` when the rebase went
     through) and `undo`.
   - It never runs `git stash`, never merges the base into the branch, and never uses `--force` or
     `--hard`.
3. R3. `sdlc.py resolve <NNN> --continue` finishes a stopped resolution:
   - It refuses while any conflicted file still holds a conflict marker, and names the files.
   - Otherwise it stages the conflicted files and continues the rebase. It lists the next commit's
     conflicts as `conflict` again when there are any, so a branch with several conflicting
     commits is taken one stop at a time.
   - When the rebase completes, it undoes the temporary commit with a mixed reset, so the set-aside
     work is uncommitted again on top of the new base.
   - It then appends a record to the change's `conflicts.md`: the base commit it now sits on and
     every file resolved, across every stop.
4. R4. `sdlc.py resolve <NNN> --abort` puts the worktree back where `resolve` found it: the branch
   at its old commit, the uncommitted work uncommitted. A test checks the worktree's files and
   `git status` are the same as before the resolve.
5. R5. A conflict in `.sdlc/last-id` is settled by the script, which keeps the higher number as
   `base` does. It's never left for the agent, and never counted in `conflicts.md` as the agent's.
6. R6. No work is lost on any path:
   - `refs/sdlc/aside/<branch>` holds the set-aside work from R2 until `/sdlc:close` deletes it with
     the branch, beside `refs/sdlc/base/<branch>`.
   - `resolve`'s `undo` names it, so a run that died halfway can be recovered from it.
   - A test kills nothing but checks the ref exists after `resolve` starts and after `--continue`
     finishes.
7. R7. Ship's Step 0 resolves instead of stopping:
   - A `refused` with `resolvable: true` sends the skill to `skills/ship/conflict.md`, which runs
     `resolve` and merges each conflicted file so both sides' intent survives. It reads the base's
     commits for those files (`git log` between the old and new base) to know what the other side
     meant.
   - It then runs `resolve --continue` until `clean`, and goes on to Step 1.
   - A refusal with `resolvable: false` still stops, as today.
   - A `--continue` refused twice on the same files, or the gate failing in a file the resolution
     merged (any other failure is reported as a failing gate is), stops with `resolve --abort` run,
     and the person is told what happened.
8. R8. `conflict.md` states the merging rule:
   - Keep what each side added.
   - Where both changed the same line, write one line carrying both meanings.
   - In `.sdlc/work/inbox.md`, keep every entry from both sides, except one that either side
     deleted.
   - Never take one side wholesale.
9. R9. Ship's WAIT names the resolution. `ship_question()` reads the change's `conflicts.md` itself
   and adds the clause `with the conflicts in A and B resolved` (paths shortened as the
   sensitive-paths clause does). A test asks the question with and without the file.
10. R10. The review covers the resolution. `conflict.md` tells Step 3's correctness pass to read
    each resolved file's final hunks against both sides. `findings.md` says nothing new: the WAIT
    clause and `conflicts.md` are the record.
11. R11. `resolve` is in `OWN_SCRIPT_CMDS`, since it writes from a change's worktree. Ship's
    `allowed-tools` gains the rules for exactly the commands `conflict.md` runs: `resolve <NNN>`,
    `--continue`, `--abort`, and the read-only `git log`/`git diff` it uses. Skill rules and
    Windows rules hold (`encoding="utf-8"`, `newline="\n"`, no top-level platform import), and no
    git call names `main`.
12. R12. The docs say the new behaviour:
    - `AGENTS.md`'s "Bringing a branch up to date" paragraph, which currently names two writes
      before the WAIT and will name `resolve` as the third, by the same named exception.
    - `docs/REFERENCE.md`'s base paragraph and `guide/process.md`'s "stops, touching nothing, when
      that would conflict".
    - `.sdlc/setup.json`, re-recorded after the guide edit (`sdlc.py record`).
13. R13. End-to-end tests for both of today's shapes:
    - 071's shape: no commits of its own, uncommitted work over a file the base changed.
    - 074's shape: several files, including `.sdlc/work/inbox.md` and an untracked change folder.
    - A branch with its own commits that conflict.

    Each runs `base` (refused, resolvable), `resolve`, a scripted resolution, `--continue`, and
    checks the final tree, `git status`, `conflicts.md` and the aside ref.

## Design

**Two halves, as the factory's landing has.** The script does every git step and the agent only
edits files, the same split 072 made in `factory.py`'s `cmd_resolve()`. Ship's skill holds no git
logic: each command in `conflict.md` is a plain `sdlc.py` call (bash can't hold the logic and a
rule can't cover it), plus read-only `git log`/`git diff` to see the base side.

**One mechanism for every shape.** Uncommitted work becomes a temporary commit, so the three
resolvable shapes all become "a branch with commits whose rebase conflicts":

- uncommitted only (071 and 074);
- commits only;
- commits plus uncommitted, which `base` refuses today.

`resolve` rebases the whole branch, and `--continue` undoes the temporary commit at the end with
`git reset <aside's parent>`, a mixed reset, so the work is uncommitted again. Staged-versus-unstaged
isn't kept, which ship never relied on: `sdlc.py ship` stages everything anyway.

**State lives in git, never a state file.**

- Before anything moves, `resolve` writes `refs/sdlc/aside/<branch>` (the temporary commit, when
  there was uncommitted work) and `refs/sdlc/start/<branch>` (the branch's commit before).
- `--continue` and `--abort` read both, so a new session can finish or undo a resolution another
  one started.
- `--abort` runs `rebase --abort` when a rebase is in progress, then `reset --keep <start>`, then a
  mixed reset back to the uncommitted state when there was an aside commit. It works after a
  resolution finished too, since R7 aborts on a gate failing after it: the resolved work is first
  kept as a commit under `refs/sdlc/end/<branch>`, and it refuses once the branch has moved past
  `end` (ship committed).
- So `start`, `aside` and `end` stay until close deletes them with the branch (R6). The files
  resolved so far live in a fourth, `refs/sdlc/pending/<branch>`, a blob, never `conflicts.md`:
  once a change has resolved before, that file is tracked, and a tracked file modified mid-rebase
  makes `rebase --continue` refuse. It is deleted when the resolution finishes or aborts.
- A rebase leaves the worktree's HEAD detached, so `resolve` finds the change from the rebase's
  own `head-name` as well as `worktrees()`, which lists only checkouts with a branch out.

**The record.** `conflicts.md` in the change's folder gets one `## <date> onto <base> <short sha>`
section per finished resolution, with a `- <path>` line per file the agent resolved. The script
writes it, ship commits it with the change, and history keeps it. `ship_question()` reads it
through a helper beside `findings_fresh()`. Nothing else parses it.

**`base` stays put.** It still aborts its own rebase and refuses. It only adds the `resolvable`
field, from which of its refusal branches fired, so 072's landing, which calls `base` and handles
conflicts itself, is unchanged.

## Contracts touched

- **A skill's WAIT step** (always Tier 2). Ship now writes before its WAIT in a third way. Like
  `base` and `findings.md`, it's a named exception: it moves only the change's own branch, keeps
  the person's work recoverable under a ref, prints the undo, decides nothing the WAIT doesn't then
  show (R9), and ship commits nothing before the yes. `AGENTS.md` names it (R12).
- **Never a stash, never a merge of the base into the branch** (`cmd_base()`'s docstring). The
  set-aside is a commit on the change's own branch under the change's own refs, and the update is
  a rebase.
- **Only the named steps push** — `resolve` pushes nothing.
- **No git call names `main`** — `resolve` takes `trunk` from `load_config()` as `base` does.
- **`allowed-tools` rules** — each new command gets an exact rule. `resolve` writes, but only in
  the change's own worktree, under the WAIT's named exception. Like `base`, it is never in
  `ALLOW_RULES`.
- **The scripts run on Windows** — every new subprocess call names `encoding="utf-8"`, and
  `conflicts.md` is written with `newline="\n"`.
- **Close deletes only the change's own folder, worktree, branch and refs** —
  `refs/sdlc/aside/<branch>` joins the refs close already deletes, `refs/sdlc/base/<branch>`.

## Alternatives rejected

- **Make `base` resolve conflicts itself.** 072's `cmd_land()` reads `base`'s refusal to start the
  factory's own `resolve`. Changing what `base` does on a conflict would break the landing. A
  separate command keeps `base`'s meaning.
- **A patch file in the change's folder** (what was done by hand for 071 and 074). It sits in the
  tree while the files it describes are reset, so a crash leaves the work only in a file the next
  run could overwrite. A commit under a ref is git's own and survives anything short of `gc` on an
  unreferenced object, and the ref prevents that.
- **`git stash`.** The stack is shared by every worktree, and another session can pop it.
- **Merging the base into the branch.** Close fast-forwards, so the merge would land on `main`'s
  first-parent line, which `closed_changes()` walks.
- **Sharing the factory's `resolve`.** `factory.py` can't import `sdlc.py`, its resolve runs
  mid-landing on a committed change, and its markers live in `runs/`. Two copies of about 40 lines
  is cheaper than a cross-plugin contract today; a seed can revisit it if they drift.
- **A fresh-context reviewer on every resolution.** The factory needs one because its gate may
  pass itself. Ship's gate is always the person's, and R9 names the resolution there.

## Verification

- `./check.sh` exits 0, including the new tests.
- `uv run --group dev pytest -q tests/test_sdlc.py -k "resolve or base"`: the R1 pin, R2–R6 and R9.
- `uv run --group dev pytest -q tests/test_adoption.py -k resolve` (or a new end-to-end test,
  R13): both of today's shapes and the committed shape, through `uv run --script`.
- `sdlc.py run-cases --tag ship`: ship's skill cases still pass with `conflict.md` beside it. This
  is a paid run, and ship names it.
- **Manual:** two scratch worktrees edit one file. Close the first, then `/sdlc:ship` the second.
  Expect ship to resolve, name the file in its question, and commit one change whose diff holds
  both edits, with `refs/sdlc/aside/<branch>` present until close.
