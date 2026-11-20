---
id: 199
slug: landing-records-unforgeable
kind: spec
created: 2026-11-20
updated: 2026-11-20
---

# 199 — Landing records an agent in the change's folder can't forge · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code. The scripts write five gate-shaped records, and each one is trusted only by the `Build:` hash it states:

- `factory.py gate` writes `build/round-<N>.gate.md`, `build/land-<n>.gate.md` and `build/land-<n>.build.md` (`cmd_gate()`).
- `factory.py accept` writes `build/land-accept.md` (`cmd_accept()`).
- `sdlc.py gate` writes `build/gate.md` (`cmd_gate()`).

Their readers compare that stated hash with the build as it stands, and with nothing else:

- `_land_gate_state()`, `_accept_state()`, `_read_gates()` and `_read_builds()` in `landing.py`.
- `hand_gate_state()` in `factory.py`.
- `_gate_state()` in `run_state.py`.

So a builder or resolver that writes a well-formed green file into the folder passes. The git common directory is the one place shared by every worktree and outside all of them (`_slot_dir()`). The train's state and the gate slots already live there for that reason.

1. **R1. The script vouches for every record it writes.** Before writing any of the five records, its writer appends one line to `sdlc-factory-records.jsonl` in the git common dir. The line is `{"change": <folder name>, "record": <path from the folder, POSIX>, "sha256": <the content's hash>}`. The hash is taken over the text with `\r\n` read as `\n`. A test runs each of the three commands on a fixture and asserts that the ledger holds the hash of the file as it now stands. The test fails if any writer skips the line.
2. **R2. `vouched()` decides from the ledger alone.** A record is vouched when some ledger line names the same change, the same record path and the hash of the file as it stands. Every version the script ever wrote stays vouched, so a `train --eject`'s `reset --keep` back to an older record still reads. A missing or unreadable ledger vouches nothing, and so does a line that won't parse. A test asserts each of these:
   - changing one byte of a vouched record makes it unvouched, and restoring it makes it vouched again;
   - the same bytes copied into another change's folder are unvouched;
   - a record copied to a different record path is unvouched;
   - a CRLF copy of a vouched record stays vouched (marked `portable`).
3. **R3. `land` refuses a change that holds an unvouched record.** If the change's folder holds any of the five records unvouched, `land` refuses before it commits anything: `state: refused`. The refusal names each such file and says the script didn't write it. This is the intent's test: write a well-formed green `build/land-accept.md` by hand with the right `Build:`, run `land`, and see it refused with the change's branch unmoved. Do the same with a hand-written green `build/round-<N>.gate.md`.
4. **R4. A landing round never reads an unvouched record as a verdict.** In `land_verdict()`, an unvouched `build/land-<n>.gate.md` or `build/land-accept.md` is a problem that names the file, and the next step is `stop`. It is never `mend` and never `pass`, even with `settled`. A test hand-writes a green `land-1.gate.md` whose `Build:` is `HEAD` and asserts `next == "stop"`.
5. **R5. A train never copies an attempt from an unvouched record into its state.** `_read_gates()` and `_read_builds()` copy no attempt from an unvouched `land-<n>.gate.md` or `land-<n>.build.md` into `TRAIN_STATE`. Instead, the train's reading names `stop` with the file as its reason. A test stacks a two-change train, writes a green `land-1.gate.md` by hand on the tip's stacked commit, and runs `train --run`. It asserts the run stops without closing anything and `state["gates"]` holds no attempt for that change.
6. **R6. A hand-written hand gate clears nothing.** `factory.py`'s `hand_gate_state()` is `green` only when `build/gate.md` is vouched. So `gate_reasons()` leaves `/sdlc-factory:decide`'s gate reasons uncleared, and `escalation_lines()` says `gate: not cleared`. A test hand-writes a green `build/gate.md` whose `Build:` matches `hand_build()` on an escalated change at `stage: test` and asserts both.
7. **R7. No writer appends to an unvouched record.** `factory.py gate`, `factory.py accept` and `sdlc.py gate` each refuse when the record they would append to exists and is unvouched. The refusal names the file and says to remove it before running again. Nothing is run and nothing is written, so a forged earlier attempt never gets vouched by a genuine one written after it. For each writer, a test plants a forged attempt and asserts the refusal, that the file is unchanged, and that the check never ran (a marker command that would leave a file).
8. **R8. What the board, `status` and core read stays the same.** `scripts/factory_records.py`'s parsing, `sdlc.py`'s `hand_gate()`, `needs_of()`, `seen_stage()` and the board's columns are unchanged, and none of them reads the ledger. The existing pins in `tests/test_modules.py` and `tests/test_hand_gate.py` pass with no edit to what they assert. `sdlc.py`'s copy of the ledger writer and hash (`_vouch()`, `_record_digest()`) is pinned to `factory.py`'s by a new test in `tests/test_hand_gate.py`. That test fails if the two write different lines for the same record.
9. **R9. The ledger is safe across worktrees and platforms.** Each write is one line opened in append mode (`encoding="utf-8"`, `newline="\n"`), under an exclusive lock on `sdlc-factory-records.lock` in the git common dir. It uses `_try_lock()` and core's copy of it, with no platform module imported at the top. A test runs two writers at once and asserts both lines are whole. `tests/test_windows.py`'s scans pass.
10. **R10. The docs say it.** These docs are updated:
    - `AGENTS.md`, *The factory*: core writes one file the factory reads, the ledger (see *Contracts touched*).
    - `docs/REFERENCE.md`, the records listed at *`.sdlc/work/` and worktrees*.
    - `plugins/factory/README.md`.
    - `plugins/factory/skills/land/SKILL.md`, where it names `build/land-<n>.gate.md` and `build/land-accept.md`.

    Each says that the script vouches for each record in the ledger and that a landing refuses one it didn't write. Each also states the limit: this protects against a write inside the worktree, not against one into the git common dir (R2's design). A grep of the docs for `land-accept.md` and `gate.md` finds no claim that contradicts this.

