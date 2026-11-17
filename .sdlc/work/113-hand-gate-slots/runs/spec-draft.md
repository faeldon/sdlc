---
id: 113
slug: hand-gate-slots
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 113 — The hand gate shares the factory's gate slots · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code before designing:

- The factory's slots are `gate_jobs` OS locks on `sdlc-factory-gate-<k>.lock` (`SLOT_NAME`) in the git common dir (`_slot_dir()`, `factory.py`). They are taken by `_try_lock()` (`fcntl.flock` or `msvcrt.locking`, imported inside the function). Each gate tries slot 0 first and polls every `SLOT_POLL` (0.25 s). It waits with no limit, and says so once on stderr (`gate_slot()`).
- `gate_jobs` is read only from the base branch's `.sdlc/factory.toml` (`_gate_jobs()` over `_base_factory()`). The default is 1, and anything but a whole number ≥ 1 falls back to 1 with a warning.
- `sdlc.py`'s `cmd_gate()` takes no lock today. It reads `[commands] check` from the base branch (`_config_at(home, "refs/heads/<trunk>")`) and runs it in the change's checkout under `GATE_TIMEOUT` (30 minutes, pinned equal to the factory's).
- `sdlc.py` already knows whether `sdlc-factory` is enabled, from Claude Code's settings files alone (`factory_enabled()`).

The requirements:

1. **R1. A hand gate waits for a factory gate's slot.** Say the factory is enabled, the base branch's `gate_jobs` is 1, and a process holds slot 0 through `factory.gate_slot()`. Then `sdlc.py gate NNN` waits, and prints `NNN-slug: waiting for a gate slot (1 of 1 in use), up to 30 minutes` once on stderr. It runs its check only once the slot frees, so the two commands' times never overlap. `test_a_hand_gate_waits_for_a_factory_gates_slot` (`tests/test_hand_gate.py`) fails if they overlap or the line is missing.
2. **R2. A factory gate waits for a hand gate's slot.** While `sdlc.py`'s slot is held, `factory.py gate` on another change waits and says so. `test_a_factory_gate_waits_for_a_hand_gates_slot` (`tests/test_factory.py`) fails if it runs at once.
3. **R3. `gate_jobs` comes from the base branch, the factory's way.** The hand gate reads it from the base branch's `.sdlc/factory.toml`, never the checkout's. A value the factory would refuse gives 1, as `_gate_jobs()` does.
   - `test_the_hand_gate_reads_gate_jobs_as_the_factory_does` sets values on the base branch (`3`, `0`, `-1`, `"2"`, `true`, `2.5`, missing, a file that won't parse) and on the checkout (`8`). It fails if `sdlc.py`'s value differs from `factory._gate_jobs(root)[0]` for any of them.
   - With `gate_jobs = 2`, a hand gate beside one held factory slot runs at once with no waiting line. The parametrized case in R1's test fails otherwise.
4. **R4. A hand gate gives up after a limit it names, and records nothing.** If no slot frees within `SLOT_WAIT` (default 30 minutes), it stops with a refusal and exits 1:
   ```
   no gate slot came free in 30 minutes (1 of 1 in use): nothing was judged, run it again
   ```
   It adds no attempt and leaves `build/gate.md` byte for byte as it was, so the board and status read the same record as before. `test_a_hand_gate_gives_up_after_its_wait_and_records_nothing` (with `SLOT_WAIT` patched to 0.5 s) fails if the record changes or a `FAIL` attempt appears.
5. **R5. Without the factory, the hand gate runs as it does today.** When `factory_enabled(home)` is false, it takes no slot: no wait, no waiting line, no lock file created in the git common dir, even while slot 0 is held. `test_without_the_factory_the_hand_gate_takes_no_slot` fails on any of the three.
6. **R6. The wait is reported, never timed.** `Seconds:` in the record measures the check alone, as in the factory, and the record's lines keep their shape (`test_the_record_is_the_factorys` still passes unchanged). The JSON summary gains `waited` (seconds, `0.0` for none) and `slot` (the index held, or `null` when no slot was taken). R1's test asserts `waited ≥ 0.5` while `seconds` stays below the check's own length plus a margin.
7. **R7. A slot outlives no gate.** A hand gate killed while it holds a slot frees it, and `factory.gate_slot()` takes it within 2 s. The lock file stays. `test_a_killed_hand_gate_frees_its_slot` is `portable`.
8. **R8. The copies are pinned.** `sdlc.py`'s copies must equal the factory's: `SLOT_NAME`, `SLOT_POLL`, the factory config path (`FACTORY_CONFIG == factory.CONFIG_FILE`) and the default (`GATE_JOBS_DEFAULT == factory.DEFAULTS["gate_jobs"]`). `test_the_slot_copies_are_the_factorys` (`portable`, `tests/test_hand_gate.py`) fails when either side's copy changes alone.
   - The lock functions are pinned by behaviour, not text. R1, R2 and R7 each hold a slot with one script's code and test it with the other's.
9. **R9. Waiting holds nothing else.** A hand gate waiting for a slot holds neither `_main_lock` nor `sdlc.lock`. `test_new_claims_a_number_while_a_hand_gate_waits` takes `_main_lock` while a hand gate waits, and fails if that blocks.
10. **R10. The docs say it.**
    - `docs/REFERENCE.md`'s *The gate, run by hand* names the shared slots, the waiting line, the limit and the refusal.
    - `plugins/factory/README.md`'s *One gate at a time* and *Mechanism* say that hand gates share the slots.
    - `factory.py`'s docstring says that `sdlc.py gate` takes the same lock files.

    These are checked at review; no test greps prose.

## Design

**Where the code goes.** All of it is in `scripts/sdlc.py`, beside `cmd_gate()` and under one comment block that says these are copies of `factory.py`'s slot code, pinned by `tests/test_hand_gate.py`.

- `SLOT_NAME = "sdlc-factory-gate-{}.lock"` and `SLOT_POLL = 0.25` are copies.
- `FACTORY_CONFIG = Path(HOST_DIR) / "factory.toml"` and `GATE_JOBS_DEFAULT = 1` are copies.
- `SLOT_WAIT = GATE_TIMEOUT` is the hand gate's own limit. The factory has none.
- `_gate_jobs_at(home, trunk) -> int` reads `git show refs/heads/<trunk>:.sdlc/factory.toml` and parses it with `tomllib`. It applies the factory's check (an `int`, not a `bool`, ≥ 1), otherwise `GATE_JOBS_DEFAULT`. A missing file, or one that won't parse, also gives the default, as `_base_factory()` returns `{}`. It returns no warnings: `factory.py config` already reports a bad value, and the hand gate isn't the place to raise it.
- `_try_lock(fd)` and `_unlock(fd)` copy the factory's. `msvcrt`, `fcntl` and `errno` are imported inside each, as `test_windows.py` requires.
- `_hand_slot(home, jobs, change, wait)` is a context manager that yields `(slot, waited)`. It follows `factory.gate_slot()`, with two differences:
  - It takes a deadline. When `time.monotonic() - start` passes `wait` with no slot held, it raises a small `SlotTimeout`. Before raising, it closes every descriptor it opened in its own `finally`.
  - Its waiting line names the limit, in whole minutes.

  The common dir comes from `git rev-parse --path-format=absolute --git-common-dir`. With no git dir it yields `(None, 0.0)`, as the factory's does.

**`cmd_gate()` order:**

1. Every refusal it makes today, unchanged: `trunk_refusal`, base config, `[commands] check`, `_one_change`, factory run, wrong branch.
2. `jobs = _gate_jobs_at(home, trunk) if factory_enabled(home)[0] else None`.
3. With `jobs`, enter `_hand_slot(home, jobs, folder.name, SLOT_WAIT)`. Without it, use a `nullcontext((None, 0.0))`. On `SlotTimeout`, return `_refused(...)` with R4's line, before any record is read or written.
4. Inside the block: `_hand_paths`, `before`, `build`, the timed run and `after`. These move inside, as in the factory's `cmd_gate`, so the build judged is the tree as it stands when the check starts, not when the wait began.
5. Outside the block: write the record exactly as today, and add `waited` and `slot` to the JSON summary.

**Edge cases:**

- **A wrong `factory_enabled()` answer.** A wrong false runs the hand gate beside a factory gate, which is today's behaviour. A wrong true makes a hand gate wait its turn when nothing else gates, which costs nothing. Neither writes anything wrong.
- **`gate_jobs` lowered after lock files for higher slots exist.** Only slots `0..jobs-1` are opened, as in the factory, so a leftover file is never a slot.
- **Two hand gates with the factory enabled.** They share the slots like any two gates. The intent's "as today" covers only the case without the factory.
- **On Windows,** the `msvcrt` byte-range lock at offset 0 on an empty file is the factory's own, so the two scripts lock the same byte.

**Not changed:** `factory.py`'s `gate_slot()`, its `gate` command and its record. R2's test proves the factory's gate already respects a slot taken by any process.

## Contracts touched

- **"`factory.py` never imports `sdlc.py`, and `sdlc` only reads the files a run leaves in a change's folder: each reads the other's files with copies of its parsing, pinned by tests"** (AGENTS.md, *The factory*). There is still no import either way. **This design widens the second half and needs a policy edit:** `sdlc.py` would now read one key, `gate_jobs`, from the base branch's `.sdlc/factory.toml`, and lock the factory's slot files. Both go through pinned copies (R8), the same mechanism `risk_paths()` uses. AGENTS.md's factory paragraph would need to say so, for example: "…and the base branch's `gate_jobs` and its slot files, for the hand gate". That is the person's decision (see the question below). Without it, the hand gate can't know how many slots exist; see the slot-0 alternative.
- **"A gate holds one of `gate_jobs` slots, locks in the git common dir, never `sdlc.lock`."** Kept. The hand gate locks the same files in the same dir, and R9 pins that it holds nothing else.
- **"Read from the base branch, so a change can't lighten its own…"** (`_config_at()`, `_base_factory()`). `gate_jobs` is read at `refs/heads/<trunk>`, never the checkout, so a change can't raise its own gate's room. R3 covers this.
- **`main` in a git call.** The ref is built from `trunk` (`refs/heads/{trunk}`), so `test_no_git_call_names_main_itself` still passes.
- **The scripts run on Windows.** Platform modules are imported inside `_try_lock`/`_unlock` only. The lock files are opened with `os.open` and never written as text, so the `newline` rule doesn't apply. R7 and R8 are `portable`.
- **`cmd_gate()` is never pre-approved.** It stays out of `READ_ONLY` and `ALLOW_RULES`, and no skill runs it. No skill text changes, so the skills' rules are untouched.
- **The board writes nothing and reads the record by its shape.** The record's shape doesn't change (R6), and a give-up writes nothing (R4), so `hand_gate()` and `_seen()` are untouched.
- **Nothing local.** Test data uses `008-reopen-drafts` and a neutral second change, as the existing tests do.

## Alternatives rejected

- **A shared module both scripts import.** Each plugin is cached on its own, and `factory.py` never imports `sdlc.py`. The house pattern is a pinned copy.
- **The hand gate takes slot 0 alone, needing no `gate_jobs`.** This would keep the contract unchanged and still never exceed `gate_jobs`. But every factory gate tries slot 0 first, so the hand gate would compete with each new factory gate for the busiest slot, and wait while others sit free. With `gate_jobs > 1` it could wait out its whole limit beside idle slots.
- **Locking every `sdlc-factory-gate-*.lock` already in the common dir.** Those files stay after `gate_jobs` is lowered. A hand gate taking slot 2 beside a factory gate on slot 0 under `gate_jobs = 1` would run two gates at once.
- **Detecting the factory by whether a lock file exists.** The first factory gate ever, started beside a hand gate, would race it. `factory_enabled()` already exists and is the one answer `sdlc` keeps.
- **Always taking a slot, factory or not.** Two hand gates would then queue where today they run together. The intent asks that nothing change without the factory.
- **Waiting with no limit, as the factory does.** The intent's constraint asks for a limit the gate names. A person is at the terminal, not a supervisor loop.
- **A give-up recorded as a `FAIL` attempt.** Nothing was judged. A red record would turn the board's card red and count in `fails`.
- **A config key for the wait, or a hand gate `jobs` of its own.** The intent didn't ask for either.
- **Taking `_main_lock` or `sdlc.lock` for the wait.** That would block `new` from claiming a number for as long as a gate runs.

## Verification

```bash
uv run --group dev pytest -q tests/test_hand_gate.py tests/test_factory.py -k "slot or gate"
uv run --group dev pytest -q -m portable -k slot
./check.sh
```

- **Healthy output:** every test above passes, among them the new `test_a_hand_gate_waits_for_a_factory_gates_slot`, `test_a_factory_gate_waits_for_a_hand_gates_slot`, `test_the_hand_gate_reads_gate_jobs_as_the_factory_does`, `test_a_hand_gate_gives_up_after_its_wait_and_records_nothing`, `test_without_the_factory_the_hand_gate_takes_no_slot`, `test_a_killed_hand_gate_frees_its_slot`, `test_the_slot_copies_are_the_factorys` and `test_new_claims_a_number_while_a_hand_gate_waits`. The existing `test_the_record_is_the_factorys`, `test_two_gates_with_a_limit_of_one_run_one_after_the_other` and `test_a_killed_gate_frees_its_slot` also pass unchanged, and `./check.sh` ends green with `claude plugin validate --strict` passing.
- **Patching the factory:** tests that need the factory enabled patch `sdlc.factory_enabled` (or point `HOME` at a temp dir), so a developer's own settings never decide a result.
- **By hand, with the factory enabled:** start `factory.py gate 008` in one worktree. While it runs, start `sdlc.py gate 009` in another. The second prints `009-…: waiting for a gate slot (1 of 1 in use), up to 30 minutes`, then runs once the first ends, and its JSON shows `waited` > 0 and `slot: 0`.

