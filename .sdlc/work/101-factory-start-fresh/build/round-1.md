Change 101 is built and left uncommitted. `./check.sh` passes: 2013 tests, exit 0. I raised no decisions.

**Slices built** (each test seen failing first, for the reason expected):
1. **`start` says how far behind it is (R1).** `start` now reports `base` and `behind`, for both `--for build` and `--for spec`, and still writes nothing.
2. **`factory.py fresh <NNN>` (R2–R5).** It runs `sdlc.py base`, and `sdlc.py resolve` when `base` refuses with `resolvable`. It adds no git step of its own.
   - A clean conflict ends as `resolved`.
   - A real conflict is undone with `resolve --abort` and refused, naming the files and the way on (`/sdlc:ship`, or `sdlc.py resolve`).
   - At `stage: build` it returns `held` without running `sdlc.py` at all.
   - A stage no run starts from is refused in `start`'s words. A restart at `stage: test` is let through.
3. **`gate_jobs` (R7).** It is read from the base branch's `factory.toml`, default 1. A bad value, or a checkout value that differs from the base's, gets a warning. `config` and `start` show it.
4. **Gate slots (R8–R11).**
   - **Locking:** `gate_slot()` holds a non-blocking OS lock on `sdlc-factory-gate-<k>.lock` in the git common dir. `fcntl` and `msvcrt` are imported inside the functions that use them.
   - **Waiting:** a gate with no free slot prints the waiting line once, then retries every 0.25 s.
   - **In `cmd_gate()`:** the check now runs inside the slot. The JSON gains `waited` and `slot`. The record file keeps its shape.
5. **Build skill (R6).** Step 0 runs `fresh` after a `start` with no refusals, and stops on its refusal. It keeps `fresh`'s `head` for `verdicts`. Step 1 shows `behind`, the state, `from` → `head`, and `undo`, or the `held` wording. The skill gains the new `Bash(...)` rule and a sentence on gate slots.
6. **Docs (R12).** `plugins/factory/README.md`, `factory.py`'s docstring, and AGENTS.md's *Writes before a WAIT* paragraph (now four exceptions) and *The factory* paragraph.

**Tests added** (`tests/test_factory.py` unless noted):
- `test_start_says_how_far_behind_the_base_the_change_is` (both purposes): R1.
- `test_fresh_fast_forwards_a_change_behind_the_base`: R2. It uses a real `sdlc.py new --worktree` change; the folder comes through byte for byte and `undo` names `reset --keep`.
- `test_fresh_holds_a_run_that_stopped_part_way`: R3.
- `test_fresh_refuses_a_stage_no_fresh_run_starts_from`: R2's stage rule, including the restart path.
- `test_fresh_resolves_what_git_can_and_stops_on_a_real_conflict`: R4, both cases, with no stash and no merge commit.
- `test_fresh_refuses_without_its_own_sdlc`: R5.
- `test_gate_jobs_is_read_from_the_base_branch_and_checked` (0, true, text, 1.5): R7.
- `test_two_gates_with_a_limit_of_one_run_one_after_the_other` (limits 1 and 2): R8 and R9. With 1, the runs don't overlap, the waiting line appears, `waited >= 0.5` and `seconds < 1.8`. With 2, they overlap.
- `test_a_killed_gate_frees_its_slot` (`portable`): R10.
- `test_build_brings_the_change_up_to_date_before_its_spec_writer` (`tests/test_skills.py`): R6.
- `test_config_defaults_and_its_warnings` was updated for the new key.

**`plan.md`**: written before the code, from the scaffold. The build kept to it apart from one extra test, for the refused-stage and restart branches.

**Left in `notes.md`** (both unticked):
- The hand gate (`sdlc.py gate`) takes no slot, as the spec says.
- `/sdlc-factory:spec` gets `behind` from `start` but neither shows it nor runs `fresh`.

**`.sdlc/work/inbox.md`** was already modified in this worktree when I started. I didn't touch it.

## Evidence

```
$ ./check.sh > /tmp/check-101.log 2>&1; echo "exit: $?"; grep -E "passed|failed|error" /tmp/check-101.log
exit: 0
All checks passed!
2013 passed in 71.12s (0:01:11)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py -k "behind or fresh or gate_jobs or two_gates or killed_gate"
14 passed, 158 deselected in 12.18s
exit: 0

$ uv run --group dev pytest -q -m portable
217 passed, 1796 deselected in 66.83s (0:01:06)
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py
345 passed in 0.75s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -k "up_to_date"   (before the skill edit)
E       AssertionError: fresh runs in Step 0's bash
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "two_gates or killed_gate"   (before gate_slot)
E           AssertionError: {'other': {...}, 'repo': {...}}   (intervals overlapped)
E           KeyError: 'waited'
E           AssertionError: assert '' == 'held 0'
3 failed, 169 deselected in 3.21s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k fresh   (before cmd_fresh)
5 failed, 160 deselected in 38.21s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k behind   (before behind_base)
2 failed, 158 deselected in 8.45s
exit: 1
```
