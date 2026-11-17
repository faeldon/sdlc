---
id: 085
slug: factory-stopped-runs
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 085 — A stopped factory run says so, and how to move it on · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

What this spec takes as given, each one checked in the code:

- A run stops only when `loop_state()` (`plugins/factory/scripts/factory.py:932-1014`) has any
  `problems`. Several of them can't be worked out again outside that call. A HEAD move needs the
  run's `--head`, which only the supervisor holds. The evidence, gate and verifier checks
  (`read_evidence()`, `_gate_state()`, `read_verified()`) are what 084 is rewriting now.
- A stopped run sits at `stage: build`, because the supervisor never runs `stage <NNN> test` on it.
  `ready()` (`factory.py:1694`) already skips any change that isn't at `test` or `shipped`, so
  `/sdlc-factory:land` never sees a stopped run.
- `factory.py agent` reads the loop through `loop_state(root, ident, None)` (`factory.py:1597`),
  with no head. Only the supervisor's Step 2 call (`skills/build/SKILL.md:219-221`) passes one.
- Close's `measure` reads only files under `runs/` whose names end in `.sessions`
  (`scripts/sdlc.py:3753`). Any other file there is never counted.
- The board marks a change as a factory run when its folder has a `runs/` folder (`board.py:125`).
  It renders a card's flags with `textContent` (`board.html:204`).

The requirements:

1. **R1. `factory.py verdicts <NNN> --head <head> --record` writes the stop record, or removes it.**
   When `next` is `stop`, it writes `.sdlc/work/NNN-slug/runs/stopped.md`. When `next` is anything
   else, it deletes that file if it exists. `tests/test_factory.py::test_record_writes_a_stop_and_removes_it_once_clear`
   fails if a stopped state leaves no file, or a clear state leaves one. That test builds a review
   with no verdict, records, puts the verdict line in and records again.
2. **R2. The record agrees with the call that wrote it.** Every problem in the file is word for word
   one of that call's `problems`, in the same order. The way the file names (R4) is the call's
   `way`. `test_the_record_is_verdicts_own_reading` fails if any problem is missing, reworded or
   reordered.
3. **R3. Without `--record`, `verdicts` writes nothing, and `--record` needs `--head`.** A call
   without the flag leaves the folder byte for byte as it was, an existing record included.
   `--record` without `--head` is refused with exit 1. Otherwise a call that can't see a HEAD move
   could remove a HEAD-moved stop. `test_verdicts_alone_writes_nothing` and
   `test_record_without_a_head_is_refused` cover this.
4. **R4. Every stop names its way on, and `factory.py` decides which.** `loop_state()` adds `way` to
   a stop's output. The record writes it, along with the sentence that goes with it:
   - `ship` when HEAD moved: an agent committed, so ship it by hand with `/sdlc:ship NNN` after
     reading the commit.
   - `mend` when every problem comes from `read_evidence()`: rerun `/sdlc-factory:build NNN`, whose
     one mend asks again for the missing `## Evidence`. If that reply still lacks it, ship by hand
     with `/sdlc:ship NNN`.
   - `rerun` otherwise: fix the cause, then rerun `/sdlc-factory:build NNN`, or ship by hand with
     `/sdlc:ship NNN`.

   `test_a_stop_names_its_way` checks each kind against the existing stop fixtures: no verdict,
   HEAD moved, missing evidence, a third red gate.
5. **R5. The loop never reads the record.** `loop_state()`, and so `agent` and depth, never open
   `runs/stopped.md`. If a record is left over from a run that is now clear, `next` is not `stop`,
   and the next `--record` removes it. `test_a_stale_record_never_stops_the_loop` covers this.
6. **R6. The board puts a stopped run under Needs you.** For a factory change at `stage: build`
   with a readable record:
   - `column` is `needs-you`.
   - The card's `stopped` holds `way` and `problems`, and each problem is a flag on the card.
   - `next` is the record's sentence.

   `tests/test_board.py::test_a_stopped_run_needs_the_person` builds this from 078's round-1 files,
   shown in the test's docstring as they are (a neutral folder name, `code.md`, `verified.md`,
   `build/round-1.md`). Its record is made with `factory.py`'s own `stop_text()`, from the two
   problems `verdicts` reported on 2026-11-17. The test fails if the card is in any other column or
   the next step reads "the factory is building it".
