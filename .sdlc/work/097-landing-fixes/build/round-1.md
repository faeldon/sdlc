I fixed three of the four landing bugs (31, 32 and 33) and left bug 34 unbuilt: it changes when the landing's gate asks you, which the process doc makes Tier 2, so it needs your call (below). Each fix got a test that failed first, and the full gate passes with 2003 tests. Nothing is committed.

## Slices built

1. **Bug 31: `land --close` misread the first changed file.** `cmd_land_close()` read `git status` through `_git()`, which strips the output. A modified first file (` M …`) lost a character of its path, looked like it was outside the change's folder, and the close was refused. A new `_dirty()` reads `git status --porcelain -z` without stripping and skips a rename's old path. The amend step moved into a new `_amend_record()`, which `cmd_land_close()` now calls.
2. **Bug 33: a second `land` after `main` moved was refused.** When the change is already committed (`stage: shipped`), `cmd_land()` now calls `_amend_record()` before `sdlc.py base`. The earlier landing's record goes into the change's commit, and the second `land` rebases.
   - I added a guard: the amend only happens when `HEAD` carries `Sdlc-Landed:`, i.e. is the landing's own commit. Without it, a change at `stage: shipped` whose commit a person made would have the record amended into that commit; a test shows this happening with the guard taken out.
3. **Bug 32: a landing didn't retire the nits a change took in.**
   - **What:** `named_nits()` finds the open `[nit]` entries in the change's worktree copy of the register whose id appears in `intent.md` or `spec.md`. Ids are matched whole, so naming `2026-11-17-11` doesn't retire `2026-11-17-1`.
   - **When:** the ids are read before `sdlc.py ship`. Only after ship succeeds does `retire_nits()` delete each entry and stage the register, so every ship refusal still happens before anything is written.
   - **Commit message:** `land_message()` adds a `Retired nits:` paragraph with one `- <id>: taken in by <change>` line each, and `land`'s output lists them as `retired_nits`.
   - This answers the intent's second open question: the nits are retired in `factory.py`, so `sdlc.py` is unchanged.
   - The land skill's Step 3.1 and the factory README now say what `land` does with nits and with an earlier landing's record.

## Tests added (`tests/test_land.py`)

- `test_land_close_reads_a_modified_first_path_in_the_folder_as_the_folders` (bug 31): before the fix it was refused with the exact `sdlc/work/…` stray path from the bug report.
- `test_a_second_land_after_main_moves_rebases_with_the_first_record_amended_in` (bug 33): before the fix it got the "has commits of its own and uncommitted work" refusal. After, the round-1 review is in the change's commit, and the change is one commit on `main` as it now stands.
- `test_a_landing_retires_the_nits_its_intent_names` (bug 32): the named nit is gone from `main`'s register, the `-1` nit and an idea stay, and the commit has the `Retired nits:` paragraph.
- `test_a_record_is_never_amended_into_a_commit_the_landing_didnt_make`: the amend guard. It failed with the guard removed and passes with it.
- `test_the_landings_nits_are_the_ones_sdlc_reads`: pins the new `NIT_RE` and the fenced-example rule to `sdlc.py`'s `parse_entries()`. It passed on its first run, as a pin of a copy does.

## Gate

`./check.sh` exits 0 with 2003 tests passed. The plugin directory's warning about a missing factory icon doesn't change the result.

## plan.md and notes.md

`plan.md` was written before the code. Since then it records the amend guard, that nits are retired after ship rather than before, the two extra tests, and the edits to the skill and README. Nothing is left in `notes.md`.

The land skill's text changed, so `/sdlc:ship`'s check on whether the skills' cases are in scope may apply.

## Decisions

- DECISION: [blocking] Bug 2026-11-17-34 (a conflict resolution counts as a landing signal only if no reviewer saw it) changes when `/sdlc-factory:land`'s WAIT asks. The process doc makes that Tier 2 ("A skill's WAIT step: what it approves, or when"), and this change is Tier 1. Options: promote 097 to Tier 2 with a spec for 34; split 34 off as its own Tier 2 change and land 097 with 31–33. Recommend splitting it off: 31–33 are tested and green as they stand, and 34 has its own design question. What counts as "a reviewer saw it" can only be read from file order (`conflicts.md` and `runs/land-resolved` against the verdict files), or from a landing round written into the `land-resolved` marker. That deserves a spec before code.

## Evidence

