---
id: 091
slug: hand-gate-record
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 091 — A gate run by hand leaves a record the board and status read · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. R1. `sdlc.py gate NNN` runs the base branch's `[commands] check` and never the checkout's. It
   reads it from `_config_at(home, "refs/heads/<trunk>")`, runs it in the change's checkout
   (`checkout_of(folder)`) through `_sh()` with `encoding="utf-8"`, `errors="replace"` and
   `stdin=DEVNULL`, and allows up to `GATE_TIMEOUT` (1,800 s, the factory's value). A test puts one
   check on the base branch and a different one in the checkout's uncommitted config. It fails if
   the checkout's check runs.
2. R2. `gate` refuses, exits 1 and writes nothing in each of these cases:
   - `trunk_refusal()` names a reason.
   - The base branch's config doesn't parse or names no check.
   - `_one_change()` matches no change, or more than one.
   - The change's folder holds `runs/` (a factory run, which `factory.py gate` gates).
   - The checkout's `HEAD` isn't on the change's branch.

   One test per refusal asserts the exit code and that no `build/gate.md` exists.
3. R3. Each run adds one attempt to `.sdlc/work/NNN-slug/build/gate.md`, in the factory's record
   shape:
   - The first line is the latest attempt's verdict, `GATE: PASS` or `GATE: FAIL`. Earlier attempts
     stay as they were.
   - The new attempt is a `## Attempt <k>` section with `Verdict:`, `Command:`, `Build:`, `Exit:`,
     `Seconds:` and `Tree:` lines.
   - Then `Last 80 lines of its output:`, each line indented four spaces, or `(no output)`.

   A pin test runs `factory.py gate` and `sdlc.py gate` on the same fixture and the same check. It
   asserts the two files match line for line, with only the `Build:` and `Seconds:` values masked.
   It also asserts that the copies of `ATTEMPT_VERDICT_RE`, `BUILD_RE`, `SECONDS_RE`, `GATE_TAIL`,
   `GATE_TIMEOUT`, `CLONE_MARK` and `HOME_MARK` are the same as `factory.py`'s.
4. R4. The verdict is `PASS` only when the check exits 0, finishes within the timeout and leaves
   unchanged every path the hash covers (R6). Anything else is `FAIL`:
   - A timeout records `Exit: timeout`.
   - A check that can't start (`OSError`) records `Exit: didn't run`.
   - A changed tree records `Tree: changed: <paths>`.

   The command prints a JSON summary (`change`, `attempt`, `verdict`, `exit`, `seconds`, `tree`,
   `to`, with `to` as `as_posix()`). It exits 0 on PASS and 1 on FAIL. One test covers each of the
   four outcomes.
5. R5. Before anything is written, the output passes through `_hand_placeholders()`, a copy of
   `factory.py`'s `_placeholders()`. It replaces the main checkout's root, then the change's
   checkout, then the home directory, with `<path-to-clone>` and `~`. Each path is matched as given,
   resolved and in POSIX form, longest first. A test feeds the same text holding all three paths to
   both functions, inside a repo with a worktree, and fails if their outputs differ.
6. R6. `hand_build(checkout, trunk)` is the build that the record and the readers compare. It is the
   first 16 hex digits of a sha256 over two things:
   - The merge-base of `trunk` and `HEAD`.
   - Each path the branch changed since that merge-base, committed, uncommitted, and untracked but
     not ignored, sorted, written as `path\0<sha256 of its bytes, or "deleted">`.

   Paths under `work_rel()` and `.sdlc/<STATE_FILES>` are left out. Tests pin each of these:
   - An unchanged tree hashes the same twice.
   - Committing the uncommitted work unchanged keeps the hash.
   - Editing a code file changes it.
   - Editing only the change's own folder (`notes.md`, the record itself) leaves it alone.
   - Rebasing onto a base branch that has moved changes it.
7. R7. `hand_gate(folder, home, trunk)` is the one reader, used by both the board and status:
   - Without `build/gate.md`, it returns None.
   - Otherwise it returns `{"verdict", "current", "exit", "seconds", "attempts", "fails", "path"}`,
     taken from the last attempt. `current` is true only when that attempt's `Build:` equals
     `hand_build()` now, and the checkout is on the change's branch.
   - A record with no `## Attempt` section, or no verdict, comes back with a `problems` line and
     `current: false`. It never raises.

   Tests cover all three cases.
8. R8. On the board, a manual change at a stage `_seen()` already moves on, `build` included, whose
   record is current with `PASS` gets `seen: "test"`. It shows in the Test column with
   `/sdlc:ship` next, even when ship's review hasn't run yet. After an edit outside the change's
   folder, the same card is back in Build. This is pinned by a test that gates, reads the card,
   edits a file and reads it again.
9. R9. A current `FAIL` record keeps the card in Build. Its `next` reads `the gate is red: read
   build/gate.md, fix it, then sdlc.py gate NNN`. Pinned by a test.
10. R10. Every manual card carries `gate`, R7's dict or None, which `board.html` shows as a `gate
    green` or `gate red` badge. The page builds it with `h()`/`textContent`, like every other node.
    A factory card has no `gate` key, and its `seen` stays None even when its folder holds a
    `build/gate.md`. Pinned by a test.
11. R11. In `/sdlc:status`, an open change with a current record adds `· gate green` or
    `· gate red` to its line. A stale record or no record adds nothing. Pinned by a test over
    `print_status`'s output for all three.
12. R12. Close's `measure` adds no trailer and no key. `_factory_files()` stays None for a change
    built by hand that has a `FAIL` record: there is no `decision.md`, and `build/gate.md` doesn't
    end in `.gate.md`. `metrics.py` counts a `Bash` call that runs `scripts/sdlc.py gate` as a
    `check` event in the stage it falls in, failed when its result is an error, as it counts
    `commands.check` now. Pinned by a test built on the shape of
    `test_tool_prompts_and_gate_runs_are_counted`, plus one asserting `_factory_files()` is None.
13. R13. `gate` is in `OWN_SCRIPT_CMDS`. It is not in `READ_ONLY`, `ALLOW_RULES` or any skill's
    `allowed-tools`. A test asserts all four.
14. R14. The record is written with `newline="\n"` and `encoding="utf-8"`, and contains no `\r`.
    It is marked `portable`.
15. R15. `docs/REFERENCE.md` documents the command, its record, and the board's and status's
    reading of it, and `./check.sh` passes.

## Design

**Where it lives.** All of the following goes in `scripts/sdlc.py`, beside `cmd_accept()`, which it
mirrors:
- `cmd_gate(root, ident)`.
- `hand_build()`.
- `hand_gate()`.
- `_hand_placeholders()`.
- The copied constants and regexes, under a comment saying they are `factory.py`'s, pinned by a
  test.

The core still never imports or runs the factory. The tests read both, as `test_board.py` already
does for `SECONDS_RE`.

**Running it.** `cmd_gate` resolves `home = main_root(root)` and the trunk from `load_config()`,
then asks `trunk_refusal()` first. It finds the folder with `_one_change()`, refuses a factory folder
(`runs/` exists), and finds the checkout with `checkout_of()`. It refuses when `git rev-parse
--abbrev-ref HEAD` there isn't the folder's name, because a record must judge the change's own
branch. The check comes from `_config_at(home, f"refs/heads/{trunk}")["commands"]["check"]`, never
`load_config()`'s, so a change can't edit the gate that judges it. That is the rule `factory.py`'s
`_base_check()` and `_risk_report()` already follow.

**The tree check and the hash share one walk.** `_hand_paths(checkout, trunk)` lists the paths and
`_hand_digests()` hashes each one. Paths come from three places:
- `git merge-base <trunk> HEAD`.
- `git diff -z --name-only --no-renames <fork>`, which covers committed and uncommitted changes.
- `git ls-files -z --others --exclude-standard`.

Both listings use `-z`, so neither quotes a path. Paths under `work_rel(home)/` and the state files
are dropped. `cmd_gate` takes the digests before and after the run: the paths whose digest changed
are the `Tree:` line, and the "before" digests are the `Build:` hash. So the record names exactly
the build it judged, even when the check changed the tree. Because the hash is over content, ship's
commit of unchanged work doesn't make a green record stale. Including the merge-base means a rebase
onto a base that has moved does make it stale. A base branch that moves without a rebase doesn't;
the card's existing `behind` count says that.

**The record.** It is written as `factory.py`'s `cmd_gate` writes its own: the new `GATE:` first
line, the earlier attempts kept below it, then the new section. The output's tail goes through
`_hand_placeholders()` first. The file is `build/gate.md`: beside the factory's
`build/round-<N>.gate.md`, but matched by none of its readers. `build_round()` globs `round-*.md`,
`_factory_files()` and `history_samples()` take only names ending in `.gate.md` or starting with
`round-`, and `_factory_files()` returns None without a `decision.md` anyway.

**Reading it.** `hand_gate()` parses the file line by line, as `read_gate_file()` does (output
lines are indented, so they never match a record line). It adds `Seconds:` and compares the last
`Build:` against `hand_build()` now. Each read hashes the change's touched files once, which is
cheap for a change's diff and runs only for manual cards and status lines.

**The board.** `_entry()` sets `entry["gate"] = read("build/gate.md", lambda: sdlc.hand_gate(...),
None)` for manual changes only, adding its `problems` to the card's. `_seen()` goes in this order:
1. Not manual, or not at a stage it moves on: None.
2. `findings.md` exists: `test`.
3. The gate record is current with `PASS`: `test`.
4. The stage is `build`: None.
5. Anything else falls through to the existing touched-path inference.

In `next_action()`, a red current gate comes before the `build` branch and returns R9's sentence.
`column()` is unchanged. `board.html` adds the badge next to the existing `by hand` badge.

**Status.** In `main()`'s status loop, beside `factory_stop()`, `rec["gate"] = hand_gate(...)` is
set for open changes without `runs/`. `print_status` adds the `· gate green` or `· gate red` mark
when `current` is true.

**Metrics.** Where `metrics.py` already matches `commands.check` as a prefix of the Bash command
(about line 703), it also matches a command containing `scripts/sdlc.py gate`, using the same event
and the same `ok` handling. This adds a case to an existing event; it doesn't redefine one.

**Boundaries.**
- *Always:* a run writes one attempt to the change's own `build/gate.md` and nothing else, and
  `/sdlc:ship` commits it with the change because ship stages the folder.
- *Asks first:* the command is never pre-approved, so the harness prompts with the command shown,
  as it does for `accept`.
- *Never:* the board and status run nothing and write nothing; `stage:` is never stamped; the
  factory's gate, readers and trailers are untouched; the person's commit or ship's Step 1 is never
  replaced.

## Contracts touched

- **The board writes nothing (`scripts/board.py`'s docstring, AGENTS.md "The board").** The board
  only reads `build/gate.md` and hashes files. Only the person's command writes.
- **A command that writes asks `trunk_refusal()` first, and never names `main` in a git call.**
  `cmd_gate` asks first and passes `trunk` (`test_no_git_call_names_main_itself`).
- **The change's path comes from `work_rel()` (`test_no_literal_work_path_in_the_script`).** The
  record's path and the hash's exclusion both come from `work_rel(home)`.
- **Writes aren't pre-approved.** `gate` runs a command and writes, so it stays out of `READ_ONLY`,
  `ALLOW_RULES` and every `allowed-tools`, like `accept` (R13). No skill runs it, so no skill names
  it.
- **The change's own script (`OWN_SCRIPT_CMDS`).** `gate` writes and is safe to rerun (each run
  only adds an attempt), so it runs the change's own `sdlc.py` once the change edits `scripts/`,
  this change included. That means a change could alter the code that records its own gate.
  However, the record is only information for the board and status: ship's Step 1 still runs the
  base branch's gate itself. The check *command* comes from the base branch, whichever copy of the
  script reads it.
- **The scripts run on Windows.** The run goes through `_sh()` (no `shell=True`) with
  `encoding="utf-8"` and `errors="replace"`. The write uses `newline="\n"`, paths shown are
  `as_posix()`, and no platform-only module is imported (R14).
- **Copies are pinned by tests.** The direction is reversed here: the core copies the factory's
  record shape and `_placeholders()`. R3 and R5's tests pin them, so the two records can't disagree.
- **Nothing about a project or a workspace.** Committed records hold `<path-to-clone>` and `~`,
  never a machine's paths (R5). Test data uses neutral names.
- **The metrics trailer contract.** No trailer is added or redefined (R12). `checks=` keeps its
  meaning when the gate runs through `sdlc.py gate`.
- **Mechanism vs. judgment.** Whether the gate is green, and whether it is current, is decided by
  the script. No skill judges either.

None of these needs to change.

## Alternatives rejected

- **Reusing `build/round-1.gate.md`.** The factory's readers treat a round file as a reviewed round
  with a builder report: `verdicts`, `_factory_files()`'s `gate_fail`, and `history_samples()`'s
  typical times. A hand gate would leak into all three, and the hash means something different
  there (report plus snapshot).
- **Hashing `HEAD`.** Work built by hand is usually uncommitted until ship, and ship's own commit
  would make every green record stale.
- **The factory's `build_hash()`.** It hashes a builder report and a snapshot, and a hand build has
  neither.
- **Stamping `stage: test` on a green gate.** 080 chose to infer the stage from what a change
  touched, so nothing writes `stage:` between plan and shipped. A stamp would also remain after a
  later edit, which is the stale state this change exists to show.
- **The board running the gate.** This breaks the board's no-writes, no-commands rule, and a
  request could start a 30-minute process.
- **A separate "Gate green" column.** Test already means "built, ready for ship's review". A badge
  separates the two states without another column for 086 and 088 to place.
- **Running ship's Step 1 through `sdlc.py gate`.** By Step 1, ship is about to write
  `findings.md`, which already moves the card. Ship would gain a write it can't pre-approve, so
  every ship would prompt.
- **A `Sdlc-*` trailer for hand gates.** The record is in the change's commit, which history keeps,
  and the trailer contract should only grow for a reader that needs it. None does.
- **Sharing code with `factory.py`.** Each plugin is cached separately, and neither imports the
  other, so the code is copied and pinned.
- **Pinning the shape with a formatter pulled out of `factory.py`.** It would touch the factory's
  gate. The end-to-end pin test compares the same thing without that.

## Verification

```bash
uv run --group dev pytest -q -n auto tests/test_sdlc.py tests/test_board.py tests/test_metrics.py tests/test_factory.py
uv run --group dev pytest -q -m portable
./check.sh
```

Healthy output:
- Every test passes, including the new R1 to R14 tests and the existing factory gate tests (whose
  output is unchanged).
- `./check.sh` ends green: ruff check, ruff format, pytest and `claude plugin validate --strict`.

By hand, from this change's worktree:
1. Run `uv run --quiet --script scripts/sdlc.py gate 091`. It prints JSON with
   `"verdict": "PASS"` and `"to": ".sdlc/work/091-hand-gate-record/build/gate.md"`. The file opens
   with `GATE: PASS` and holds no `/Users/` path.
2. Run `sdlc.py board`. 091's card is in Test with a `gate green` badge and `/sdlc:ship` next.
3. Touch a file under `scripts/` and refresh. The card is back in Build, without the badge.
4. `sdlc.py status` shows `· gate green` on 091's line before step 3 and nothing after it.