7. **R7. A record that won't read is still a stop the person sees.** If `runs/stopped.md` doesn't
   open with a `STOPPED:` line, it is a board `problems` line, and the card is under Needs you.
   `test_an_unreadable_stop_record_is_a_problem` covers this.
8. **R8. The record counts only at `stage: build`.** At `design`, `test`, `shipped` or `dropped`,
   the board and status ignore it. A stopped run that was shipped by hand keeps its record in
   history, and its card goes to Ready to close as today. `test_a_stop_record_counts_only_at_build`
   covers this.
9. **R9. Every other run reads exactly as today.** At `build` with no record, the card says "the
   factory is building it: wait for its decision". A blocking decision still says "answer its
   decision in the factory's supervisor". READY at `test` is still under Ready. The existing
   `test_board.py` cases pass unchanged, and `test_a_resumed_run_goes_back_to_build` checks that
   removing the record moves the card back to the Build column with that same next step.
10. **R10. `/sdlc:status` marks a stopped run on its line.** The line reads `· stopped, touched <ago>`
    in place of `quiet` or a bare touched time. Under the title come one `⚠ ` line per problem
    (each problem cut to fit one line) and a `→ <the record's sentence>` line.
    `tests/test_next_up.py::test_a_stopped_factory_run_is_marked_on_its_status_line` fails if
    `quiet` appears on that line or the reason is missing. `check --strict` reports nothing new: a
    stop is not a broken pipeline.
11. **R11. The readers' parsing is pinned to `factory.py`'s.** `board.py` and `sdlc.py` hold copies
    of `STOPPED_RE`, `NEXT_RE`, `PROBLEM_RE` and the path `STOPPED`. In `sdlc.py` they are named
    `FACTORY_STOPPED_RE` and so on, beside `FACTORY_KEPT_RE`. The existing pin tests fail if a
    pattern differs: `test_board.py::test_the_factory_parsing_is_a_pinned_copy` and
    `test_metrics.py`'s pin at line 1148, both extended.
12. **R12. Nothing in the core runs the factory, and the board still writes nothing.** No new
    `subprocess` call names `factory.py` in `board.py` or `sdlc.py`, and the board's existing
    no-write and route tests pass.
13. **R13. `ready` still leaves a stopped run out.** `test_ready_leaves_a_stopped_run_out` fails if
    a change at `stage: build` with a record appears in `factory.py ready`.
14. **R14. The supervisor records every reading and never edits the record.**
    `plugins/factory/skills/build/SKILL.md` makes these changes:
    - Step 2's command becomes `factory.py verdicts <NNN> --head <head> --record`. The existing
      `verdicts *` rule already covers it.
    - The `stop` step says the record now carries the problems and the way on, and that the
      supervisor never writes, edits or deletes `runs/stopped.md`.
    - Step 1 adds the file to the run's list of files.

    `test_factory.py::test_the_supervisor_records_each_reading` fails if the skill's `verdicts`
    command lacks `--record`.
15. **R15. The docs say it.**
    - `plugins/factory/README.md`: the file in the folder listing.
    - `docs/REFERENCE.md`: the board's Needs you, and the status line.
    - `skills/status/SKILL.md`: a stopped line is never in flight and never just quiet. It is
      recommended at rule 3 with its own `→` step.
    - `AGENTS.md`: the two sentence changes under *Contracts touched*.
    - `factory.py`: the module docstring ("writes only where its name says") and `cmd_verdicts`'s
      docstring.
16. **R16. `./check.sh` passes.** Every new test that touches no shell fake is marked `portable`,
    and the record is written with `encoding="utf-8", newline="\n"`.

## Design

**The record: `runs/stopped.md`.** `factory.py` gets one renderer, `stop_text(change, way,
problems)`, and the record looks like this:

```
STOPPED: rerun
NEXT: fix its cause, then /sdlc-factory:build 078, or ship it by hand with /sdlc:ship 078

- PROBLEM: reviews/round-1/verified.md answers code: … 0 times, not once
- PROBLEM: reviews/round-1/verified.md answers code: …, which no review of round 1 asks for
```

- The first line follows the pattern of `VERDICT:` and `DECISION:`:
  `STOPPED_RE = ^STOPPED: (mend|rerun|ship)\s*$`.
- `NEXT_RE = ^NEXT: (.+?)\s*$` and `PROBLEM_RE = ^- PROBLEM: (.+?)\s*$`. Any newline inside a
  problem is written as a space, so one problem is always one line.
