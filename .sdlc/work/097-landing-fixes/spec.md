---
id: 097
slug: landing-fixes
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 097 — Fix four bugs in the factory's landing · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Each test named below is in `tests/test_land.py`. Without the requirement, the test fails.

**2026-11-17-31: the porcelain parse**

R1. `land --close` reads the worktree's uncommitted paths with `git status --porcelain -z
--untracked-files=all`, read raw and never through `_git()` (which strips the output). For a rename
or copy it skips the old path. Suppose a tracked file in the change's folder is modified after the
landing's commit and is listed first, as ` M .sdlc/work/NNN-slug/runs/costs.jsonl`. Then the close
amends it in and closes. `test_land_close_reads_a_modified_first_path_in_the_folder_as_the_folders`
fails with the stray `sdlc/work/…` path otherwise.

R2. Anything uncommitted outside the change's folder is still refused, and the refusal names the
path. This holds for `land --close` and for the amend in a second `land` (R4). Nothing is amended.
`test_a_landings_record_never_takes_in_a_path_outside_its_folder` (new) leaves an untracked file at
the repo root. It fails if either command amends the file or closes.

**2026-11-17-33: the landing's record before a second rebase**

R3. A change already at `stage: shipped` gets the earlier landing's record (`build/land-<n>.gate.md`,
`reviews/land-<n>/`, `runs/land-resolved`, `runs/costs.jsonl`). `land` amends that record into the
change's commit *before* it runs `sdlc.py base`. So a second `land` after `main` moved rebases and is
not refused. `test_a_second_land_after_main_moves_rebases_with_the_first_record_amended_in` fails
with `sdlc.py base`'s "has commits of its own and uncommitted work" otherwise. It also checks that
the change is one commit on `main` as it now stands.

R4. The record is amended only into the landing's own commit: `HEAD`'s message must carry an
`Sdlc-Landed:` line. Otherwise `land` refuses ("HEAD isn't the landing's commit") and nothing is
amended. `test_a_record_is_never_amended_into_a_commit_the_landing_didnt_make` fails with the guard
removed.

R5. `land --close` and the second `land` share one amend (`_amend_record()`). Neither has its own
copy.

**2026-11-17-32: nits a landing takes in**

R6. A nit is taken in only when the change names its id in one of two places, matching the
convention `/sdlc:intent` and `/sdlc:spec` already write. The places are the `## Approach` section of
`intent.md` (Tier 1) and the `## Requirements` section of `spec.md` (Tier 2). Each section runs to
the next `## ` heading. The nit must be an open `[nit]` entry, outside a fenced block, in the
worktree's register. The id is matched whole, so a longer id that starts with a nit's id doesn't
name it. An id written anywhere else is not taken in, for example in the Problem, as this change's
own intent does, citing what an earlier change took in. Nothing is ever inferred from the diff.
`test_a_landing_retires_the_nits_its_intent_names` gains an id named only in the Problem. It fails
if that nit leaves the register, or if the nit whose id is a prefix of the named one leaves.

R7. The named nits are read before `sdlc.py ship` and deleted only after ship succeeds. Each entry
is deleted from its heading to the line before the next heading, and the register is staged. Then
the commit runs. A ship refusal leaves the register byte-for-byte as it was.
`test_a_refused_step_lands_nothing_of_that_change` is extended with a named nit and fails if the
register changed.

R8. The landing's commit message carries a `Retired nits:` paragraph after its body, with one
`- <id>: taken in by <NNN-slug>` line for each nit, as `/sdlc:ship` writes it. `land`'s JSON lists
the ids as `retired_nits`, and the list is empty when there are none. Asserted in the test of R6.

R9. The factory reads the register with a copy of `sdlc.py`'s parsing (`NIT_RE` and the fence rule).
`test_the_landings_nits_are_the_ones_sdlc_reads` pins the copy to `parse_entries()` and fails when
they disagree on any entry.

**2026-11-17-34: a resolution counts exactly when no reviewer saw it**