```
$ uv run --group dev pytest -q tests/test_land.py -k modified_first   # before the fix
E       AssertionError: {'refusals': ["uncommitted outside the change's folder: sdlc/work/001-costed/runs/costs.jsonl"]}
1 failed, 7 deselected in 6.53s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k second_land   # before the fix
E           AssertionError: {'change': '001-twice', 'state': 'refused', 'refusals': ["sdlc.py base refused: 001-twice has commits of its own and uncommitted work, so it can't rebase: commit the work, then run /sdlc:ship again"], 'head': '0848654', ...}
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k didnt_make   # guard removed
E       AssertionError: {'change': '001-handmade', 'state': 'current', 'refusals': [], 'head': '031312c', ...}
1 failed, 9 deselected in 4.24s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k retires   # before the fix
E       AssertionError: tidy
exit: 1

$ uv run --group dev pytest -q tests/test_land.py
12 passed in 11.63s
exit: 0

$ ./check.sh
All checks passed!
2003 passed in 39.86s
✔ Validation passed
✔ Validation passed
exit: 0
```

I've stopped without building anything. D1 says to promote 097 to Tier 2 with a spec for bug 34, but there is no spec yet: `spec.md` doesn't exist and `intent.md` still says `tier: 1`, `stage: build`.

Writing the spec isn't my job. It's a stage with its own approval question, and the reviewers will judge my build against it. If I wrote it here, that question would be skipped and the reviewers would be checking the code against a spec I wrote myself. Changing `tier:` belongs to that same stage, so I left the intent alone.

**What happens next:** promote 097 to Tier 2 and run `/sdlc-factory:spec 097` (or `/sdlc:spec 097`). Once `spec.md` is approved, resume me and I'll:
1. Rewrite `plan.md` against the spec's numbered requirements.
2. Check the work already done for 31–33 against those requirements, and change it where the spec differs.
3. Build 34 test-first.

**State of the tree:** this round changed nothing in the code. The work for 31–33 is unchanged and uncommitted, and it waits for the spec, as D1 says. The gate passes with 2003 tests.

**For the spec on 34**, the design questions I'd want it to settle:
- **What counts as "a reviewer saw the resolution":**
  - **Order of files:** the resolution's record (`conflicts.md` or `runs/land-resolved`) is older than some reviewer's verdict file. This reads what's already there, but file times can't be trusted after a fresh checkout.
  - **A recorded round:** `factory.py resolve --continue` writes `land-<n>` into the `land-resolved` marker. The resolution counts as seen when `reviews/land-<n>/` holds a verdict. This is reliable, but a marker written before this change carries no round and would still count as unseen.
- **Resolutions made by `sdlc.py resolve`** (recorded in `conflicts.md`) before or between the build's rounds: the factory records nothing to say which review round came after them. The spec needs to say whether such a resolution counts as seen.
- **Wording:** whether `land`'s skill text ("a conflict resolved in an earlier landing") and the README's list of signals change to the new rule.

No new decisions this round; D1 is settled and I'm building on its answer.

## Evidence

```
$ test -f .sdlc/work/097-landing-fixes/spec.md
exit: 1

$ grep -n "^tier:\|^stage:" .sdlc/work/097-landing-fixes/intent.md
4:tier: 1
6:stage: build
exit: 0

$ ./check.sh
All checks passed!
2003 passed in 49.82s
✔ Validation passed
✔ Validation passed
exit: 0
```

I built all of R1–R18. Each new or extended test failed before its code, and the gate passes with 2008 tests. Nothing is committed.

## Slices built

1. **R2: paths outside the change's folder.** New test: an untracked file at the root makes both the second `land` and `land --close` refuse, naming it, with `HEAD` unchanged. The code already did this, so I took the stray check out to see it fail: the stray file was amended in and `base` then refused.
2. **R6, R8: where nit ids are read.** `named_nits()` now reads only intent.md's `## Approach` and spec.md's `## Requirements`. Round 1 read the whole file and retired a nit the Problem only cited; the test now shows that nit staying. `land`'s output always has `retired_nits`, `[]` when there are none.
3. **R7: a refusal leaves the register alone.** `test_a_refused_step_lands_nothing_of_that_change` now also makes ship itself refuse (an open finding), with a nit named, and compares the register byte for byte. The test before it refused ahead of ship, so it couldn't show this. Moving the deletion to before ship makes it fail.
4. **R14:** `resolved_files()`, a copy of `sdlc.py`'s `conflicts_resolved()`, with a test pinning the two together.
5. **R12:** `land_verdict()` is lifted out of `cmd_land_verdicts()`. Every existing `land-verdicts` test passes unedited.
6. **R10, R11:**
   - **Marker:** `resolve --continue` writes `runs/land-resolved` as `land-<n>` on its first line, then the files.
   - **Signal:** `resolution_signals()` counts a landing resolution as a signal until `land_verdict()` for that round says `pass`. A marker with no round always counts.
   - **Tests:** the batch test checks the marker's first line, and that the signal is gone after the pass. The new test covers each case: before review, a reviewer missing, a change the verifier kept, all passed, `HEAD` moved after the pass, and a marker with no round.