- The constant is `STOPPED = Path("runs") / "stopped.md"`, beside `COSTS`.
- It lives under `runs/`, with the run's own files. `measure` reads only `*.sessions` there. The
  board's `/file` serves it like any file in the folder.

**Who writes it.** Only `cmd_verdicts`, and only with `--record` and `--head`. It calls
`loop_state()` once and prints exactly as today, with `way` added on a stop. It writes or deletes
the record from that same `out`, so the record and the printed reading can't differ (R2). The
supervisor already runs `verdicts --head` after every step, so it now records after every step.

- A run that stops gets its record on the call that found the stop.
- A run the person resumes (`/sdlc-factory:build NNN`, where `start` gives a fresh `head`) has the
  record removed by its first reading that finds no problem. That reading only happens because the
  cause is gone (R1, R5).
- If anything deletes the file by hand while the cause remains, the next recording call writes it
  again.

**Why `way` is `factory.py`'s call.** It knows which problems came from where: the `moved` flag,
and the list `read_evidence()` returned. `loop_state()` keeps those two apart as it builds
`problems`, and sets `out["way"]` only on a stop. The sentence is written into the record, so the
board and status print it and never have their own wording. The mend sentence names its own
fallback, because nothing records whether the mend was already used: today only the supervisor's
context knows. Recording mends would be scope this intent didn't ask for.

**The board.**

- `_factory()` reads the record with the pinned copies into `stopped: {"way", "next", "problems"}`,
  or None. A first line that doesn't parse becomes a `problems` line (R7).
- `next_action()` returns `stopped["next"]` for a factory change at `build` with a record. This
  check runs after the `CLOSED` check and before `pending`, the order `verdicts` itself uses: stop
  before decide.
- `column()` returns `needs-you` under the same condition.
- `board.html` pushes one flag per problem, with `textContent` as the other flags do. The Needs you
  column's `who` becomes "a decision, a problem or a stopped run".
- Nothing else in the entry changes, so R9 holds.

**Status.**

- `sdlc.py` gets `factory_stop(folder)`, a reader of `runs/stopped.md` using the `FACTORY_*` copies,
  never raising: an unreadable record becomes a one-item stop whose problem says so.
- `main()`'s status branch sets `rec["stopped"]` for an open change at `stage: build`, beside
  `behind` and `quiet`. It does this there and not in `analyze()`, so `check` never sees it.
- `print_status()` replaces the `quiet` or touched marker with `· stopped, touched <ago>` and prints
  the `⚠` and `→` lines under the title.
- The status skill treats such a line as waiting on the person and recommends its `→` step under
  rule 3.

**Edge cases.**

- A stop with a pending decision as well: `verdicts` says `stop`, so the record wins on both
  readers, as in the loop.
- A Tier 2 at `design`: the supervisor moves it to `build` before any agent runs, so no stop can
  happen at `design`. The readers ignore a record there anyway (R8).
- A HEAD-moved stop cleared by a rerun with a fresh `head`: that is how `start` and `verdicts`
  already behave when a run resumes, and the person chose it by rerunning. This change doesn't
  touch it.
- The order with 084: both edit `factory.py`, and 084 changes the problem texts of `read_verified()`
  and whether 078 stops at all. The record copies whatever `verdicts` says, so the two changes only
  conflict as text. The board test's problems are fixed strings, so 084's change doesn't alter what
  it checks.

## Contracts touched

1. **AGENTS.md, *The factory*: "`verdicts` writes nothing, so a run that reviewed at the full depth
   stays full by what its rounds hold, never by a state file."** **This design needs the sentence
   changed: it is a policy edit, for the person.** The point of the sentence (depth and the next
   step come from the rounds, never from a state file) still holds: R5 means the loop never reads
   `runs/stopped.md`. But "writes nothing" stops being true when `--record` is passed. Proposed
   wording: "`verdicts` decides from the rounds alone and never reads a state file. With
   `--record`, which only the supervisor passes, it writes the stop it found to `runs/stopped.md`
   for the board and status, or removes it, and nothing reads that back into the loop."
2. **AGENTS.md, *The factory*: "`sdlc` only reads, at ship, the files a run leaves in the change's
   folder."** **This also needs the sentence changed.** Status now reads `runs/stopped.md`, read
   only, with pinned copies, and the board already reads a run's files. Proposed: "`sdlc` only
   reads the files a run leaves in the change's folder: ship reads its rounds, and the board and
   status read its stop record."
