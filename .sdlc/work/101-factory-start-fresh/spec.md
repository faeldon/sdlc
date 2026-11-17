---
id: 101
slug: factory-start-fresh
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 101 — Factory builds start current and share the gate · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Each test named below goes in `tests/test_factory.py` unless another file is named.

R1. `factory.py start` adds two keys to its JSON for both `--for build` and `--for spec`. `base`
    is the branch `_base()` names, or null. `behind` is the number of commits on the base that the
    change's `HEAD` lacks (`git rev-list --count HEAD..<base>`), or null when there is no base.
    `start` still writes nothing. `test_start_says_how_far_behind_the_base_the_change_is` puts
    two commits on `main` after the change branched and expects `behind: 2`, then `0` once the
    branch is current. It fails if the key is missing or wrong.

R2. A new command, `factory.py fresh <NNN>`, brings the change's branch up to date with the base
    branch. It runs `sdlc.py base <change>` of the factory's own version (`_sdlc()`, `sdlc_path()`)
    in the change's worktree. It does this only for a change at a stage a fresh run starts from:
    `plan` or `design`, or `test` when `restart_state()` gives a restart. It prints JSON with these
    keys:
    - `change`
    - `state`: one of `current`, `fast-forwarded`, `rebased`, `resolved`, `held` or `refused`
    - `behind`: how far behind the change was before
    - `from` and `head`: the short `HEAD` before and after
    - `undo`: the command that undoes the move, from `base` or `resolve`
    - `refusals`

    `test_fresh_fast_forwards_a_change_behind_the_base` uses a real worktree two commits behind,
    with its change folder uncommitted. Afterwards `HEAD` is `main`'s tip, the folder's files are
    byte for byte as before, and `undo` names `reset --keep <from>`. It fails if `HEAD` doesn't
    move or the folder is lost.

R3. At `stage: build` (a stopped run starting again), `fresh` moves nothing. It returns
    `state: held` with the reason: that run's rounds were gated and reviewed on that base, and
    landing rebases and gates it again. `test_fresh_holds_a_run_that_stopped_part_way` uses a
    change at `stage: build`, one commit behind, and fails if `HEAD` moves.

