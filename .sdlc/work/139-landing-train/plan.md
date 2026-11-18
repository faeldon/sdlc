---
id: 139
slug: landing-train
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 139 — A landing train: the batch is integrated once, gated once, and its conflicts resolved once · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py` — `_main_lock()` reentrant per thread (a thread-local depth per lock path;
  only the outermost hold takes the OS lock) and inheritable by a handoff (`LOCK_HELD_ENV`,
  `SDLC_LOCK_HELD=<lock path>`, read and cleared at `cmd_close()`'s entry, set by `_handoff()`);
  `cmd_close()` wraps `merge` through `remove folder` in one `_main_lock()` hold (the dropped
  kind too, around `record`), letting go before `remove worktree`, the push and the cleanup;
  `_close_commit()`'s own hold nests; a new refusal before any write when a commit in
  `<trunk>..<branch>` touches another change's folder (`_carries_others()`, R12). Reuses
  `_lock_path()`, `work_rel()`, `DIR_RE`, `_git()`.
- `plugins/factory/scripts/factory.py` —
  - `cmd_land()` stops after its commit, `state: committed`; the `base` call and the
    "landed before" amend go (R2). A refusal while a train names the change is written to the
    train's state as that change's `failed` reason (`_train_fail()`), so the train ejects it.
  - The train's state: `TRAIN_STATE = "sdlc-factory-train.json"` in the git common dir
    (`_slot_dir()`), `read_train()` / `write_train()`; per change `worktree`, `pre`, `on` (the
    commit its own commits sit on), `stacked`, `stacking` (an `--onto` under way), `landed`,
    `ejected`, `failed`; train-wide `order`, `by`, `base`, `base_tip` (what the first live change
    stacks onto: the base's tip at the start, moved to the last landed change's stacked commit,
    or to the base's tip on a move), `expected` (the base's tip before the next close), `moves`,
    `gates`, `ejections`, `began`.
  - `cmd_train()`: `--begin <NNN…> --by` (from `ready()`'s order, refused while one is under way),
    the reading (names `next`: `commit`, `stack` with `onto`, `resolve` with its files, `gate`,
    `eject`, `accept`/`review`/`verify`/`mend` passed through from `land_verdict()`, `close`,
    `stop`, `done`; records `pre`/`on` when a change's commit appears, the gates it reads from
    `build/land-*.gate.md`, and a stacked change whose tree changed outside its folder, a fix),
    `--eject <NNN>` (reset `--keep` to `pre`, the train's records checked out from the stacked
    commit into the folder, an `eject` step record, `runs/land-train.md`, the stale
    `runs/land-resolved` removed, amended in; the undo printed) and `--stop` (every live change
    back the same way, a `stop` record, the state removed). Bisection: the green prefix `g` and
    red prefix `r` come from the recorded gates valid for the stack as it stands (gated commit ==
    the change's `stacked`); `p = (g + r) // 2` until `r == g + 1`, then eject `r`; the first live
    change ejected twice in a row is a stop.
  - `cmd_resolve(onto=…)`: the stack. Amends dirty records in first, then `git rebase --onto
    <onto> <on[k]>` with `_settle_counter()`'s counter loop as today; `current` when already
    there, `stacked` when it moved cleanly, `conflict` for the agent; opens `reviews/land-<n+1>/`
    when it moves; `--continue` finishes the stack (state updated, `builder.sessions` staged with
    the other mid-rebase records: `RESOLVE_RECORDS`).
  - `cmd_land_close()` in a train: refuses a change that isn't the next to close; checks the
    base's tip against `expected` (a partial close of this change is not a move); on a move counts
    it, moves `base_tip`, unstacks the live changes, records `stack` and says `moved`; else `git
    rebase --onto <trunk> <on[k]>`, writes `runs/land-train.md` (R17), amends, runs `sdlc.py
    close`, records `landed` and the new `expected`. Without a train it only refuses when the base
    moved (`_behind()`), since nothing rebases outside the train now.
  - `_land_gate_state()`: in a train, PASS when a recorded gate's commit has the change's stacked
    commit as an ancestor (R4/R5); `_land_diff()`: in a train the fork is `on[k]`, not the merge
    base; `cmd_gate(land=True)`: a change with no landing round in a train gates into
    `build/land-1.gate.md` (the first change, unmoved, when bisection reaches it).
  - `_land_task("train-resolve")`: a fresh builder session (`TASKS`, `TASK_ROLE`, `LAND_TASKS`,
    `LAND_TASK_STEP["train-resolve"] = "resolve"`, not in `RESUMES`) whose prompt names every
    non-ejected change: its title, its spec (`git show <pre>:…/spec.md`, `intent.md` at Tier 1)
    and its diff (`git show <pre>`).
  - `land_question()` (R16); `LAND_STEPS` += `stack`, `eject`; `land_step_text()` /
    `read_land_step()` gain `TRAIN: k of n` (`TRAIN_RE`); `_record_land()` fills it from the
    state; the docstring's command list and writes paragraph.
