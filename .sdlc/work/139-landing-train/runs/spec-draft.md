---
id: 139
slug: landing-train
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 139 — A landing train: the batch is integrated once, gated once, and its conflicts resolved once · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

In these requirements, "train" means one `/sdlc-factory:land` of the batch `land-check` gives. "Stacked commit k" is change k's commit once it has been rebased onto stacked commit k−1. Stacked commit 0 is the base branch's tip when the train starts. "Pre-train commit" is the change's commit as `land` made it, before any rebase. Tests named here are new unless marked as kept. Most go in a new `tests/test_train.py`.

1. **R1. Each change stacks on the one before.** Each change rebases in its own worktree, from a clean tree, in `land-check`'s order. Change 1 goes onto the base branch's tip and change k onto stacked commit k−1. There is no merge, no stash and no `--force`. `test_a_train_stacks_each_change_on_the_one_before` checks that `git rev-parse <k>^` equals stacked commit k−1. It also checks that `<trunk>..<k>` holds exactly changes 1..k's commits, one each.
2. **R2. `land` no longer rebases.** `factory.py land <NNN> --by …` ships and commits, as it does today, and then stops with `state: committed`. All bringing up to date belongs to the train. The commit it leaves is recorded as the change's pre-train commit. `test_land_commits_and_leaves_the_rebase_to_the_train` asserts the branch's parent is still its old base after `land`.
3. **R3. One landing agent resolves a stack conflict.** A conflict while stacking change k goes to the `builder` agent, run as `agent <k> --task train-resolve` in k's worktree. Its prompt holds every change in the train: its `spec.md` (or `intent.md` at Tier 1) and its commit's diff. It is never a resumed session of any change's own builder. `.sdlc/last-id` still settles itself (`_settle_counter()`). `--continue` still refuses a leftover marker and aborts on a second conflict. `test_a_train_conflict_goes_to_one_agent_with_every_change` asserts the prompt names every change's spec heading and diff. It also asserts the session id lands in k's `runs/builder.sessions`.
4. **R4. Each resolution is reviewed again.** Every reviewer at change k's depth reviews it, after the tip's gate passes. A change in a batch landed `by=auto` closes only once that review passes. That keeps `cmd_land_close()`'s rule. `test_a_train_resolution_is_reviewed_before_it_closes` asserts `land --close` refuses k while that review is missing.
5. **R5. One gate for a green train.** A train of n ≥ 2 with no red gate, no fix and no move runs the base branch's `[commands] check` exactly once. It runs at the tip, in change n's worktree, before any reviewer reads any change. A train of one whose change didn't move runs none, as a `current` landing does today. `test_a_green_train_of_three_gates_once` counts the `## Attempt` sections across every change's `build/land-*.gate.md` and expects 1.
6. **R6. A red tip is bisected by prefix.** Each prefix p is gated in change p's worktree, at stacked commit p. The prefix of none, the base branch, is taken as green. The first red prefix's last change is the one at fault. One ejection costs at most ⌈log₂ n⌉ gates beyond the tip's. `test_a_red_tip_ejects_the_change_at_fault` uses three changes and a check that fails while change 2's file exists. It asserts that change 2 is ejected, that 1 and 3 land, and that the gate ran at most 1 + 2 times before the re-stack.
7. **R7. An ejected change goes back as it was and keeps its reason.** Its branch goes back to its pre-train commit with `git reset --keep`, and the undo is printed. Its `runs/land-step.md` records a `stop` that reads `ejected from the train: <reason>`, with the gate file that shows why. That record is amended into its commit. Nothing of it reaches the base branch. The changes after it re-stack onto the change before it, and their tip is gated again. The same test asserts four things:
   - No commit on `<trunk>` touches change 2's folder or its file.
   - Change 2's tree, outside its own folder, equals its pre-train commit's.
   - Change 2's parent is its old base.
   - The re-stacked tip was gated.