R10. `factory.py resolve --continue` writes `runs/land-resolved` with `land-<n>` on its first line,
where `<n>` is the landing round under way (`land_round()`). The resolved files go on the second
line, as the marker's only line holds them now. The batch test asserts the first line.

R11. A landing resolution is a signal, worded exactly as now ("a conflict was resolved while
landing"), until `land-verdicts` for the marker's round says `pass`. After that it is not a signal.
A marker whose first line isn't `land-<digits>` was written before this change and stays a signal.
`test_a_landing_resolution_counts_until_its_review_passes` (new) fails if any of the following is
wrong:
- the signal is missing before the review;
- the signal is missing while a reviewer is missing, or the verifier kept a change;
- the signal is still there after every reviewer at the run's depth passed;
- the signal is missing for a marker without a round.

The existing assertion in `test_a_batch_lands_in_order_and_a_conflict_is_resolved_reviewed_and_closed`
(signal right after `resolve --continue`) stands. The test gains the reverse after its `pass`.

R12. `land-verdicts` and R11 decide `pass` with one function, `land_verdict(root, folder, cfg, n)`.
`cmd_land_verdicts` emits it for `land_round(folder)` with its output unchanged, and every existing
`land-verdicts` test passes unedited.

R13. A resolution `sdlc.py resolve` recorded in the change's `conflicts.md` is a signal in either of
two cases:
- a file any section names now differs from its hash in the newest complete build round's snapshot
  (`build/round-<R>.files`);
- the change has no complete round, or that round has no snapshot.

A file absent both from the snapshot and from the change's paths counts as unchanged. The signal
reads `a conflict resolved by sdlc.py resolve after the last review round: <files>`.
`test_a_resolution_the_build_reviewed_is_no_signal_and_one_after_it_is` (new) fails if either case
is misread. The first case is resolved before the round's snapshot and the second edited after it.

R14. The factory reads `conflicts.md` with a copy of `sdlc.py`'s `conflicts_resolved()` (each `- `
line's path, once, in order). `test_the_landings_resolutions_are_the_ones_sdlc_reads` (new) pins the
copy to it.

R15. `land --close` refuses a change whose commit says `Sdlc-Landed: by=auto` while its landing
resolution is a signal (R11), and names it. The rule is the script's, not only the skill's.
`test_an_auto_landing_never_closes_over_a_resolution_no_review_passed` (new) fails if the close
merges before the landing review passes, or is refused after.

R16. In a batch that passed itself, a change whose conflict was resolved during this landing goes on
to close once its landing review passes. The land skill no longer stops it for the next
`/sdlc-factory:land`. This changes when the WAIT asks (see *Contracts touched*). It is a skill-text
change. R15 is what makes it safe.

R17. The land skill's list of signals (Step 1) and Step 3.3, the factory README's list, and the
docstrings of `land_signals()` and `cmd_resolve()` say "a resolved conflict no reviewer has seen"
and the rule of R11 and R13. No text still says that a conflict resolved in an earlier landing
always asks.

**All four**

R18. `./check.sh` passes. Every `test_land.py` test that passes today passes unedited, apart from the
extensions named above.

## Design

**Assumptions, each checked in the code.**
- The landing runs in the change's worktree. `land --close` hands off to the main checkout
  (`cmd_land_close()`).
- The factory never imports `sdlc.py`. It copies the parsing and pins the copy (`BUG_RE`,
  `risk_paths()`).
- `sdlc.py ship` stages and stamps, but never touches the register. Retiring nits is ship's
  *skill*'s job (`skills/ship/SKILL.md`, Step 4).
- `sdlc.py resolve` records each finished resolution as a `## <date> onto <trunk> <sha>` section
  with `- <path>` lines. The date has no time of day, so it can't order a resolution against a
  review round.
- Snapshots hash every path the change touches, outside the change folders (`_tree_hashes()`), as
  each build round left it.
- Nothing but `factory.py` reads `runs/land-resolved`. The four readers are all its own, and
  `board.py` has none.

**31 and 33: one amend.** `_dirty(root)` runs `git status --porcelain -z --untracked-files=all` by
`subprocess.run` (with `encoding="utf-8"`) and splits it on NUL. It takes `entry[3:]` as the path and
skips the next entry after an `R` or `C` status. `_amend_record(root, folder)` calls `_dirty()` and
refuses on any path outside `work_rel()/<change>/`. When something is dirty, it checks that `HEAD`
is the landing's commit (`Sdlc-Landed:`). Then it runs `git add -- <folder>` and `git commit -q
--amend --no-edit`. `cmd_land_close()` calls it before the handoff. `cmd_land()` calls it on the
`stage: shipped` branch before `sdlc.py base`. Both sides of the stray check are git's own
unescaped `-z` paths against `Path.as_posix()`, with nothing compared to `--name-only` output.

**32: nits.** `named_nits(root, folder)` takes the text of intent.md's `## Approach` and spec.md's
`## Requirements`, each up to the next `## ` heading. It walks the register (`INBOX`) with
`FENCE_RE` and `NIT_RE`, and keeps each `[nit]` id that the text names whole:
`(?<![\w-])<id>(?![\w-])`. `retire_nits(root, ids)` keeps every line outside a retired entry and
writes with `newline="\n"`. `cmd_land()` calls `named_nits()` before ship, then `retire_nits()` and
`git add` after ship returns 0, then the commit. `land_message(..., nits)` appends the paragraph.
The register on the branch is the branch's copy. A nit filed on `main` after the fork isn't in it,
so it isn't retired. It stays open, which is the safe side.

**34: what "a reviewer saw it" means, read from the change's files.**
- *A landing resolution.* `cmd_resolve(cont=True)` writes the marker as `land-<n>\n<files>\n`.
  `resolution_signals(root, folder, cfg)` reads its first line with `^land-(\d+)$`. It returns no
  landing signal exactly when `land_verdict(root, folder, cfg, n)["next"] == "pass"`. A `pass`
  already requires three things: every reviewer at the run's depth (`run["reviewers"]`, since the
  marker exists) returned a verdict, the landing gate is not red, and the verifier kept nothing.
  "Seen" therefore means "reviewed and passed", which is all the gate needs. A later clean landing
  round leaves the marker's round as it was, and that round's pass still stands. A second
  resolution rewrites the marker with its own round.