- `scripts/board.py` — `TRAIN_RE` and the `train` field (pinned copies), `LAND_AT["stack"] = 1`,
  `LAND_AT["eject"]` with `eject` shown as a stop (`stopped`, its problems), `LAND_LABEL["stack"]
  = "stacking"`, `train` in the progress dict. `scripts/board.html` shows `k of n in a train`.
- `plugins/factory/agents/builder.md` — the landing-conflict section covers the train: every
  change's spec and diff are read with `git show`; still only the conflicted files edited.
- `plugins/factory/skills/land/SKILL.md` — Step 0 asks `train` first (a rerun resumes); Step 3
  is the loop over `train`'s `next`; the fullest question; `Bash(… factory.py train *)`.
- `AGENTS.md` — *The factory* paragraph (the train stacks through `resolve --onto`; `land` no
  longer runs `base`), *Closing* (the lock from the merge to the `Close`), *The register*'s
  "under the same `_main_lock()`" stays true. `plugins/factory/README.md`'s landing bullet and
  command list; `docs/REFERENCE.md`'s `/sdlc-factory:land` sentence.
- `tests/test_train.py` (new) — R1–R19's tests, a `_drive()` helper that runs the train loop as
  the skill would, agents stood in for by files.
- `tests/test_land.py` — `current` → `committed`; the tests that drove a rebase, conflict or move
  through `land`/`land --close` alone are rewritten over the train; the question test's wording.
- `tests/test_register_lands.py` — `test_close_and_inbox_commit_keep_both_entries` files its idea
  from `_push_plan` (before the lock), not `fix_trailers` (R15).
- `tests/test_board.py` — `LANDS` gains `stack` and `eject`; `test_a_train_member_shows_its_place_and_an_ejection`.
- `.sdlc/work/139-landing-train/checks.md` — the doc lines and the skill's rule, which only a
  revert could lose.

## Work order