## Design

**The ledger.** `sdlc-factory-records.jsonl` lives in the git common dir (`factory._slot_dir()`, `git rev-parse --git-common-dir`). It sits beside `sdlc-factory-train.json` and the gate slot locks, outside every worktree, and no `git status` shows it.

- **What a line holds:** a JSON object naming one record version the script wrote.
- **What it leaves out:** no verdict and no build. The record file stays the only place those are read, and it stays a file a person reads in the change's folder (intent constraint).
- **Pruning:** lines are never rewritten or pruned. A line is about 150 bytes, and one is written per gate or accept attempt.

**Writing (R1, R7, R9).** `factory.py` gets these, beside `read_gate_file()`:

- `RECORDS_LEDGER`;
- `_record_digest(text)`: sha256 of the text with `\r\n` → `\n`;
- `_vouch(root, folder, path, text)`;
- `vouched(root, folder, path)`;
- `forged_records(root, folder)`: the five record kinds present in the folder, by glob, that aren't vouched.

`cmd_gate()` and `cmd_accept()` already build the whole new text before writing it, and their order changes to this:

1. If the record exists, check it with `vouched()`, else refuse (R7).
2. Build the text.
3. `_vouch()` the text.
4. Write the file.

Vouching before writing means a crash between the two leaves a vouched hash that no file holds, which is harmless. The reverse order would leave a genuine record unvouched.

`sdlc.py`'s `cmd_gate()` does the same through its pinned copies (`_vouch()`, `_record_digest()`, the lock through `closing`'s lock helpers or a copy of `_try_lock()`). These are placed with the other hand-gate copies and pinned as `_hand_hash()` is.

**Reading (R2–R6).**

- **`vouched()`:** reads the ledger line by line, skips lines that don't parse, and returns True on a match of (change, record, hash).
- **`cmd_land()`:** in `land_check`, beside the `accept` and `cases` checks, it calls `forged_records()` and refuses on any result. This covers round gates too: a change that never moved in a train is landed on its build round's gate alone (`_train_gates()`'s `train of one that never moved`). A forged round gate would otherwise reach a commit through the reviewers.
- **`land_verdict()`:** calls `vouched()` on the land gate and accept records before `_land_gate_state()` and `_accept_state()` read them. If either is unvouched, it adds a problem that isn't in `every`, so the step is `stop`.
- **`_read_gates()` and `_read_builds()`:** collect unvouched paths instead of copying from them. The train's reading (`_train_gates()`, `_train_build()`) returns `{"next": "stop", "reason": "<file> isn't a record the script wrote"}` before it bisects. `train --run` already stops on `stop`.
- **`hand_gate_state()`:** ANDs `vouched()` into `green`.

`run_state.py`'s `_gate_state()`, and so `verdicts`, are not changed. `verdicts` "reads no state file but `runs/mended`", and the landing catches a forged round gate in R3 before any commit.

**Tests that write records by hand.** About 90 places in `tests/` write or read these records, and most write them directly to drive a state. They get one helper in `tests/conftest.py` that writes the record and calls `factory._vouch()`, so their assertions are unchanged. A test whose point is a hand-written record (R3–R7) skips the helper. The `evals/` fixtures write none of these files (checked).