- *A resolution by `sdlc.py resolve`.* `resolved_files(folder)` (the copy of R14) lists the files.
  `_rounds_at_depth()` gives the rounds, and the newest with `complete` gives `R`. The resolution
  was seen when, for each file, `_tree_hashes(root, base).get(f)` equals `read_snapshot(folder,
  R).get(f)`. The reviewers of round R read exactly that content. This compares content, not file
  times, so a fresh checkout reads it the same way.
- `land_signals()` adds both through `resolution_signals()`, in place of today's bare `is_file()`.
  `cmd_land_close()` reads `HEAD`'s message. On `by=auto` it calls `resolution_signals()` and
  refuses on the landing one. It doesn't check the `conflicts.md` one: `land` already checked it
  before committing, and the landing's own rebase can change those files' hashes without anyone
  resolving anything.
- `_land_task()` and `land-verdicts` keep reading the marker's existence to decide who reviews.
  That is unchanged.

**Edge cases.**
- If the landing's clean rebase changes a file `conflicts.md` names, a *second* `land` reads it as a
  signal. That errs towards asking the person, which is the safe side.
- A pre-change marker always asks, as today.
- With no complete build round, a `conflicts.md` resolution always counts.

**Boundaries.**
- *Always:* every signal is computed by the script; R11 and R13 decide alone, and the skill only
  reports them.
- *Asks first:* any batch with a signal, as today.
- *Never:*
  - forces, stashes, or merges `main` into a branch;
  - amends a commit the landing didn't make;
  - infers a nit from the diff;
  - changes `sdlc.py`.

## Contracts touched