1. **Close's lock and its refusal (sdlc.py alone).** Red: `test_the_lock_is_reentrant_in_a_thread_and_exclusive_across_threads`,
   `test_close_holds_the_lock_from_its_merge_to_its_close`, `test_close_refuses_a_branch_carrying_another_change`;
   the R15 edit to the reread test. Green: reentrant `_main_lock()`, the hold in `cmd_close()`,
   `_handoff()`'s env var, `_carries_others()`. The adoption test's real merged handoff proves the
   inheritance (R14's second half).
2. **`land` stops at its commit; the question.** Red: `test_land_commits_and_leaves_the_rebase_to_the_train`,
   `test_the_question_says_the_batch_is_stacked_and_gated_once`. Green: `cmd_land()` trimmed,
   `land_question()`; `current` → `committed` across `test_land.py`.
3. **The train without a gate: state, stack, close.** Red: `test_a_train_stacks_each_change_on_the_one_before`,
   `test_a_train_of_three_lands_as_three_closes`, `test_each_landed_change_records_its_place_in_the_train`,
   `test_a_rerun_resumes_the_train_and_a_second_refuses`, `test_a_stopped_train_puts_every_unlanded_change_back`.
   Green: the state, `cmd_train()` (begin, reading, stop), `cmd_resolve(onto=)`,
   `cmd_land_close()`'s train path, `runs/land-train.md`, `_land_diff()`'s fork.
4. **The gate, bisection and ejection.** Red: `test_a_green_train_of_three_gates_once`,
   `test_a_red_tip_ejects_the_change_at_fault`, `test_a_kept_landing_change_ejects_only_its_change`,
   `test_a_train_resolution_is_reviewed_before_it_closes`, `test_a_train_conflict_goes_to_one_agent_with_every_change`.
   Green: `_land_gate_state()`'s train reading, `cmd_gate(land=True)` with no round, bisection in
   the reading, `--eject`, `train-resolve`.
5. **Moves.** Red: `test_a_move_mid_train_re_stacks_the_rest_and_counts_once`. Green: the
   expected-tip check in `cmd_land_close()`, the move's bookkeeping, the stop past `[land] moves`.
6. **The board and the step record.** Red: `test_a_train_member_shows_its_place_and_an_ejection`,
   the pinned-copy tests. Green: `TRAIN:` line, `stack`/`eject` steps, `board.py`/`board.html`.
7. **The skill, the agent, the docs, the rewritten landing tests, `checks.md`**; `./check.sh`.

## Tests

- R1 `test_a_train_stacks_each_change_on_the_one_before`; R2 `test_land_commits_and_leaves_the_rebase_to_the_train`;
  R3 `test_a_train_conflict_goes_to_one_agent_with_every_change`; R4 `test_a_train_resolution_is_reviewed_before_it_closes`;
  R5 `test_a_green_train_of_three_gates_once`; R6+R7 `test_a_red_tip_ejects_the_change_at_fault`;
  R8 `test_a_kept_landing_change_ejects_only_its_change`, `test_failing_acceptance_checks_as_stacked_eject_only_that_change`
  and `test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change`; R9 `test_a_train_of_three_lands_as_three_closes`;
  R10 `test_a_move_mid_train_re_stacks_the_rest_and_counts_once`; R11 `test_a_stopped_train_puts_every_unlanded_change_back`;
  R12 `test_close_refuses_a_branch_carrying_another_change`; R13 `test_close_holds_the_lock_from_its_merge_to_its_close` (portable);
  R14 `test_the_lock_is_reentrant_in_a_thread_and_exclusive_across_threads` (portable),
  `test_the_handoff_passes_the_hold_and_the_child_takes_no_lock` (portable: the variable passed only
  while held, popped before the child's first process, a close finishing under another thread's
  hold) and `test_a_close_that_hands_off_runs_under_the_parents_hold` (a real double handoff
  through `uv`, bounded by a timeout); R15 `test_close_and_inbox_commit_keep_both_entries` (kept,
  moved hook); R16 `test_the_question_says_the_batch_is_stacked_and_gated_once`;
  R17 `test_each_landed_change_records_its_place_in_the_train`; R18 `test_a_train_member_shows_its_place_and_an_ejection`
  (test_board.py) and `test_the_landing_step_record_is_a_pinned_copy` (kept, extended);
  R19 `test_a_rerun_resumes_the_train_and_a_second_refuses`.
- Acceptance checks (`checks.md`): AGENTS.md's *Closing* line names the lock's span; the land
  skill grants `factory.py train`.
- Manual (the spec's): a scratch host with three ready changes, `/sdlc-factory:land`, the
  first-parent line and the board's `k of 3`.

## Rollback

`git revert <sha>` undoes the code, the skill and the docs. It does not undo: a
`sdlc-factory-train.json` left in a host's git common dir by a train under way (delete it; the
branches it names are put back by `factory.py train --stop` before the revert, or by `git reset
--keep <pre-train commit>` from each change's `runs/land-step.md`); `Close` commits a train landed
(history, as any landing's); a `runs/land-train.md` in landed changes' folders in history (read by
nothing after this). The lock file `sdlc.lock` is unchanged in shape.

## Where the build departed from the plan

- `_inherit_lock()` is a plain call at `cmd_close()`'s top that primes the thread's depth for the
  process's life (a handed-off close is a process of its own), not a context manager wrapping a
  split-out body: `test_only_the_named_steps_push` pins `cmd_close` as `_push()`'s caller.
- The reentrant lock's R15 test files its idea by writing the register before the lock (what
  `/sdlc:idea` does before its `inbox-commit` waits), and asserts the `Close` commit carries it
  and the later `inbox-commit` finds nothing left to record: a `File` commit before close's merge
  would, rightly, make the fast-forward refuse.
- The move's bookkeeping is `_train_moved()`, called both before a close (R10) and after a close
  the race refused, as the old `cmd_land_close()` read a racing move.
- `_rebasing()` reads git's `rebase-merge`/`rebase-apply` dirs, not `REBASE_HEAD`, which outlives
  a finished rebase on git 2.56; `cmd_resolve()`'s counter loop uses it too.
- The reading finds checkouts through `current_branch()` (`_change_checkouts()`): a worktree
  mid-rebase has a detached HEAD, which `worktrees()` leaves out.
- A `resolve --continue` with markers left is a failure the train ejects (as the skill always
  stopped on it), so the rewritten batch test no longer probes it mid-train.
- `land --by` refuses a commit a person made (`stage: shipped`, no `Sdlc-Landed:`) through
  `_land_readiness()`, which the reading shares, so the train ejects such a change rather than
  asking for its commit again.
- R10's logic came with the close path in slice 3, so its two tests passed when first run; the
  other tests of each slice were seen red first.
- Round 1's review: the handoff's inheritance and R8's two other causes got their own tests;
  the first found that `cmd_close()` popped `LOCK_HELD_ENV` after `main_root()`'s git call, so
  the pop is now the function's first act.
- `tests/test_land.py` loses four tests the train makes obsolete (a move sending the landing back
  to its rebase, a second `land` rebasing, the moves bound and its record): R2 and R10's tests
  cover what they proved.

## Readings of the spec, where it left room

- `eject` is a step of its own in `runs/land-step.md` (R18), and its `- PROBLEM:` line is the
  `ejected from the train: <reason>` R7 asks for, the reason naming the gate file; the board shows
  it as a stop.
- The train-resolve prompt *names* each change's spec and diff (`git show <sha>:<path>`,
  `git show <sha>`) rather than inlining n specs and diffs into one prompt; the builder has
  Bash and reads them. R3's test checks the names.
- `train` is the one reader; it also writes the state file on every reading (what it derives:
  pre-train commits, gates read, a changed tree), as the spec's "(`--record`)" allows; branches
  are moved only by `--eject`, `--stop`, `resolve --onto` and `land --close`.
- A change `land` refused, or whose stack `resolve` aborted, is ejected like any other failure
  (R8); with no commit of its own, ejecting it moves nothing.
- A fix (`yes, with a fix`) runs at the `close` step of its change, as today's Step 4: the
  reading then sees the tree changed outside the folder, re-stacks what is above and gates again.
