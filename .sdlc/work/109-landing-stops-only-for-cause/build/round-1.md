All 14 requirements are built and the full gate passes (2189 passed, 9 skipped). Everything is left uncommitted for `/sdlc:ship`. `plan.md` was written first, after reading the code.

**Slices built**, each with its test run red for the expected reason before the code went in:
1. **R7–R9, the landing commit.** The commit moved into a new `_land_commit()`. When git refuses it, the refusal now carries the tail of git's own output. A rerun after a commit that failed after `sdlc.py ship` makes the commit, with the same message and the same `Retired nits:`. A change a person shipped and committed by hand is still refused and gets no new commit.
2. **R11–R12, carried notes.** A note's indented continuation lines are now part of its text, in `land-check` and in the seed's body. A note with no proposal gets a seed titled by its first sentence. A proposal matches a note on its first line or its full text.
3. **R13, the register after a resolution.** When `.sdlc/work/inbox.md` conflicts, `resolve --continue` deletes, by id only, the entries the change's `idea:` and `fixes:` name and the nits it retired, and reports them as `dropped`. The builder's resolve prompt also lists those ids.
4. **R5.** `agent --task mend` is refused unless `verdicts` names that role in a `mend` stop. This closes the path that filed 103's landing mend into its build round.
5. **R10, build loop.** The approver (`DECISION:` after a preamble) and the verifier (answers the script can't read) each get one mend a round, in their own resumed session.
6. **R1–R4, R6 and R10, landing.** `land-verdicts` now says `next: mend` when every problem is mendable: a missing `exit:` or evidence section, a verdict after a preamble, or the verifier's unread answers. A new `--task land-mend` writes only under `reviews/land-<n>/` and records `<role> land-<n>`. Landing and build mends don't use up each other's allowance. A red gate beside a mendable problem still stops.
7. **R14 and docs.** The land skill runs `land-mend` for each role `land-verdicts` lists. The build skill now names the approver and verifier mends. The behaviour, approver and verifier agent prompts, the factory README and AGENTS.md's factory paragraph are updated.

**Tests added:** the 15 the spec names, plus `test_a_resolution_drops_entries_by_id_alone`, which checks that a seed named by title is skipped and a fenced example is never matched. R6 and R9 passed before any code changed: the spec says those keep today's behaviour, so their tests only pin it.

**Existing tests I changed:**
- Two tests asked for a builder mend when nothing needed one. R5 now refuses that, so each first gives the builder a report without its evidence.
- One assertion in the preamble test now expects R5's refusal message instead of "owe evidence".
- `test_a_record_is_never_amended_into_a_commit_the_landing_didnt_make` is now `test_a_hand_shipped_change_is_not_committed_again`. Its hand-made commit now includes `intent.md` at `stage: shipped`, because under R8 a commit without it reads as a landing whose commit failed.

**Changes to `plan.md`:** it records that test rename, and that `read_verified()` now takes the file name to use in its problems, so a landing round's problems say `reviews/land-<n>/verified.md` instead of `reviews/round-<n>/`.

**`notes.md`:** besides the rename and the `read_verified()` change, one build note: `drop_entries()` ends an entry at the next level-one or level-two heading, so a `###` inside a retired nit is now deleted with it. One item is left open:
- [ ] `_resolve()`'s messages still say "round <n>" when the round is a landing round.

No decisions raised.

## Evidence

$ uv run --group dev pytest -q tests/test_land.py -k "hand_shipped or carries_git or commit_failed"   (before the code)
FAILED tests/test_land.py::test_a_failed_landing_commit_carries_git_s_error
FAILED tests/test_land.py::test_a_landing_whose_commit_failed_commits_on_rerun
2 failed, 1 passed, 34 deselected in 8.77s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -n auto -k "mend or preamble or for_cause"   (before the code)
5 failed, 2 passed in 3.29s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_land.py tests/test_factory.py
252 passed in 17.57s
exit: 0

$ ./check.sh
All checks passed!
2189 passed, 9 skipped in 82.16s (0:01:22)
✔ Validation passed
✔ Validation passed
exit: 0
