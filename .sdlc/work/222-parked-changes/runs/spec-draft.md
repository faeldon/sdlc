---
id: 222
slug: parked-changes
kind: spec
created: 2026-11-21
updated: 2026-11-21
---

# 222 — A change can be parked on a host resource, with a deadline, instead of stopping or asking · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code unless marked: the build loop runs a host's command in one step only, `gate`, which goes through `_run_check()` (`factory.py`). The builder's `check` and the landing's `gate --land` (and `--build`) run the same function but outside the build loop's steps. `verdicts` is `run_state.loop_state()`, and today it reads no state file but `runs/mended`. A gate slot is an `flock` held by the gate's own process for as long as it runs (`gate_slot()`), and today it waits for a slot with no bound. A host's factory settings are read from the base branch's `.sdlc/factory.toml` (`_base_factory()`), so a change can't loosen its own. The core reads a run's files only through `scripts/factory_records.py`.

1. **R1. Busy is opt-in.** A host's command counts as busy only when the base branch's `.sdlc/factory.toml` sets `[park] exit = <n>` and the command exits with exactly `n`. Without the key, or with any other code, `gate`, `check` and `gate --land` behave exactly as they do now. Test `test_a_busy_code_without_park_exit_is_a_red_gate` fails if a gate exiting 75 with no `[park]` writes anything but a `Verdict: FAIL` attempt.
2. **R2. A busy gate parks, and records no attempt.** `factory.py gate <NNN>` on a busy exit leaves `build/round-<N>.gate.md` untouched, writes `runs/parked.md`, and prints `"verdict": "BUSY"` with the park's fields (exit 1). A test fails if the gate file gains an attempt, or if `runs/parked.md` lacks any of `PARKED: gate`, `ROUND:`, `RESOURCE:`, `HOLDER:`, `SINCE:`, `RETRY:`, `DEADLINE:` and `ATTEMPTS:`.
3. **R3. What the host returns.** A busy command may print three lines in its output: `SDLC-BUSY-RESOURCE: <text>`, `SDLC-BUSY-HOLDER: <text>` and `SDLC-BUSY-UNTIL: <YYYY-MM-DDTHH:MM:SSZ | whole minutes>`. All three are optional, and where a line appears twice the last one counts. Each value is made to one line, cut to 200 characters, and passed through `_placeholders()` and `_defused()`. A missing resource or holder is written as `unknown`. An `UNTIL` that won't parse is ignored, and the record notes it in a `- NOTE:` line. `test_busy_payload_is_read_defused_and_cut` fails if a home path, a term or a 300-character holder reaches the record as given.
4. **R4. One deadline per park, which the host never extends.** The first busy attempt for a given (step, round) sets `SINCE` to now and `DEADLINE` to `SINCE + [park] deadline` minutes (default 60, accepted from 1 to 1440, otherwise 60 with a warning). A later busy attempt for the same (step, round) keeps both, adds 1 to `ATTEMPTS` and sets a new `RETRY`. `RETRY` is the host's `UNTIL`, or else now plus `[park] retry` minutes (default 5). It is never less than one minute from now and never past `DEADLINE`. `test_a_repark_keeps_its_deadline` fails if a second busy attempt moves `DEADLINE`, or if an `UNTIL` past it moves `RETRY` past it.
5. **R5. A run that isn't busy ends the park.** A gate attempt that isn't busy (PASS, FAIL, timeout or didn't run) removes `runs/parked.md` after writing its attempt. A test fails if the record survives a green or red attempt.
6. **R6. `verdicts` reads the park.** While `next` would otherwise be `gate` for the record's round:
   - before `RETRY`, `next` is `parked`, with `round` and a `parked` object (resource, holder, since, retry, deadline, attempts);
   - from `RETRY` until `DEADLINE`, `next` is `gate`;
   - at or past `DEADLINE`, the park is a problem, so `next` is `stop` with `way` `parked`.

   `test_verdicts_parks_then_retries_then_stops` fails on any of the three readings at fixed clock values.
7. **R7. `verdicts` decides from the files and an injected clock.** `loop_state()` and `cmd_verdicts()` take `now` (default: the real clock), and the same files with the same `now` always give the same reading. A test fails if a reading depends on anything but those.
8. **R8. A park record is trusted only as far as it can be.** `runs/parked.md` is vouched in the records ledger before it is written (`_vouch()`), as a gate record is. `verdicts` reads an unvouched record, or one that won't parse, as a problem (`stop`, `way` `rerun`), never as a wait. It also caps the deadline at `SINCE + [park] deadline` from the base branch, whatever the file says. A record for any other round, or one left after its round's gate has a current verdict, is stale: `verdicts` passes over it and `--record` removes it. `test_a_forged_park_never_waits` fails if a hand-written record with a far deadline yields `parked`.
9. **R9. What `--record` writes.**
   - `runs/step.md` records `STEP: parked`.
   - At the deadline, `runs/stopped.md` records `STOPPED: parked`. Its `NEXT:` line names the resource and holder (`free <resource> (held by <holder>), then /sdlc-factory:build {id}`), and `WAYS_WHY` has the longer sentence.
   - `STOPPED_RE` gains `parked` in both `factory.py` and `factory_records.py`, the two kept identical by `test_every_shared_name_is_the_factorys`.
   - `sdlc.py`'s `FACTORY_STOP_NEEDS` gains `parked`.

   A test fails if a stop at the deadline reads back through `factory_records.read_stop()` with `way` None.
10. **R10. `factory.py park`.**
    - `park <NNN> --wait` blocks until the park's `RETRY`, its `DEADLINE`, or until the record is gone, whichever comes first. It checks the record every few seconds, writes nothing, and prints the reading `verdicts` would give then.
    - `park <NNN> --clear` removes `runs/parked.md` only when its deadline has passed, and refuses otherwise.

    Test: `--wait` returns within its bound on a stand-in clock, and `--clear` refuses a live park and removes an expired one.
11. **R11. The build skill.**
    - On `parked`, the supervisor runs `park <NNN> --wait` with `run_in_background`, then returns to Step 2.
    - A `stop` whose `way` is `parked` is reported and left.
    - `start --for build` reports `parked` (the record, and whether it is expired) and writes nothing. On a rerun's yes with an expired park, the skill runs `park <NNN> --clear` before its first `verdicts`.
    - Both commands get `Bash(...)` rules in `allowed-tools`, written as run.

    `tests/test_skills.py` fails on a missing or unused rule.
12. **R12. A gate slot wait is bounded.** `gate` waits at most `SLOT_WAIT` (2 × `GATE_TIMEOUT`) for a slot. Past that it records no attempt and parks the change on the resource `gate slot`, holder `another gate`, with R4's deadline, whether or not `[park] exit` is set. `check` exits 1 past `SLOT_WAIT`, saying so on stderr. `test_a_gate_slot_wait_ends` fails if `gate_slot()` waits past `SLOT_WAIT` on a stand-in clock.
13. **R13. A busy landing gate never ejects.** `gate --land` (and `--land --build`) on a busy exit, or past `SLOT_WAIT`, writes no attempt and no `runs/parked.md`, and emits a `problem` naming the resource, the holder and `UNTIL`. `train --run` then stops on that problem through its existing rule (`landing._run_loop()`'s `out.get("problem")`) and never ejects or bisects. `landing.py` is not edited. A test fails if a busy tip gate yields an `eject`.
14. **R14. `check` passes busy through.** `factory.py check` returns the host's busy exit code unchanged, prints one `busy: <resource> held by <holder> until <until>` line on stderr, and writes nothing. A test fails if `check` writes `runs/parked.md`.
15. **R15. Autopilot.**
    - A `parked` reading runs no command, and the change's state records `retry` and `deadline`.
    - `starts()` passes over a change until its `retry`.
    - `run_loop()` never ends while a change is parked before its deadline and no budget is spent. It waits in slices of at most 30 s, rereading the cancel file each time.
    - Past the deadline, the next reading's `stop` holds the change with the stop's problem, which names the holder.
    - A parked change still counts in `in_flight`.

    `test_autopilot_waits_out_a_park_and_holds_past_its_deadline` fails if the loop ends early, busy-loops (more than one `verdicts` before `retry`), or lands a change past its deadline.
16. **R16. Status and the board show it.**
    - `factory_records.read_park()`, a copy of `factory.py`'s parsing pinned by a test, reads the record for `status` and the board.
    - `status` prints a parked change under Building with a `⏸ parked on <resource>, held by <holder>; retry <time>, deadline <time>` line.
    - The board's card places `parked` at the gate's position (`AT`) with that text, built with `textContent`.
    - A park past its deadline with no `runs/stopped.md` (a supervisor that died) is a need in `needs_of()` (`parked past its deadline: free <resource>`), which moves the card to Needs you.

    Tests in `tests/test_board.py` and `tests/test_sdlc.py` fail on either column.
17. **R17. The transition table.**
    - `factory.py` gains `STEPS`, every `next` `verdicts` can name.
    - The factory README gains a table with one row per step: its stage, what moves it on, and its bound (an agent step `AGENT_TIMEOUT`; `gate` `GATE_TIMEOUT` plus `SLOT_WAIT`; `parked` its deadline; `decide`, `upgrade`, `spec` and `stop` the person; `done` terminal).

    `test_every_step_has_a_row_and_a_bound` fails if `run_state.py` assigns `out["next"]` a value not in `STEPS` (read from its AST), if a step has no row, or if a row's bound is empty.
18. **R18. The docs follow.**
    - The factory README's *Configuration* gains `[park]` (`exit`, `deadline`, `retry`), suggesting 75 (`EX_TEMPFAIL`) as the code.
    - `docs/REFERENCE.md` gains the host's side: the code, the three lines, and that the plugin keeps no resource model.
    - `docs/FEATURES.md` gains `park`, which `tests/test_feature_map.py` checks.
    - `AGENTS.md`'s factory paragraph changes as *Contracts touched* says.

## Design

**The signal.** `_run_check()` stays the one place a host's command runs. A new pure helper, `busy_of(code, output, cfg)`, returns `None`, or `{resource, holder, until, note}` when `cfg["park"]["exit"]` is set and equals `code`. `cmd_gate`, `cmd_check` and the `--land` paths call it right after the run. Only the build loop's `gate` writes a park. `load_config()` reads `[park]` from `_base_factory()`, as it reads `gate_jobs`, with a warning when the checkout's copy differs. Under `check`, the output goes straight through and isn't captured, so the payload is read only from what a capturing caller sees. `check` therefore reports the code, and the payload only when the host also printed it to stderr. If that proves too thin, capturing with tee is the plan's call.

**The record.** `runs/parked.md` is `factory.py`'s, shaped like `runs/stopped.md` (key lines, then `- NOTE:` lines), written by a new `park_text()` and read by `read_park()`. The constants (`PARKED`, `PARKED_RE` and its field regexes) live in `factory.py`, and core's copies live in `factory_records.py` under the same names. `cmd_gate` writes it, after `_vouch()`, only for a build-round gate. A gate attempt that isn't busy removes it. `--record` removes a stale one. `park --clear` removes an expired one. Nothing else writes it.

**The reading.** `loop_state(root, ident, head, now=None)` reads the park once, next to `_gate_state()`.
- An unvouched or garbled record goes into `problems` (way `rerun`).
- A record past its deadline goes into `problems`, and `way` becomes `parked` when every problem is a park's, the way `mend` is decided.
- Otherwise, in the branch that would name `gate` (`unreviewed and gate["current"] is None`), `now < RETRY` gives `next = "parked"` and `out["parked"]`. Anything else falls through to `gate`.

Because a park sits only in front of `gate`, it never competes with `decide`, `fix` or `review`. A restart or upgrade round makes the record stale by round number.

"Once the host says free" is read here as "once a retry isn't busy". The plugin can learn that the resource is free only by asking again, at `RETRY`.

**Waiting.**
- **Supervisor:** `park --wait` in the background keeps the supervisor free, as an agent does. It is bounded by the deadline, which is capped at 24 h.
- **Autopilot:** `build_step()` returns `{"parked": {...}}` without running a command. `apply_change()` stores `retry` and `deadline` on the change. `starts()` passes over the change while `now < retry`. `run_loop()`, when nothing is running but something is parked, waits until the earliest `retry`, in slices of at most 30 s, rereading the cancel file and the budgets each slice. `AUTOPILOT_STEPS`' comment adds `parked` to the loop's own readings.
- **Gate slot:** `gate_slot()` takes a deadline. On `SLOT_WAIT` it yields `(None, waited)` with a `timed_out` flag, and `cmd_gate` parks on `gate slot`. A parked change holds no slot, because it has no live process (see *Open questions*, resolved).

**Showing it.** `factory_records.read_park()` feeds `status` (`print_status()`'s line) and the board (`_track()`: `AT["parked"] = 1`, labelled `parked: <resource>`, with state `paused` in `STEP_WORDS` worded `waiting on <holder>:`). `needs_of()` gains its rule from `rec["parked"]` and `rec["now"]`, keeping `needs_of()` free of any clock read of its own: the caller passes `now`.

**The table.** `STEPS = ("build", "gate", "fix", "review", "arbitrate", "rework", "approve", "decide", "upgrade", "spec", "parked", "done", "stop")`, documented in the factory README under *The loop's states* and held by the AST test (R17).

### Boundaries

- **Always:** a busy wait ends by its deadline; the deadline comes from the base branch alone; a busy answer is never written as a red gate.
- **Asks first:** clearing an expired park happens only on the yes of a rerun of `/sdlc-factory:build`.
- **Never:** a resource model, a lock or a queue of the host's; parking a landing (a busy landing gate stops the train); parking an agent session mid-run; extending a deadline from the host's answer; any change for a host without `[park] exit`, except that a gate slot wait now ends.

## Contracts touched

- **`AGENTS.md`: "`verdicts` decides from the rounds alone and reads no state file but `runs/mended`."** **This change needs that sentence changed.** `verdicts` would also read `runs/parked.md` and the clock. The design keeps the rule's intent: the record is vouched, its deadline is capped from the base branch, the clock is injected and deterministic in tests, and nothing an agent writes can make a run wait. The new sentence: "reads no state file but `runs/mended` and the vouched `runs/parked.md`, and the clock only for a park". `run_state.py`'s docstring changes to match. This is a policy edit for the person's yes.
- **`AGENTS.md`: "`factory.py gate` and `check`, through one function (`_run_check()`), the only places it runs a host's command."** Kept. `busy_of()` reads the result and runs nothing.
- **A record read as a verdict only while the ledger vouches for it (`vouched()`).** Extended to `runs/parked.md`, written through `_vouch()` before `write_text`. A busy attempt is never written as a gate record, so no verdict changes meaning.
- **Settings from the base branch** (`_base_factory()`, `gate_jobs`, `[autopilot]`). `[park]` is read the same way, so a change can't set a long deadline for itself.
- **Writes before a WAIT (the six).** None added. `gate` writing the park is part of the approved run's own step, as its attempt is. `park --clear` runs only after the rerun's yes. `park --wait` writes nothing.
- **Gate slots are locks in the git common dir, never `sdlc.lock`.** Unchanged. The bound is added to the waiting loop only.
- **Core reads a run's files only through `factory_records.py`, with copies pinned (`tests/test_modules.py`).** `read_park()` and its constants go there under `factory.py`'s names. No other core file names the record.
- **The board writes nothing and builds nodes with `textContent`.** Kept: the park line is text.
- **The stop ways (`STOPPED_RE`, `WAYS`, `FACTORY_STOP_NEEDS`).** Extended by `parked` in each copy. Readers of the old three see a new value, which `read_stop()` already returns as is.
- **Autopilot** (`AUTOPILOT_STEPS` is the only set of commands it runs; `hold_causes()`; `--by autopilot`). No command is added to `AUTOPILOT_STEPS`, because a park runs none. A deadline stop holds the change as every stop does. `autopilot.py` is in `[review] sensitive`.
- **The landing (`landing.py`, `RUN_EJECTS`).** Not edited. A busy landing gate reaches the train only as a `problem`, which already stops it rather than ejecting.
- **Skills' `allowed-tools`, one rule per command run.** Two `park` rules in `build/SKILL.md`. No `if` goes into a bash block: whether a park is expired is `start`'s field.
- **Windows** (`encoding="utf-8"`, `newline="\n"`, no `fcntl` at the top). The new writes follow these rules, and `park --wait` sleeps with `time.sleep` only.
- **The core hand gate (`sdlc.py gate`).** Unchanged. A busy exit there is the person's red, as it is today. It isn't a factory step.
- **REVIEW.md's "a doc's claim the change made false."** R18 names each doc and the sentence that changes.

## Alternatives rejected

- **A resource model in the plugin** (named resources, a lock table, conflict rules). The intent rules it out. The host already knows its resources, and a copy in the plugin would drift.
- **Sleeping inside `gate` until free.** That would hold a gate slot and an autopilot worker for the whole wait and look like a hung gate. Ending the process and rereading at `RETRY` frees both.
- **Taking the host's `UNTIL` as the deadline.** A host that keeps saying "ten more minutes" would wait forever. `UNTIL` sets only the next retry.
- **A park as a `[default]` or `[blocking]` decision.** Asking is what the intent wants to avoid, and a decision has no clock.
- **Writing a busy attempt as `Verdict: FAIL` with a marker.** Every reader of gate records (`fails`, `GATE_FIXES`, the train's bisect) would have to learn the marker, and one that didn't would eject or stop a change for a red it never had.
- **A host-written "free" file the factory polls.** That gives the plugin a second interface into the host, and it is a resource model by another name.
- **Parking the train on a busy landing gate.** The train's state machine, its run lock and its ejection rules would all need a waiting state. Stopping the train with the holder named is safe now. Landing parks can be a change of their own if the person wants them (see *Open questions*).
- **Parking a builder mid-session on `check`.** The builder's session would have to be suspended and resumed. Passing the code through lets the builder report it as it reports any red check.
- **A default busy code (75) that is on without config.** A host whose check already exits 75 for some other reason would start parking, which breaks the constraint that a host that never returns the busy code sees no change.

## Verification

```bash
./check.sh
uv run --group dev pytest -q -n auto tests/test_factory_gate.py tests/test_factory_loop.py tests/test_autopilot.py tests/test_board.py tests/test_modules.py tests/test_feature_map.py tests/test_skills.py
uv run --group dev pytest -q -m portable
```

Healthy output:
- Every new test passes: R1–R17's named tests, the pinned copies of `PARKED_RE`, `STOPPED_RE` and `read_park()`, and the AST check on `STEPS`.
- `./check.sh` passes ruff, the format check, the full suite and `claude plugin validate --strict`.
- The portable run passes, covering the new writes' `newline` and the platform imports.
- `sdlc.py drift` reports nothing, since no `defaults/` or `guide/` file changes.

By hand, in a scratch host:
1. Set `[park] exit = 75`, `deadline = 2`, `retry = 1` on the base branch.
2. Make `[commands] check` print the three `SDLC-BUSY-*` lines and exit 75.
3. Run `/sdlc-factory:build`. The card shows `parked: <resource>` at the gate, `status` shows the `⏸` line, and after about two minutes the card moves to Needs you with `free <resource> (held by <holder>)`.
4. Change the check to exit 0 and rerun. `park --clear` runs after the yes, and the gate goes green.

