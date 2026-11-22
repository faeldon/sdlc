# 232 — Plan

> Tier 1 with four files touched, so a plan: what changes, in what order, and what proves it.

## Files to change

- `plugins/factory/scripts/factory.py`: `EXIT_RE` takes a note after the code, after a space:
  `^\s*exit:\s*\d+(?:\s.*)?$`. Slightly narrower than the intent's `\d+\b.*`, which would also
  read `exit: 2.5` or `exit: 2(x)` as code 2; a space-separated note is what agents write.
  `read_evidence()` and `is_read()` are unchanged.
- `plugins/factory/agents/reviewer-behaviour.md`, `plugins/factory/agents/builder.md`: each
  *Evidence* paragraph says every command that ran ends `; echo "exit: $?"` and records the
  number, never a word, and that a command a hook refused is no `$ ` line. The reviewer lists it
  under `## Notes` (its prompt has no *Not run* section; Notes already holds "anything you
  couldn't run and why"); the builder says so in its report. "every command, reads included",
  which tests pin, stays.
- `tests/test_factory_depth.py`: one parametrized test beside 215's behaviour-evidence test.

## Work order

1. The parser: the test red on the two noted exits, then the regex.
2. The prompts, proved by `checks.md`.

## Tests

- `test_an_exit_with_a_note_after_its_code_is_an_exit`: `verdicts` on a behaviour reply with
  `exit: 2 (note)`, `exit: 0 # ok`, `exit: 1` finds no problem; `exit: nonzero (...)`,
  `exit: not run (...)` and `exit: 2x` still name the missing exit and stop.
- `checks.md`: both prompts carry the hook and real-code sentences.

## Rollback

Nothing outside the tree: `git revert` undoes it all.