7. **R13:** a resolution recorded in `conflicts.md` counts unless each file it names hashes the same now as in the newest complete build round's snapshot. With no complete round, it always counts. The test covers no round, a resolution made before the snapshot, and one edited after it.
8. **R15:** `land --close` refuses a change committed `by=auto` while its landing resolution hasn't passed review. It checks before the amend moves `HEAD`, and closes once review passes.
9. **R16, R17:**
   - **Land skill:** Step 1's list of signals now says "a resolved conflict no reviewer has seen", with both rules. Step 3.3 no longer holds a reviewed resolution back for the next landing.
   - **Elsewhere:** the factory README's list now uses the same wording, and the docstrings of `land_signals()` and `cmd_resolve()` describe the new rule.

## One departure from the spec

R12 names `land_verdict(root, folder, cfg, n)`. I added a keyword `settled=False` that is passed to `_land_gate_state()`, and `plan.md` says why.

The spec says a round's pass still stands after `HEAD` moves. But a landing gate attempt only counts while `HEAD` is the commit it ran on, and the second `land`'s amend (R3) moves `HEAD`. So a passed round would turn back into a signal. With `settled`, R11 takes the round's last gate verdict as it stands: red stays red and a pass stays a pass. `land-verdicts` itself still checks the gate against the current `HEAD`.

Turning `settled` off makes the R11 test fail on exactly the line where `HEAD` moves.

## Gate and the spec's checks

- `./check.sh`: 2008 passed, ruff clean, both plugin validations pass.
- The portable tests: 216 passed.
- `preflight 097`: the skill cases' scope is empty, there are no risk paths, and no nits are listed.

## plan.md and notes.md

`plan.md` is rewritten against R1–R18: what round 1 built and the spec kept, the nine slices, which test proves which requirement, why `settled` exists, and rollback. Nothing is left in `notes.md`.

## Decisions

None raised. D1 is settled and the work is built on it.

## Evidence

```
$ uv run --group dev pytest -q tests/test_land.py -k outside_its_folder   # stray check taken out
E       assert (1 == 1 and 'stray.txt' in "sdlc.py base refused: 001-strayed has commits of its own and uncommitted work, so it can't rebase: commit the work, then run /sdlc:ship again")
1 failed, 12 deselected in 1.91s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k "retires or sdlc_reads or outside_its"   # before R6
E       AssertionError: {'change': '001-tidy', 'state': 'current', 'refusals': [], 'retired_nits': ['2026-11-17-11', '2026-11-17-2'], ...}
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k refused_step   # nits deleted before ship
E       AssertionError: the register as it was
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k resolutions_are   # before R14
E       AttributeError: module 'factory_landing' has no attribute 'resolved_files'
1 failed, 13 deselected in 0.11s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k "until_its_review or batch_lands"   # before R10
E       AssertionError: the round under way, then the files
E       assert ['README.md'] == ['land-1', 'README.md']
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k until_its_review   # before R11
>       assert not asks(), "every reviewer at the run's depth passed it"
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k until_its_review   # settled turned off
>       assert not asks(), "the landing's own record moved HEAD: the pass still stands"
E       AssertionError: the landing's own record moved HEAD: the pass still stands
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k build_reviewed   # before R13
>       assert asked() == [f"{said}: README.md, untouched.txt"], "no complete round saw it"
E       assert [] == ['a conflict ...ntouched.txt']
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k never_closes_over   # before R15
>       assert code == 1 and "a conflict was resolved while landing" in out["refusals"][0], out
E       assert (0 == 1)
exit: 1

$ uv run --group dev pytest -q tests/test_land.py tests/test_factory.py   # after R12
172 passed in 56.89s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py
17 passed in 41.28s
exit: 0

$ ./check.sh
All checks passed!
2008 passed in 71.21s (0:01:11)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -m portable
216 passed, 1792 deselected in 50.79s
exit: 0

$ uv run --quiet --script scripts/sdlc.py preflight 097
cases {"available": true, ..., "scope": [], ...}
risk {"sensitive": [], "irreversible": [], "deep": false}
nits {"path": ".sdlc/work/inbox.md", "nits": [], "problems": []}
exit: 0
```
