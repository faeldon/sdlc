The register no longer rides a change's branch. Ship and the factory's landing now hold what they file and retire in the change's `entries.md`, and close applies it inside the `Close` commit. The gate passes (2428 passed, 13 skipped), and nothing is committed.

**Slices built**
1. **The held file and the plan.** `held_entries()` reads a change's `entries.md`: `Retire <id>: <reason>` lines, then whole entries. `register_plan()` is the pure function close runs. It removes the seeds named by `idea:`, the bugs named by `fixes:` and each retired nit, then appends the held entries. It skips an entry the register already holds word for word, and reports a retirement that is already gone as `gone`. It refuses an unreadable file, a title that matches two entries, or a held id the register holds with other text. `_drop_seed()` is gone; its span rule is now `_without_entry()`.
2. **Ship and close.** `sdlc.py ship` no longer deletes anything. It refuses an uncommitted register edit before stamping (R11) and says what close will retire and file. `cmd_close()` checks the plan before its merge, alongside its other preconditions (R6), and shows `report["register"]`, `--check` included. `_close_commit()` takes `_main_lock()`, rereads the register, writes it, and commits it with the folder's removal in one `Close` commit (R4, R7). A failed step puts the register back.
3. **The edge cases.** `next_entry_ids()` now also counts ids in `entries.md` files, on disk and in any commit (R8). `recorded_issues()` reads each checkout's `entries.md` (R9). A shipped change keeps claiming its seed until close (R10). `drop` refuses while `entries.md` holds an entry (R12).
4. **The factory.** `_dispose()` writes `entries.md` and no longer needs the register's template. `retire_nits()` writes `Retire` lines. The rerun after a failed commit takes its nits from `named_nits()` again, which is idempotent (R1–R3). `ENTRIES` and `RETIRE_RE` are copies of sdlc's, pinned by a test (R13).
5. **The outcome tests (R5),** one for ship by hand and one for factory landings. In the hand test I delete `.sdlc/last-id` before shipping, because it conflicts by itself; the factory test lets `resolve` settle it as usual.
6. **The docs (R14).** Ship's `SKILL.md`, `undone.md`, `closes.md`, `factory.md` and `conflict.md` now say where entries go. So do the land skill, REFERENCE.md and AGENTS.md (*Closing*, *The register*). I trimmed ship's `SKILL.md` back under its 475-line budget.

**Tests**
- **New, `tests/test_register_lands.py`:** R1 by hand, R4, R6 (three tests: refused before the merge, an unreadable file, a rerun filing once), R7, R11, R12, R8, R9 and R5 by hand.
- **New, `test_land.py`:** R1 for the factory, R2, R13 and R5 for the factory.
- **New, `test_skills.py`:** R14. I checked its regex against the old skill text, and it catches each old instruction.
- **Rewritten:** the `test_ship_deletes_*` cases are now `test_close_retires_*`, run against `register_plan()` as pure text. Also rewritten: two tests in `test_bugs.py` and R10's `test_a_shipped_change_claims_its_seed_until_it_closes`.
- **Adapted:**
  - `test_adoption`: ship's output and the `Close` commit now hold the register change.
  - `test_archive`: the split-off seed is held in `entries.md`.
  - `test_resolve`: the old-way edit is refused, moved to `entries.md`, then filed.
  - `test_land`: the resolution fixture now builds a branch shipped the old way, since only that kind can still conflict on the register.

I saw the new tests fail before their code, except R10's: I changed `_open_claims()` before rewriting that test, so I never ran it red. By reading, the old code returned 0 where the test expects 1.

**What changed in `plan.md`:** the plan is written, then updated to match the build: `_branch_register_plan()` added, `_drop_seed()` removed rather than wrapped, the extra test files adapted, and a note that the `close_retires` cases run the pure planner rather than a full close each.

**Left in `notes.md`** (two unticked lines, so ship will ask you to give each a disposition):
- Close holds the lock only around its write and commit, not from its merge. An `inbox-commit` landing in that window would put a `File` commit between the change and its `Close`. This gap existed before this change.
- The R7 test proves close rereads the register under the lock, not that two processes contend for it.

Ship will also want a `Skill evals:` note in `findings.md`, because this touches `skills/ship/`. Running the evals is a paid call, so that's your decision.

- DECISION: [default] Should drop refuse when `entries.md` holds only `Retire` lines? Options: refuse on entries only; refuse on any line. Going ahead with entries only: a drop retires nothing, so losing those lines is what should happen.
- DECISION: [default] Should `held_entries()` accept `>` note lines and the `# ` title before the first entry? Options: accept them; accept only `Retire` and blank lines. Going ahead with accepting them; any other stray line is refused, naming its line.

## Evidence

$ ./check.sh
All checks passed!
250 files already formatted
2428 passed, 13 skipped in 240.01s (0:04:00)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -m portable
396 passed, 13 skipped, 2032 deselected in 138.11s (0:02:18)
exit: 0

$ uv run --group dev pytest -q tests/test_register_lands.py tests/test_land.py tests/test_sdlc.py tests/test_bugs.py tests/test_inbox.py tests/test_groups.py tests/test_nits.py tests/test_resolve.py tests/test_archive.py tests/test_skills.py -n auto
930 passed in 53.84s
exit: 0

$ uv run --group dev pytest -q tests/test_register_lands.py   (before close's code)
8 failed, 2 passed in 3.05s
exit: 1

$ uv run --group dev pytest -q tests/test_sdlc.py -k "close_retires or held or …"   (before register_plan)
24 failed, 8 passed, 215 deselected in 2.01s
exit: 1

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0