- **A skill's WAIT, "what it approves, or when", is always Tier 2 (`.sdlc/SDLC.md`).** This change
  moves *when*, in two ways. A reviewed landing resolution no longer asks at the next landing. In a
  batch that passed itself, a resolved change now closes in the same landing once its full-depth
  review passes (R16). In the other direction, a `sdlc.py resolve` resolution no review round saw
  now asks where today it never did. **This loosens a gate: a builder's edit made during landing can
  reach `main` without a person, behind every reviewer's pass and a green gate.** The intent asks
  for exactly this ("one they reviewed need not"). R15 moves the guard from the skill's text into
  the script. D1 promoted the change to Tier 2 for this.
- **`Sdlc-Landed: by=auto` only when no change carries a risk signal (AGENTS.md, the factory).**
  The rule is unchanged, and the change only redefines one signal. `cmd_land()` still refuses
  `auto` on any signal. `cmd_land_close()` now refuses too, for a resolution no review passed.
- **Landing commits only through `sdlc`'s own `ship`, `base` and `close`.** The landing's own
  `git commit` (after ship) and `--amend` (before close) already existed. This moves the amend
  earlier, and guards it to the landing's own commit (R4). There is no new kind of commit and no
  copy of ship's or close's git steps.
- **`factory.py` never imports `sdlc.py`; copies are pinned by tests.** `NIT_RE` and the fence rule
  are pinned by R9, the `conflicts.md` reader by R14.
- **Writes before a WAIT, and never a stash or a merge of `main`.** There is no new write before
  the batch's question. The register edit happens in the step the person already approved, or that
  passed itself.
- **The register: `inbox-commit` is the only code that commits the register on its own.** The
  landing doesn't commit it on its own. The deletion rides in the change's own commit, as
  `/sdlc:ship`'s does, so a drop never loses an entry: the entry stays on `main` until the change
  lands.
- **The scripts run on Windows.** Every new `subprocess.run` names `encoding="utf-8"`, every
  `write_text` passes `newline="\n"`, and paths are compared as git prints them on both sides (see
  REVIEW.md's "A path compared as text between two sources").
- **`land-verdicts`' output is a contract the skill reads.** It is unchanged (R12).

No invariant in AGENTS.md needs to change.

## Alternatives rejected

- **`sdlc.py ship --retire <ids>`** (intent's open question 2). This would put the register into
  `sdlc.py ship`, which no caller uses that way today: `/sdlc:ship`'s skill deletes nits itself,
  after its own WAIT. It would also widen a core command's contract for the factory's sake. The
  factory already copies the register's parsing for bugs.
- **Reading nit ids from all of `intent.md` and `spec.md`** (as round 1 built it). Any id cited in
  prose would be retired as "taken in". This change's own Problem cites an id an earlier change
  took in.
- **Ordering a resolution against reviews by file mtime.** Mtimes aren't kept by a checkout, a
  rebase or a clone, and `conflicts.md`'s sections carry only a date.
- **Writing a round into `conflicts.md`.** That file is `sdlc.py`'s, read by ship's question, and a
  hand-built change has no review rounds to name.
- **Counting a passed landing round as having seen a `conflicts.md` resolution.** A clean rebase is
  reviewed by `behaviour` alone, so it would let one reviewer stand in for the run's depth.
- **Re-checking every signal at `land --close`.** `land` checked them before it committed, and the
  `conflicts.md` hash check would fire on the landing's own rebase.
- **Keeping the skill's stop after a reviewed landing resolution.** The next landing would find no
  signal and land it `by=auto` anyway, so the stop only adds a landing's delay.
- **Splitting 34 into its own change.** D1 decided against it.

## Verification

```bash
uv run --group dev pytest -q tests/test_land.py      # every landing test, the new ones included
uv run --group dev pytest -q -m portable             # what CI's Windows job runs
./check.sh                                           # ruff, format, the full suite, plugin validate
uv run --quiet --script scripts/sdlc.py preflight 097   # `cases.scope`: the land skill's text changed
```

Healthy output looks like this:
- `test_land.py` passes, including the five new tests and the extended ones. Each new test was
  seen failing before its code, and the evidence in `build/round-<R>.md` shows it.
- `check.sh` ends with `All checks passed!`, a passing pytest count, and `✔ Validation passed`
  twice.
- If `preflight` puts the factory's skill cases in scope, the person decides whether to pay for a
  run, as for any skill-text change.