8. **R8. A failure in one change ejects that change.** That covers its acceptance checks failing on its stacked commit, a landing review that keeps a change, and a reply still unreadable after its one mend. That change is ejected as in R7 and the rest go on. It does not stop every change after it. `test_a_kept_landing_change_ejects_only_its_change` checks this.
9. **R9. A batch of three lands as three closes.** Once the tip is green and every review has passed, the changes close in order through `sdlc.py close`. Before change k closes, its branch is rebased onto the base branch past the commit it was stacked on (`git rebase --onto <trunk> <stacked k−1>`). On the train's own branch that steps over only the train's own `Close` commits. `test_a_train_of_three_lands_as_three_closes` checks four things:
   - The first-parent line reads A, `Close A`, B, `Close B`, C, `Close C`.
   - `closed_changes()` returns three records in that order.
   - Each record's `sha` is its `Close` commit's parent.
   - Each holds its `intent.md` at `stage: shipped`, with `metrics` parsed from its `Close` commit.
10. **R10. Any other commit on the base branch is a move.** The train records the base branch tip it expects next: stacked commit 0 before the first close, then the last `Close` it wrote. A different tip before a close means the base moved. The rest of the train re-stacks onto the base, is gated again at its new tip, and is reviewed as a re-stack calls for. A move counts once for the train against `[land] moves`. Past that limit, every change not yet landed goes back to its pre-train commit and the train stops. `test_a_move_mid_train_re_stacks_the_rest_and_counts_once` uses an `inbox-commit` between `Close A` and B. It asserts one move, one more gate, and B and C landed with `Close B`'s parent being B.
11. **R11. A stopped train leaves no branch holding another change's commit.** On any stop, every change not landed goes back to its pre-train commit. `test_a_stopped_train_puts_every_unlanded_change_back` checks this.
12. **R12. Close refuses a branch that carries another change's commit.** `sdlc.py close` refuses, before writing anything, when any commit in `<trunk>..<branch>` adds or changes a path under another change's folder (`work_rel()`/`<other NNN-slug>/`). A crashed train could leave such a branch, and its fast-forward would put the other change on the base branch with no `Close`. `test_close_refuses_a_branch_carrying_another_change` checks this.
13. **R13. Close holds the lock from its merge to its `Close` commit.** `cmd_close()` holds `_main_lock()` from before its `merge --ff-only` until `_close_commit()` has committed. It lets go before `mark_issues`, the worktree's removal, the push and the cleanup. A rerun that finds the change already merged takes the lock before its `remove folder` step. `test_close_holds_the_lock_from_its_merge_to_its_close` races the two in threads, as `test_inbox_commit_waits_for_the_lock_claim_takes` does. Thread 1 runs `cmd_close`, paused just after its merge. Thread 2 runs `cmd_inbox_commit`. The test asserts thread 2 has not finished within 0.5 s while thread 1 is paused. It also asserts the first-parent order is the change's commit, `Close`, then `File`. Marked `portable`.
14. **R14. The lock is reentrant within a thread and inherited by a handoff.** `_close_commit()` takes no second OS lock inside close's hold, so it can't deadlock itself. Another thread, or another process, still waits. In this repo, close's `_handoff()` to the merged code tells its child, through the environment, that the parent holds the lock. The child takes none, and that variable is cleared before the child starts any other process. `test_the_lock_is_reentrant_in_a_thread_and_exclusive_across_threads` covers the first part (`portable`). A handoff test covers the second: a close that hands off finishes within its timeout.
15. **R15. The existing reread test still proves the reread.** `test_close_and_inbox_commit_keep_both_entries` (kept) files its idea before close takes the lock, no longer from inside `fix_trailers`, which would now run under the hold. It still asserts both entries are kept.
16. **R16. The one question says what a train does.** `land_question()` says that the changes are:
    - stacked in this order on `<base>`;
    - gated once at the tip;
    - when the tip is red, bisected, with the change at fault left out (with why) and the rest landed;
    - resolved by one landing agent and reviewed again when they conflict;
    - brought up to date as often as `<base>` moves, up to `<moves>` times;
    - closed in order.

    `clear` and every signal stay as they are. `test_the_question_says_the_batch_is_stacked_and_gated_once` pins the wording.
