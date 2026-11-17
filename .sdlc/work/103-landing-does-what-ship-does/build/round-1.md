The landing now does what `/sdlc:ship` does: a batch with acceptance checks, an undone note and an irreversible path landed through `factory.py` alone in the end-to-end test. `plan.md` was written first, and each step's test was written and seen to fail before the code. `./check.sh` passes with 2008 tests. Nothing is committed.

**The question and the batch (R1–R3)**
- Acceptance checks, skills' cases in scope, undone notes and assumed decisions no longer keep a change out of `land-check`'s batch. Each is now a signal, so a batch holding one never lands without the person's yes.
- `land-check` shows, for each change, its checks, its cases with their $5 cap, each undone note with its proposed fate (carried as a seed or dropped), each assumed decision, and its `How to recover:` lines. It also prints the batch's question, which adds a clause only for what the batch holds.
- The one exclusion left: a change touching an irreversible path that the approver gave no way back for.

**The new commands (R4–R7, R11)**
- `factory.py accept <NNN>` runs the checks through `sdlc.py accept` and records each attempt in `build/land-accept.md`. That record sits in the change's folder, which the build identity leaves out, so writing it doesn't change what it records.
- `factory.py cases <NNN>` runs `sdlc.py run-cases` for one change and writes the `Skill evals:` line `sdlc.py ship` reads. A failed case writes nothing.
- No skill's allowed rules cover either command, so the harness asks before every run.
- `land` refuses, before writing anything, a change whose checks haven't passed on it as it stands or whose cases haven't run.
- After a rebase, `land-verdicts` says `accept`: the checks run again after the gate and before any review, and a failure stops the change. The cases are not rerun, since each run is paid.

**What the yes writes (R8–R10, R12)**
- On `--by person`, before `sdlc.py ship`, `land` adds each carried note to the register as a seed, ticks dropped notes with their reason, and ticks each assumed decision as confirmed. A rerun writes none of these twice.
- The commit carries `Carried forward:`, `Dropped:` and `How to recover:` paragraphs, plus `Sdlc-Landed: by=person`.
- The approver is now told which irreversible paths the diff touches and asked for one `- UNDONE:` line per unticked note and one `- RECOVER:` line per irreversible path. An item with no proposal is carried as a seed, never dropped.

**Two things not in the spec**
- **A `resolve` bug fix.** When `.sdlc/last-id` was the only file a rebase conflicted on, `resolve` settled it, then refused and left the rebase stopped. Every batch of two or more locally numbered changes hit this at its second change, so the end-to-end test (R13) couldn't pass. `resolve` now carries on with the rebase and reports `clean`. The skill's Step 3 treats `clean` like `rebased`; it runs the builder only when files are listed as conflicted. This is recorded in `plan.md`.
- **The `Fresh review:` line.** `land` used to write it only when `findings.md` was missing. Since `factory.py cases` can now create that file first, `land` now writes the line whenever it's absent from the file's note.

**Tests:** 9 new tests in `tests/test_land.py` for R1–R5, R7, R8, R10, R11 and R13, and one existing test extended for R9. One test in `test_factory.py` pins the factory's copies of `CASES_RE`, `FRESH_RE` and the cases' cost cap to `sdlc.py`'s. `test_no_skill_lets_accept_run_unasked` now covers both factory commands; I confirmed it fails on a rule that would grant `factory.py accept`. The cases can't run in a scratch repo, so R5 and R7 use stand-ins for `sdlc.py`'s output.

The README, the land skill (description, Steps 0–4, Out of scope) and `approver.md` are updated, and "shipped by hand" no longer appears in `plugins/factory`. Nothing was added to `notes.md`.

- DECISION: [default] Keep the `resolve` counter-only conflict fix in this change, or split it into its own? Options: keep; split. Recommend keep: R13's batch of three can't land without it, and it's about 10 lines in the landing's own `cmd_resolve`, plus the skill's Step 3 split.

## Evidence

$ ./check.sh
All checks passed!
207 files already formatted
2008 passed in 37.34s
✔ Validation passed
exit: 0

$ uv run --group dev pytest tests/test_land.py -q -n auto
16 passed in 6.10s
exit: 0

$ uv run --group dev pytest tests/test_skills.py tests/test_factory.py -q -n auto
503 passed in 7.98s
exit: 0

$ git grep -n "shipped by hand\|ship those by hand" plugins/factory
(no output: no match)
exit: 1