R4. When `base` refuses with `resolvable: true`, `fresh` runs `sdlc.py resolve <change>`.
    - **`state: clean`:** `fresh` reports `resolved`. The work is uncommitted on the new base.
    - **`state: conflict`:** `fresh` runs `sdlc.py resolve <change> --abort`, so the worktree is
      back as `fresh` found it (`HEAD`, and the uncommitted files' contents). It exits 1, with a
      refusal that names the conflicted files and the way on: `/sdlc:ship` from the worktree, or
      `sdlc.py resolve`, by the person.

    `fresh` never stashes, never merges the base into the branch, and never forces.
    `test_fresh_resolves_what_git_can_and_stops_on_a_real_conflict` has two cases:
    - (a) An uncommitted edit to a file that `main` then changes differently. `fresh` refuses, the
      file and `HEAD` are as before, `git stash list` is empty, and no merge commit exists.
    - (b) A branch with a commit of its own, uncommitted work, and `main` changing another file.
      `fresh` reports `state: resolved`, `HEAD`'s parent chain holds `main`'s tip, and the work is
      still uncommitted.

    It fails if either case moves the wrong thing.

R5. When `base` refuses and the refusal isn't resolvable, or when no `sdlc.py` of the factory's
    version can be found, `fresh` exits 1 with that reason and moves nothing.
    `test_fresh_refuses_without_its_own_sdlc` stubs `sdlc_path()` to `(None, why)` and fails if
    the exit is 0 or `HEAD` moves.

R6. `/sdlc-factory:build` runs `fresh` in Step 0, after a `start` with no refusals and before the
    spec-writer or the WAIT.
    - From then on it keeps `fresh`'s `head` in place of `start`'s, as the `--head` it gives
      `verdicts`.
    - On a refusal it shows the refusal and stops.
    - Step 1 shows `behind` and what `fresh` did: the state, `from` → `head`, and `undo`. At
      `held`, it says the run resumes `<behind>` commits behind `<base>`.

    The skill gains the rule
    `Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py fresh *)`.
    `test_build_brings_the_change_up_to_date_before_its_spec_writer` (`tests/test_skills.py`)
    fails if Step 0's bash block lacks `factory.py fresh <NNN>`, or if `fresh` comes after the
    first `--task spec`. The existing rule/command tests fail if the rule and the command differ.

R7. `gate_jobs` is a new top-level key in `.sdlc/factory.toml`. It is the most `factory.py gate`
    runs at once across every worktree of the repo.
    - It must be a whole number of 1 or more. The default is 1.
    - It is read from the base branch's copy, as `mode` is.
    - A bad value (0, a bool, text) gives a warning and leaves 1.
    - A checkout value that differs from the base's gives `mode`'s warning ("applies once it
      lands").
    - `config` and `start` show it.

    `test_gate_jobs_is_read_from_the_base_branch_and_checked` fails if the checkout's value is
    used, or if a bad value goes unwarned.

R8. `factory.py gate`, both for a round and with `--land`, takes one of `gate_jobs` slots before
    it runs the check, and holds it until the check has finished.
    - Slot *k* is an exclusive OS lock on `<git common dir>/sdlc-factory-gate-<k>.lock`, so every
      worktree shares it.
    - When no slot is free, the gate prints one line to stderr,
      `<change>: waiting for a gate slot (<N> of <N> in use)`, then retries until one frees.
    - A refusal returns before any slot is taken.

    `test_two_gates_with_a_limit_of_one_run_one_after_the_other` builds two changes in two
    worktrees, each with a build report. Their check is a `sh` script that appends start and end
    timestamps to a file outside both trees and sleeps 1 s. Both gates run at once as
    subprocesses. The test fails if the two intervals overlap, or if neither printed the waiting
    line. The same test with `gate_jobs = 2` fails if the intervals *don't* overlap, which shows
    the limit is what orders them.

R9. A gate's wait is not part of its time. `Seconds:` in the record and `seconds` in the JSON
    count from when the slot is taken. The JSON gains `waited` (seconds, `0.0` when there was no
    wait). The record's shape (`GATE:`, `## Attempt`, `Verdict:`, `Build:`, `Exit:`, `Seconds:`,
    `Tree:`) is unchanged. In R8's limit-one test, the gate that waited reports `waited >= 0.5`
    and `seconds < 1.8`. The test fails if the wait is counted. The existing
    `tests/test_hand_gate.py` copies still pass.

R10. A slot never outlives its gate. It is a lock held on an open descriptor, never a file whose
    existence is the lock, so the OS releases it when the process exits, however it exits. The
    lock files stay in place. `test_a_killed_gate_frees_its_slot` (marked `portable`) starts a
    child Python that loads `factory.py` by path, takes slot 0 and waits. The test kills the
    child (`proc.kill()`), then takes slot 0 itself, and fails if that takes more than 2 s.

R11. The slot code runs on Windows. `fcntl` and `msvcrt` are imported only inside the functions
    that use them. Non-blocking locking is `fcntl.LOCK_EX | LOCK_NB`, and `msvcrt.LK_NBLCK` on
    byte 0. The existing import scan in `tests/test_windows.py` fails on a top-level import.

R12. The docs say what changed:
    - `plugins/factory/README.md`: `gate_jobs` in its config block, `fresh` and the slots under
      *Rounds that converge* and *Mechanism*.
    - `factory.py`'s docstring: what `fresh` writes, and the lock files under the git common dir.
    - `plugins/factory/skills/build/SKILL.md`: R6.
    - `AGENTS.md`'s *Writes before a WAIT* and *The factory* paragraphs: see Contracts touched.

    No test checks the wording. Ship's context-doc pass checks it.

## Design

**Assumptions checked in the code.**
- A change's branch has no commits of its own before ship. `new` commits nothing, and the change
  folder stays uncommitted in the worktree. So `sdlc.py base` usually fast-forwards and carries
  the folder across (`cmd_base()`).
- `base` already keeps `.sdlc/last-id`'s higher number (`cmd_base()`, the `counter` branch).
- `base` aborts a rebase that conflicts and flags it `resolvable` (`cmd_base()`'s `refuse`).
- `resolve --abort` puts the worktree back where `resolve` found it (`cmd_resolve()`).
- The spec-writer runs in the worktree in Step 1, before the WAIT (`SKILL.md` Step 1). Only an
  update in Step 0 lets it draft against current code.
- `verdicts --head` stops a run whose `HEAD` moved (`loop_state()`), so the head the skill keeps
  must be the one after `fresh`.

**`start` (R1).** It gains `base = _base(root)` and
`behind = int(_git(root, "rev-list", "--count", f"HEAD..{base}"))`, or null without a base. It
stays read-only. The `/sdlc-factory:spec` skill gets the same keys, but this change doesn't make
it show them.

**`fresh` (R2–R5).** `cmd_fresh(root, ident)` works in these steps:
1. `find_change()` and the stage check: `plan`/`design`, or `test` with `restart_state()` giving
   a restart. At `build` it returns `held`. Any other stage is refused, using `start`'s wording.
2. It records `from` = short `HEAD` and `behind`.
3. It runs `code, based, said = _sdlc(["base", folder.name], root)`.
   - `action` `current`, `fast-forwarded` or `rebased` passes through as `state`, with `undo`
     taken from `based`.
   - `refused` with `resolvable` runs `_sdlc(["resolve", folder.name], root)`. Its `state: clean`
     (or `current`) becomes `resolved`, with `resolve`'s `undo`. Its `conflict` runs
     `_sdlc(["resolve", folder.name, "--abort"], root)` and refuses with `conflicted`. If the
     abort itself refuses, the refusal includes both texts and `resolve`'s `undo`, so the person
     has the way back.
   - Any other refusal, or a missing `sdlc.py`, is a refusal with its reason.
4. It reports `head` = short `HEAD` afterwards.

It is the same delegation `cmd_land()` uses for `base`. `factory.py` gets no git logic of its own
for this, so `base`'s and `resolve`'s rules (no stash, no merge, only the change's own branch
moves) stay in one implementation. `fresh` is not `factory.py resolve`: that one is landing's,
and leaves a conflict for the builder.

**The build skill (R6).** Step 0 becomes `config && start <NNN> --for build`. If there are no
refusals, it then runs `fresh <NNN>`. These are two bash blocks, since the condition is the
skill's reading of `start`'s refusals, as it is today. `fresh` decides `held` itself, so the skill
has no stage logic. Step 1 shows what `fresh` did, alongside the rest of what it shows. The WAIT
question doesn't change: the update has already happened and been shown, as ship's has.

**Gate slots (R7–R11).** These are new pieces of `factory.py`:
- `DEFAULTS["gate_jobs"] = 1` and `_gate_jobs(root)`, which reads `_base_factory(root)` and
  validates like `_land()`. `load_config()` sets `cfg["gate_jobs"]` and adds the warning when the
  checkout's value differs.
- `_slot_dir(root)`: `git rev-parse --path-format=absolute --git-common-dir`. When git can't
  answer (outside a repo), the gate runs unlimited and its JSON says `slot: null`. It never
  refuses for this.
- `_try_lock(fd) -> bool` and `_unlock(fd)`: non-blocking per platform, with the imports inside
  them. They are this script's own, shaped like `sdlc.py`'s `_flock_lock`/`_msvcrt_lock`, and are
  not imported from it.
- `gate_slot(root, jobs, change)`, a context manager. It opens `sdlc-factory-gate-<k>.lock` for
  k in `range(jobs)` with `os.open(O_RDWR | O_CREAT)` and tries each. When none is free, it
  prints the waiting line once to stderr and sleeps 0.25 s between passes. It yields
  `(k, waited)`, and closes the descriptor in `finally`, which releases a flock. The files stay,
  as `_main_lock()`'s does.
- In `cmd_gate()`, everything from `before = _tree_hashes(...)` through `after` runs inside
  `gate_slot`. `start = time.monotonic()` stays after the slot is taken, and `waited` goes into
  the JSON.

There is no cap on the wait. Each gate holding a slot is bounded by `GATE_TIMEOUT`.

The slots are separate from `sdlc.lock`. A 40 s gate holding the lock that `new` claims numbers
under would stall every `/sdlc:intent`.

### Boundaries

- **Always:** `fresh` moves only the change's own branch, through `sdlc.py`, and prints the undo.
  A gate takes a slot before it runs the check.
- **Asks first:** nothing new. `fresh` is a named write before the build's WAIT (see Contracts
  touched), and everything after it is still behind that WAIT.
- **Never:**
  - a stash
  - a merge of the base into the branch
  - a forced or hard reset
  - an update of a run that stopped part way
  - an agent run before the yes to resolve a conflict
  - a gate's wait counted in its `Seconds:`
  - a change setting its own `gate_jobs`
  - a slot taken by `sdlc.py gate` (the hand gate), which stays as it is

## Contracts touched

- **Writes before a WAIT (AGENTS.md, *Architecture*).** **This needs the policy to change.** The
  list says "Three", and each is a named exception: ship's `base` and `resolve`, and ship's
  `findings.md`. This design adds a fourth: the factory build's `fresh` in Step 0, which is ship's
  own `base` and `resolve`, run through `sdlc.py`. It meets the same conditions. It moves only the
  change's own branch, prints the undo, never stashes or merges, and leaves the worktree as it
  found it on a conflict. `AGENTS.md` would name it, and `SKILL.md` would say it is a named
  exception, as the skill already does for `decisions.md`'s revise line. The alternative that
  needs no policy change is under Alternatives rejected, and it is your call.
- **The factory: "Landing is the one place it commits" (AGENTS.md).** `fresh` commits nothing of
  its own. On a rebase, `sdlc.py resolve` makes its temporary set-aside commit and undoes it
  before it returns, and that commit is `sdlc.py`'s, as landing's commits run through `sdlc.py`.
  The paragraph's wording should still say so: "and `fresh` moves a change's branch onto the base
  before a build, through `sdlc`'s own `base` and `resolve`". That is a wording edit, made in this
  change.
- **`factory.py` never imports `sdlc.py`.** `fresh` runs it as a subprocess (`_sdlc()`), and the
  slot code is the factory's own copy of the lock's shape, not an import.
- **`factory.py gate` is the one place the factory runs a host's command.** That stays true. The
  slot wraps the existing `subprocess.run` and adds no other command.
- **What a change may do unasked is read from the base branch.** `gate_jobs` is read from the base
  branch's `factory.toml`, as `mode`, `[land]` and `[ui]` are. Every worktree then agrees on the
  number of slots, and a change can't give itself more.
- **The gate record's shape, pinned by `tests/test_hand_gate.py` and `tests/test_board.py`.**
  Unchanged. `waited` goes only in the JSON.
- **Never a stash, never a merge of the base (AGENTS.md, *Writes before a WAIT*).** `fresh` gets
  both from `base` and `resolve` and adds no git step.
- **The `git.base` rule.** `fresh` passes no branch name and leaves the trunk to `sdlc.py`. The
  base name `start` reports comes from the existing `_base()`.
- **A run stops if `HEAD` moves.** `fresh` runs before the run's `head` is fixed, and the skill
  keeps the `head` `fresh` returns. A run that stopped part way is never moved (R3).
- **Narrow `allowed-tools`, plain bash blocks, one WAIT (tests/test_skills.py).** One new rule,
  written exactly as the command runs. No `if` in a block: the condition is the skill's reading,
  and `held` is the script's. The WAIT count doesn't change.
- **The scripts run on Windows (tests/test_windows.py).** The platform modules are imported inside
  functions, every lock path is built from a `Path`, and the kill test is `portable`.
- **`factory.py`'s docstring is its contract.** It says each command writes only where its name
  says, and nothing under `.git/` but by the landing. It gains `fresh` (the change's branch,
  through `sdlc.py`) and `gate`'s lock files under the git common dir.

## Alternatives rejected

- **Update inside `start`.** `start` is read-only, and `/sdlc-factory:spec` calls it as well. Every
  `factory.py` command writes only what its name says.
- **Update after the yes, in Step 3.** This needs no policy change, but the spec-writer would
  draft in Step 1 against the code as it was hours earlier, which is the cost this change exists
  to remove. It is kept as your alternative to the policy edit, not the recommendation.
- **The builder resolves a conflict at build start.** That is a paid agent run before the person
  has agreed to the run, or a new loop step ahead of `build`. It would only matter for a restart
  or a resumed run, the only states with code that could conflict. Ship and landing already
  resolve with an agent at the point where one is approved.
- **Updating a run that stopped part way.** Its gated, reviewed rounds would then stand on code
  they never saw. The gate's `build_hash()` reads the report and snapshot, not the base, so the
  gate would wrongly read as current.
- **Merging the base into the branch.** Close would put the merge on the base's first-parent line,
  which `closed_changes()` walks.
- **A lock that is a file's existence, or a pid file.** A crashed gate leaves it behind, which
  breaks the constraint that no lock outlives its gate.
- **A lock in the tree or under `.sdlc/`.** It would show in `git status` and differ per worktree,
  so gates in different worktrees wouldn't share it.
- **Reusing `sdlc.lock`.** `new` would wait behind every gate.
- **Limiting pytest's `-n`.** The plugin doesn't know a host's check is pytest. Only the number of
  gates running at once is the factory's to set.
- **A `Waited:` line in the record.** It changes a shape that the board and the hand gate copy, to
  carry a number nothing reads yet.
- **Slots shared with `sdlc.py gate`.** That would make the lock file's name a contract across the
  two plugins, and the intent is about the factory. It is left as a possible seed.

## Verification

```bash
uv run --group dev pytest -q tests/test_factory.py -k "behind or fresh or gate_jobs or two_gates or killed_gate"
uv run --group dev pytest -q tests/test_skills.py tests/test_windows.py tests/test_hand_gate.py tests/test_board.py tests/test_land.py
uv run --group dev pytest -q -m portable
./check.sh
```

Healthy output: every named test passes. `test_two_gates_with_a_limit_of_one_run_one_after_the_other`
takes about 2 s, and its waiting gate's JSON shows `waited` near 1 and `seconds` near 1. The
existing gate, land and hand-gate tests pass unchanged. `./check.sh` ends green: ruff, the format
check, pytest, and `claude plugin validate --strict`.

By hand, from the main checkout, with one change worktree a few commits behind `main`:
- `factory.py start <NNN> --for build` shows `behind: <n>`.
- `factory.py fresh <NNN>` shows `state: fast-forwarded`, its `undo`, and `head` equal to
  `main`'s short sha.
- Two `factory.py gate` runs started at once in two change worktrees: one prints
  `waiting for a gate slot (1 of 1 in use)` and starts only when the other has finished.