17. **R17. Each change records its part in its own commit.** `runs/land-train.md` holds `TRAIN: <k> of <n>`, `STACKED ON: <NNN-slug or base>`, the tip's gate (verdict, commit, and the change folder whose gate file holds it) and each bisection gate it took part in. It is amended into the change's commit before it closes. `test_each_landed_change_records_its_place_in_the_train` reads it from each `Close` commit's parent.
18. **R18. Each change keeps its own landing track on the board.** `runs/land-step.md` gains a `TRAIN: <k> of <n>` line and the steps `stack` and `eject`. The board places `stack` at the rebase position, shows `eject` as a stop with its reason, and shows "k of n in a train". Copies of the parsing are pinned in `tests/test_board.py` (`test_a_train_member_shows_its_place_and_an_ejection`).
19. **R19. A train survives a rerun.** Its state (order, pre-train and stacked commits, the expected tip, gates, ejections, moves) lives in `sdlc-factory-train.json` in the git common dir, never in a tree. A rerun of `/sdlc-factory:land` resumes it. A second landing refuses while one is under way. `test_a_rerun_resumes_the_train_and_a_second_refuses` checks this.

## Design

### Assumptions, each checked in the code

- **Moving the base branch.** `cmd_close()` only fast-forwards (`merge --ff-only`). `closed_changes()` reads each `Close` commit's first parent as the change. So a change's branch has to sit exactly on the base branch's tip when it closes. A branch stacked on another change's commit must never reach close (R11, R12).
- **The register stays off the branch.** A change's branch never edits the register (`held_entries()`, AGENTS.md *The register*). A `Close` commit only removes its own folder and edits the register. So rebasing change k+1 past `Close k` touches paths disjoint from k+1's commit, and it can't conflict, `.sdlc/last-id` aside, which `_settle_counter()` already handles.
- **The lock today.** `_main_lock()` is taken in exactly three places: `claim()`, `cmd_inbox_commit()` and `_close_commit()`. `flock` and `msvcrt.locking` both block a second descriptor in the same process, so nesting it would deadlock (R14).
- **Rebase tools the factory already has.** `factory.py resolve` already runs the landing's conflicting rebase itself, in the change's worktree. `cmd_base()` already prints `git reset --keep <before>` as its undo.
- **The board reads per change.** `scripts/board.py` reads `runs/land-step.md` per change folder (`LAND_STEPS`, pinned). No train-wide folder exists, so none is added.
- **The check reads `.sdlc/work/`.** This repo's own gate reads files under `.sdlc/work/` (`tests/test_nothing_local.py` scans every tracked file). So a register edit on the base branch can change the gate's verdict. That is why any commit not written by the train is a move (R10). It is not waved through as "only the register".

### The train, step by step

`factory.py train` is a new command. Like `verdicts` in the build loop, it reads `sdlc-factory-train.json` and the change folders and names the next step, writing nothing but the state file (`--record`). The skill runs the step it names and asks again. The steps:

1. **commit**: for each change, `land <NNN> --by …` (R2). The rules stay as they are today: refusals before any write, dispositions, ship, the composed message, `Sdlc-Landed`. The pre-train commit is recorded.
2. **stack k**: `resolve <k> --onto <stacked k−1>`. This is `cmd_resolve()`'s rebase given a target, so the base-branch case is `--onto <trunk>`. It returns `clean`, `conflict` or `stacked`. On `conflict`: `agent <k> --task train-resolve`, then `resolve <k> --continue`, recorded in `runs/land-resolved` as today (R3). Each moved change gets a landing round (`reviews/land-<n>/`). A `yes, with a fix` is made here, on its change's stacked commit, before the gate, and the changes above it re-stack. So the one gate covers the fix as well.
3. **gate**: `gate <n> --land` at the tip (R5). When it fails, **bisect p** gates prefixes in change p's worktree until the first red prefix is found. Then **eject p** (R6, R7): reset to the pre-train commit, amend the record in, and re-stack p+1..n onto stacked commit p−1, which may conflict again and go to the agent. Then gate the new tip again. If the first change is ejected twice in a row, the base branch's own check is the likelier fault, so the train stops (R11) instead of ejecting everything.
4. **review**: for each moved change, `land-verdicts <k>` as today. That covers the behaviour check on its stacked commit, every reviewer at its depth on a resolution or a fix, `accept` on its stacked commit, `verify` and `mend`. The tip gate's verdict stands in for each change's own landing gate. `_land_gate_state()` reads the train's tip record when change k's stacked commit is an ancestor of the gated tip. A per-change stop ejects that change (R8) and goes back to step 2 for the changes above it.
5. **close k**, in order:
   1. Check the base branch's tip against the expected tip (R10).
   2. `git rebase --onto <trunk> <stacked k−1>` in k's worktree. For k = 1 this is a no-op.
   3. `land <k> --close`, which writes `runs/land-train.md`, amends the record in, and runs `sdlc.py close`.
   4. Record the new `Close` as the expected tip.