**What this protects.** A record is now forgeable only by a write into the git common dir, not by a write into the change's folder. The builder's and the resolver's Edit/Write work in the worktree. A write into the common dir goes through the harness's permission mode, `[factory] mode`, `auto` by default. The train's state and the slot locks already rest on that same boundary. The docs say so (R10) rather than claiming more.

## Contracts touched

- **"`factory.py` never imports `sdlc.py`… each reads the other's files with copies of its parsing, pinned by tests."** The design stays inside this. Core and the factory share the ledger's format through pinned copies (R8), and neither imports the other.
- **AGENTS.md, *The factory*: "`sdlc` only reads the files a run leaves… the gate slots' lock files…".** This sentence would stop being true, and a person needs to decide on it. `sdlc.py gate` now also **writes** a factory-read file, the ledger line for `build/gate.md`. This is the first file core writes for the factory to read. The alternative is to leave the hand gate unprotected (see the questions after the spec). If the hand gate stays in scope, the map gets this sentence: "and appends the hand gate's line to the records ledger (`_vouch()`), a copy pinned to `factory.py`'s."
- **"Nothing about a record goes into `sdlc.lock` or a tree other than the git common dir"** (intent). The ledger and its lock are in the git common dir only.
- **"`verdicts` decides from the rounds alone and reads no state file but `runs/mended`."** Kept: `verdicts` is not changed.
- **The scripts run on Windows.** Kept by R9: `newline="\n"`, `encoding="utf-8"`, lock modules imported only inside functions, and a `portable` test for CRLF hashing.
- **Writes before a WAIT.** A ledger line is written only by `gate` and `accept`, which already write their record unasked. It is a record of a write already allowed, not a new write.
- **The board writes nothing and is in neither `READ_ONLY` nor `ALLOW_RULES`.** Unchanged: it doesn't read the ledger (R8).
- **REVIEW.md, "A doc's claim the change made false".** R10 lists the docs that name these records.

## Alternatives rejected

- **A keyed signature (HMAC) in each record.** The key has to live somewhere the script can read and the agent can't, and the only such place is the git common dir, the same place the ledger lives. So a signature protects no more than the ledger, while adding a secret to create and rotate. It would also add a line to every record, and the board, `status` and `factory_records.py` would have to learn to skip it. Their reading would change, against the intent's outcome.
- **Keeping only the latest hash per record.** A train's `--eject` (`reset --keep`) brings back the version committed before the train, and that version was genuine. Refusing it would stop every ejected change.
- **Moving the records out of the folder.** Against the intent's constraint: records stay files a person reads in the change's folder and stay committed with it.
- **Re-running the gate at landing instead of trusting any record.** The train runs the gate once at its tip by design (185). Re-running per change throws that away and still leaves `land-accept.md` and the hand gate open.
- **Having `verdicts` check round gates.** Breaks `verdicts`' "reads no state file" rule, and R3 already catches a forged round gate before any commit.
- **Letting a writer start a fresh file over an unvouched record.** That would silently drop whatever was there. A refusal (R7) is loud and costs one `rm`.
- **Pruning the ledger at close.** Close is core's and holds `_main_lock()`. Teaching it a factory file to save a few kilobytes isn't worth the extra coupling.

## Verification

```bash
uv run --group dev pytest -q -n auto tests/test_land.py tests/test_train.py tests/test_hand_gate.py tests/test_factory_gate.py tests/test_modules.py
uv run --group dev pytest -q -m portable
./check.sh
```

What a healthy run looks like:

- **All of `./check.sh` passes:** ruff, ruff format, every test, and `claude plugin validate --strict`.
- **New tests pass by name:** each R test, for example `test_land_refuses_a_hand_written_accept_record`, `test_train_run_stops_on_a_hand_written_gate`, `test_a_hand_written_hand_gate_clears_nothing`, `test_no_writer_appends_to_an_unvouched_record`, `test_the_ledger_writer_is_pinned_to_core`, and `test_a_crlf_record_stays_vouched` (portable).
- **Existing pins in `tests/test_modules.py` and `tests/test_hand_gate.py` pass** with no edit to what they assert.
- **By hand:**
  1. In a scratch host, run a factory change to `stage: test` and `factory.py accept` it.
  2. Run `cat "$(git rev-parse --git-common-dir)"/sdlc-factory-records.jsonl`. It shows one line naming `build/land-accept.md`.
  3. Add a space to that file. `factory.py land` should now refuse and name it.

