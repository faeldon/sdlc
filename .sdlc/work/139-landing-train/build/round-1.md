All seven slices are built, the gate is green and nothing is committed (`HEAD` is still `e111ebc`; 14 paths changed or new in the tree). The report:

## Report — 139 landing-train, build round 1

**Slices built**

1. **Close's lock and refusal (`scripts/sdlc.py`).** `_main_lock()` is reentrant per thread (`_lock_depth()`), `cmd_close()` holds it from the first landing step (the merge) until the `Close`/`Drop` commit and lets go before the issues are told, the worktree's removal, the push and the cleanup; `_handoff()` passes the hold to its child through `SDLC_LOCK_HELD` (`_inherit_lock()`, popped at `cmd_close()`'s entry); `_carries_others()` refuses a branch whose commits touch another change's folder (R12–R15).
2. **`land` stops at its commit; the question** (R2, R16): `cmd_land()` ends `state: committed`; `land_question()` says stacked, gated once at the tip, bisected, one landing agent, closed in order.
3. **The train** (`plugins/factory/scripts/factory.py`): `cmd_train()` (`--begin`, the reading, `--eject`, `--stop`), its state in `sdlc-factory-train.json` in the git common dir; `resolve --onto` as the stack (records amended in first, counter settling itself, a landing round opened when it moves); `land --close`'s train path (next-to-close only, expected-tip check, `rebase --onto <base> <on>` past the `Close` commits, `runs/land-train.md`); `_land_diff()` reads a stacked change's diff from where its own commits start (R1, R9, R11, R17, R19).
4. **Gate, bisection, ejection, one landing agent** (R3–R8): `_train_gate()` bisects by prefix from the gates valid for the stack; `_land_gate_state()` lets the tip's PASS stand in for every change under it; `--eject` resets `--keep` to the pre-train commit, checks the train's records back into the folder, records `eject` with the reason and the gate file, amends; `train-resolve` is a fresh builder session told every change's title, spec and diff.
5. **Moves** (R10): `_train_moved()` before a close and after one a race refused; past `[land] moves` the reading says `stop`.
6. **Board and record** (R18): `TRAIN: k of n` in `runs/land-step.md`, steps `stack` and `eject`, pinned copies in `board.py`, `k of n in a train` on the page.
7. **Skill, agent, docs, tests, checks**: the land `SKILL.md` is a loop over `train`'s `next` (one WAIT kept; `train *` rule added), `builder.md`'s landing section covers the train, AGENTS.md's *Closing* and *The factory* paragraphs, the factory README, REFERENCE, `factory.py`'s docstring; `checks.md` with three acceptance checks.

**Tests added** (`tests/test_train.py`, 17): R1 `stacks_each_change_on_the_one_before`, R2 `land_commits_and_leaves_the_rebase_to_the_train`, R3 `conflict_goes_to_one_agent_with_every_change`, R4 `resolution_is_reviewed_before_it_closes`, R5 `green_train_of_three_gates_once`, R6+R7 `red_tip_ejects_the_change_at_fault`, R8 `kept_landing_change_ejects_only_its_change`, R9 `train_of_three_lands_as_three_closes`, R10 `move_mid_train_re_stacks_the_rest_and_counts_once` and `train_stops_past_land_moves`, R11 `stopped_train_puts_every_unlanded_change_back`, R12 `close_refuses_a_branch_carrying_another_change`, R13 `close_holds_the_lock_from_its_merge_to_its_close` (portable), R14 `lock_is_reentrant_in_a_thread_and_exclusive_across_threads` (portable; the handoff half is the kept adoption test, which runs the real double handoff), R16 `question_says_the_batch_is_stacked_and_gated_once`, R17 `each_landed_change_records_its_place_in_the_train`, R19 `rerun_resumes_the_train_and_a_second_refuses`. `tests/test_board.py`: `test_a_train_member_shows_its_place_and_an_ejection`, the pinned-copy test extended (R18). R15: `test_close_and_inbox_commit_keep_both_entries` now writes the idea before the lock. `tests/test_land.py`: 21 tests rewritten over the train (`_stack`, `_land_train`), 4 the train makes obsolete removed (R2 and R10's tests cover them). Every slice's tests were seen red first except R10's two, whose logic came with slice 3's close path (said in `plan.md`).

**Gate**: `./check.sh` green, 2565 passed, 18 skipped. Portable subset: 460 passed.

**`plan.md`**: a *Where the build departed* section (the lock primed by a call, not a wrapper, since a test pins `cmd_close` as `_push()`'s caller; `_rebasing()` reads git's state dirs, `REBASE_HEAD` outliving a rebase on git 2.56; checkouts found through `current_branch()` for a worktree mid-rebase; markers left after `--continue` eject; a hand-shipped commit refused via `_land_readiness()`; the four removed tests).

**`notes.md`**: three `- [ ]` items (factory `resolve` without `--onto` now unused by any skill; the agent's reply and `land-resolved` marker left for close's amend; two test drivers that could be one).

**Decisions**

- DECISION: [default] The `train-resolve` prompt names each change's spec and diff (`git show <sha>:…/spec.md`, `git show <sha>`) for the builder to read, rather than inlining n specs and diffs. Going ahead unless told otherwise.
  - OPTION: name them — a short prompt whatever the batch size; the builder reads what it needs with Bash
  - OPTION: inline them — nothing to run, but five specs and diffs can be most of a prompt
  - WHY: R3 says the prompt "holds" them and its test "names" them; naming satisfies both readings and keeps the cost bounded
- DECISION: [default] `eject` is a step of its own in `runs/land-step.md` (R18), its `- PROBLEM:` line reading `ejected from the train: <reason>` with the gate file; the board shows it as a stop. Going ahead unless told otherwise.
  - OPTION: a step `eject` — the record says what happened; the board's stop handling covers it
  - OPTION: `STEP: stop` with `AFTER: eject` — R7's literal "records a stop", but `eject` is not a position on the track
  - WHY: R18 lists `eject` among the steps and asks the board to show it as a stop

## Evidence

```
$ ./check.sh > /tmp/gate-139.txt 2>&1; echo "exit: $?"; grep -E "passed|failed|error|Validation" /tmp/gate-139.txt | tail -5
exit: 0
All checks passed!
2565 passed, 18 skipped in 81.22s (0:01:21)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest tests/test_train.py -q -p no:cacheprovider
.................                                                        [100%]
17 passed in 94.41s (0:01:34)
exit: 0

$ uv run --group dev pytest -q -m portable -p no:cacheprovider
460 passed, 18 skipped, 2105 deselected in 75.98s (0:01:15)
exit: 0

$ uv run --group dev pytest tests/test_land.py -q -n auto -p no:cacheprovider
72 passed in 17.71s
exit: 0

$ uv run --group dev pytest tests/test_board.py tests/test_land.py::test_the_landing_step_record_reads_back_what_it_writes -q -n auto -p no:cacheprovider
199 passed, 18 skipped in 5.10s
exit: 0

$ uv run --group dev pytest tests/test_skills.py -q -n auto -p no:cacheprovider
377 passed in 0.77s
exit: 0

$ for blk in 1 2 3; do awk … .sdlc/work/139-landing-train/checks.md > /tmp/chk$blk.sh; sh /tmp/chk$blk.sh; echo "check $blk exit: $?"; done
check 1 exit: 0
check 2 exit: 0
check 3 exit: 0
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ git log --oneline -1; git status --porcelain | wc -l
e111ebc File 2026-11-18-40
      14
```