The board and the history read `runs/land-step.md` and `runs/land-train.md` from each change's own folder. Ejection and stop reuse `_close_stopped()`'s amend.

### Close's lock

`_main_lock()` becomes reentrant per thread: a thread-local depth per lock path, and only the outermost hold takes the OS lock. `cmd_close()` wraps `merge` through `remove folder` in one hold. That covers `verify`, `measure` and the tracker's `archive`, so a claim or an idea filed meanwhile waits for one tracker call. `_close_commit()`'s own `with _main_lock()` then nests. `_handoff()` sets `SDLC_LOCK_HELD=<lock path>` for its child, which reads and clears it. The parent waits on the child, so the hold is sound. The variable never reaches `close_cleanup`, `measure`'s subprocesses or a tracker.

### Edge cases

- **A train of one:** stacking onto the base is today's `base`, and a change that didn't move needs no gate (R5).
- **A flaky gate:** bisection may eject the wrong change. Ejecting is always safe, because nothing red lands and the ejected change gets its gate file as the reason.
- **A crash:** a crash mid-train leaves state that the next `/sdlc-factory:land` resumes (R19), and close's refusal (R12) catches a hand close of a stacked branch.
- **A push failure** at close k stays `push_failed`. The change has landed and the train goes on.

### Boundaries

- **Always:** each change keeps its own commit, its `Sdlc-*` trailers and its `Close`, right after it on the first-parent line. Conflicts go to an agent and are reviewed again. A change at fault is ejected, with its reason.
- **Asks first:** nothing new. The one question (R16) covers stacking, ejecting and closing in order, and `clear` passes it by itself only as today.
- **Never:** a merge of the base into a branch, a stash, `--force`, or `reset --hard`. No `Close` written anywhere but by `sdlc.py close` on the base branch. No change landed through a branch holding another change's commit. `/sdlc:ship` and `/sdlc:close` by hand are unchanged, apart from close's lock span and its R12 refusal. Selective tests are not built.

## Contracts touched

- **The first-parent line (`closed_changes()`, *Closing*, *Releasing*).** It keeps one `Close` per change, right after the change's commit. Each change still closes alone through `sdlc.py close`'s fast-forward (R9). R12 makes it impossible for a stacked branch to break this.
- **"Never a merge of `main` into the branch, never a stash, never `--force`" (*Writes before a WAIT*, `cmd_base()`).** Stacking uses rebase. Ejecting and undoing use `reset --keep`, which refuses to lose work, and only on the change's own branch. The train writes nothing before the WAIT.
- **"Only the builder edits; agents that judge have no Write; no agent commits" (*The factory*).** The landing agent is the `builder` with a new task, and every git step is the script's.
- **"Landing is the one place it commits, through `sdlc`'s own `ship`, `base` and `close`" (*The factory*).** Commits still come only from `ship`, `close` and the existing record amends. Stacking is the factory's own rebase, which `resolve` already does. **This needs an edit to the policy doc's factory paragraph, AGENTS.md**, to say the train stacks through `resolve --onto` and that `land` no longer runs `base`. It describes new behaviour and changes no tested invariant.
- **"The `Close` commit ... under the same `_main_lock()`" (*Closing*).** The span widens from merge to `Close`. **AGENTS.md's *Closing* line and `_main_lock()`'s docstring change to say so.** This is the fix the intent asks for.
- **Gate slots stay separate from `sdlc.lock`.** The train's state file has its own name in the git common dir. It is neither `sdlc.lock` nor a gate slot.
- **The gate passes itself only when no change carries a risk signal.** The signals don't change. Ejecting lands less, never more, so a `by=auto` train may eject without asking.
- **The base branch name is `trunk`.** It is never written as `main` in a git call (`test_no_git_call_names_main_itself`), and every new git call takes `trunk` or `_base()`.
- **`factory.py` never imports `sdlc.py`.** The board reads the train's records with pinned copies, and `sdlc` reads nothing of the train's state.
- **Skills.** The land skill keeps exactly one WAIT. It gains `Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py train *)` and loses no rule it still runs. Its bash blocks stay plain.
- **Windows.** The thread-local reentrancy works with `msvcrt` as well as `flock`. Every new `write_text` passes `newline="\n"`, and the lock tests are `portable`.
- **The gate's guarantee: this weakens, and it needs your yes.** Today every change is gated as it reaches the base branch. In a train, only the tip is gated. The base branch passes through prefixes (changes 1..k with their `Close` commits) that were never gated on their own. Each is a prefix of a green tip. The intent asks for this trade, but it is a guarantee given up, so it's stated here.

