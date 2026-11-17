---
id: 123
slug: evidence-reads
kind: plan
created: 2026-11-17
updated: 2026-11-18
---

# 123 — A passing check isn't stopped for a read without its exit · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `import shlex`; a new `is_read()` (with its `READS` set and
  per-program helpers) beside `EVIDENCE` and `EXIT_RE`; `read_evidence()` tracks whether the open
  command printed a non-blank, non-fence line and excuses a missing exit only for a read that did.
  Callers (`loop_state()`, `land_verdict()`, the mend prompts) are untouched.
  Round 1's review tightened it past the spec's Design: `rg` has its own condition (no `--pre` or
  `--pre-glob`, which run a program), awk's `system` is matched with any space before its `(`, and
  a digit redirect target passes only after `>&`, never after `>`, `>>` or `&>`, where it names a
  file.
- `tests/test_factory.py`: R1's table test (portable), R2, R3, R6 tests, R4's new parametrized case,
  and `test_a_build_mend_is_refused_when_verdicts_names_none`'s reply moved off `head` (R7).
- `tests/test_land.py`: `NO_EXIT` becomes `$ uv run pytest -q` with output (R7), a guard test that
  it still fails `read_evidence()`, and R5's `test_119s_landing_replies_pass`.
- `plugins/factory/agents/reviewer-behaviour.md`, `plugins/factory/agents/builder.md`: still ask
  for `exit: <n>` on every command; the stop sentence says "unless it is a read that shows its
  output" (R8).
- `plugins/factory/README.md` (*Shown, not said*) and `AGENTS.md`'s factory paragraph: name
  `is_read()` beside `read_evidence()` (R8).
- `tests/test_skills.py`: one assert that both prompts carry "a read that shows its output" (R8).

Reused: `EXIT_RE`, `read_evidence()`'s loop, the test files' `_change`, `_round`, `_report`,
`_verdicts`, `_landing`, `_folder`, `_run` helpers.

## Work order

1. **`is_read()` alone** (R1): the table test first, red on the missing function; then the function
   (refuse substitutions outside single quotes, `shlex` tokenise with punctuation chars, split on
   `| || && ;`, redirections only to `/dev/null` or a descriptor, per-program rules for `awk`,
   `sed`, `sort`, `find`, `git`). Nothing calls it yet.
2. **`read_evidence()` excuses a read that shows output** (R2, R3, R4, R6): tests first (R2, R3
   and R6 red, R4's new case green already and staying green), then the one change in the loop.
3. **Landing fixtures** (R5, R7): `NO_EXIT` moved to a non-read with its guard test, the build-mend
   test's reply likewise, and the 119 replies test.
4. **Prompts and docs** (R8): the skills test's new assert red, then the prompt, README and
   AGENTS.md edits. `./check.sh` at the end.

## Tests

- R1: `test_a_read_is_only_what_the_script_can_tell_changes_nothing` (`tests/test_factory.py`,
  `portable`), the spec's table of reads and non-reads.
- R2: `test_a_read_showing_its_output_needs_no_exit`.
- R3: `test_a_silent_read_still_needs_its_exit` (`$ cmp a b` then the next `$`, and at the end).
- R4: a new case in `test_a_builder_report_without_its_evidence_stops_the_run`,
  `$ uv run pytest -q | grep passed` with output and no exit.
- R5: `test_119s_landing_replies_pass` (`tests/test_land.py`).
- R6: `test_a_builders_read_needs_no_exit`: `verdicts` gives `review`.
- R7: `test_no_exit_is_not_a_read` guards `NO_EXIT`; 109's three landing tests and the build-mend
  test keep passing on a real missing exit.
- R8: `test_what_runs_the_change_shows_its_evidence_and_never_runs_checks` gains one assert.

## Rollback

`git revert` undoes all of it: the change writes no data, publishes nothing and renames nothing a
host points at. Reports written while it was in place stay valid under the old rule only if they
carry every exit; a run stopped after a revert is mended or shipped by hand as before 123.