3. **AGENTS.md, *The board*: it writes nothing, it reads a factory run's files with copies of
   `factory.py`'s parsing pinned by `tests/test_board.py`, and the core never imports or runs the
   factory.** The design stays inside this: one more file is read with three more pinned patterns
   (R11), and nothing runs the factory (R12).
4. **The factory never imports `sdlc.py`.** Unchanged: the record is `factory.py`'s own, and
   `sdlc.py` holds the copies.
5. **The factory's agents: the agents that judge have no Write, and no agent commits.** Unchanged:
   the script writes the record, and the skill forbids the supervisor to edit it (R14).
6. **`factory.py`'s docstring: "Every command prints JSON and writes only where its name says".**
   Kept true: the flag is named `--record`, and the docstring lists it (R15).
7. **The metrics trailer contract.** Not touched. `measure` reads only `*.sessions`, and a stop
   isn't measured (see Alternatives).
8. **Skills: narrow `allowed-tools`, plain bash.** The build skill's command keeps its existing
   `verdicts *` rule, and the status skill gains no command.
9. **The scripts run on Windows.** The record is written with `encoding="utf-8", newline="\n"`,
   paths are shown with `as_posix()`, and the new tests are marked `portable` (R16).
10. **Nothing local.** Test folders use neutral names. 078's file text is this repo's own, cited by
    its change number in a docstring, as `test_board.py` already cites 075 and 080.

## Alternatives rejected

- **Copies of `verdicts`' stop checks in `board.py` and `sdlc.py`, with nothing recorded.**
  - A HEAD move can't be seen without the run's `head`, which only the supervisor holds.
  - The copies would have to include `read_evidence()`, `read_verified()` (which 084 is rewriting),
    the gate count and the depth rule.
  - Three copies of the most-changed logic in the factory would disagree after any change to it,
    which is exactly the "two accounts" failure the intent rules out.
- **`verdicts` always records, with no flag.** Every reading would become a write. A call without
  `--head` (by hand, or `agent`'s own `loop_state`) can't see a HEAD move and would remove that
  stop.
- **A separate `factory.py stop` command run in the supervisor's `stop` step.** The writing and the
  clearing would be two commands, and the second would need a hook on resume. A record written
  from the same call that decided can't disagree with it.
- **The stop as an entry in the board's `problems`.** That list means "a file that won't read". A
  stop isn't one, and its next step needs the way, which `problems` can't carry.
- **Status running `factory.py verdicts`.** The core never runs the factory, and a host without
  `sdlc-factory` installed has no script to run.
- **The record in a git ref or under `.sdlc/` state.** The board and status read change folders,
  and `/file` couldn't show a ref. A run's files live in its folder.
- **Measuring stops as a `Sdlc-*` trailer.** The intent didn't ask for it, and the trailer format is
  a contract to extend on purpose: a seed of its own.
- **Recording a failed agent session (`agent`'s `problem`) as a stop.** `verdicts` wouldn't say
  `stop` for it, so the record would disagree with the next reading. Such a run is stalled, not
  stopped: left for the person (see the open questions).

## Verification

```bash
./check.sh
uv run --group dev pytest -q tests/test_factory.py -k "record or stop or way or ready or supervisor"
uv run --group dev pytest -q tests/test_board.py tests/test_metrics.py -k "stop or pinned or resumed"
uv run --group dev pytest -q tests/test_next_up.py -k "stopped or touched"
uv run --group dev pytest -q -m portable
```

Healthy output:

- `./check.sh` ends green: ruff clean, nothing to reformat, every test passed, and
  `claude plugin validate --strict` passes.
- Each `-k` run selects at least the tests R1 to R14 name, and they all pass.
- The portable run passes, as CI's Windows job will.

By hand, in a scratch repo built like `test_board.py`'s fixture with one stopped change:

- `sdlc.py status` prints that change's line as
  `… · stopped, touched 0m ago`, then a `⚠ reviews/round-1/…` line and a
  `→ fix its cause, then /sdlc-factory:build NNN, or ship it by hand with /sdlc:ship NNN` line.
- `sdlc.py board` shows the card under **Needs you**, with each problem as a flag and that step as
  its next one.
- Deleting the record (standing in for the clear reading of a resumed run) and reloading the page
  moves the card back to Build, reading "the factory is building it: wait for its decision".