## Alternatives rejected

- **Ejecting by the files the failing tests touch.** The gate is the host's opaque `[commands] check`. Mapping a failure to paths would mean the plugin knowing the host's test runner, which breaks *Mechanism vs. policy*. Prefix bisection costs at most ⌈log₂ 5⌉ = 3 gates at the default batch size.
- **A separate landing branch and worktree off `main`.** Every change's branch would then have to be moved onto it afterwards, and each `Close` commit would need its own rebase of everything above it. Stacking each change's own branch puts the stack in the worktrees that already exist. Prefix p is then simply change p's HEAD, so bisection needs no checkouts.
- **Writing the `Close` commits on the landing branch and fast-forwarding `main` once.** This would mean a second implementation of close against a branch that isn't the base. That breaks "ship, base and close have one implementation", and it puts measuring and archiving off the base branch.
- **Each change's own builder resolving in turn.** It never sees the other changes' specs, and that context is exactly what a cross-change conflict needs. The Outcome names one landing agent.
- **One builder session resumed across every conflict.** A session is stored per working directory, and each conflict is in a different change's worktree.
- **Holding `_main_lock()` for the whole train.** It would block every `/sdlc:new` and every idea filed for n closes, including n tracker calls. A move costs one re-stack and one gate.
- **Releasing the lock before `_handoff()` and taking it again in the child.** That reopens the window the intent closes, between this repo's merge and its `Close`.
- **Treating a register-only commit on the base branch as no move.** This repo's own check reads `.sdlc/work/`, so the gate's verdict can depend on it.
- **Running only the tests that cover a move's untouched paths** (weighed, as the intent asks). The same mechanism-vs-policy objection applies, and a move already costs only one gate at the tip. Left for a change of its own if the retro shows move gates dominating.
- **Leaving an ejected change rebased onto the stack.** Its branch would hold the commits of changes before it. `/sdlc:close` by hand would then fast-forward them onto the base branch with no `Close`.

## Verification

```bash
uv run --group dev pytest tests/test_train.py tests/test_land.py tests/test_register_lands.py tests/test_bugs.py tests/test_board.py -q -n auto
uv run --group dev pytest -q -m portable          # the lock's tests, as CI's Windows job runs them
./check.sh                                         # ruff check, ruff format --check, pytest -n auto, claude plugin validate --strict
```

Healthy output: every test passes, R1–R19's included. `test_close_holds_the_lock_from_its_merge_to_its_close` finishes in well under 10 s, with no hang. `check.sh` ends with the validator's success line.

Manual check, in a scratch host with the factory enabled and three ready changes, two of which touch one file:
- Run `/sdlc-factory:land`. Its question names the train.
- After landing, `git log --first-parent --format=%s <base>` reads change, `Close`, change, `Close`, change, `Close`.
- Each landed change's `runs/land-train.md` shows the single tip gate.
- The board shows each change at "k of 3" while it runs.

