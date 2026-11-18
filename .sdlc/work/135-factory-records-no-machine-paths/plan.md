# 135 — Plan

> How the Approach is built, written after reading the code: the files it touches, the order of
> its slices, and which test proves which outcome.

## Files to change

- `plugins/factory/scripts/factory.py`: `HOME_MARK` becomes `<home>`; `cmd_agent` runs the reply
  through the existing `_placeholders(reply, root)` once, right after a successful session and
  before either write, so the plain write and `_file_draft()` (the spec draft and its questions)
  both get it. No new helper: `_placeholders()` already finds the main checkout
  (`_all_checkouts()`) from the worktree `cmd_agent` runs in.
  `is_read()` swaps both marks for plain words before tokenising, so a filed read naming
  `<home>` or `<path-to-clone>` isn't taken for a redirect (round 1's review).
- `scripts/sdlc.py`: the pinned copy's `HOME_MARK` becomes `<home>` too
  (`test_the_copies_are_the_factorys`).
- `docs/REFERENCE.md`: the hand gate's paragraph says the home directory is written `<home>`.
- `tests/test_factory.py`: the gate record test's expected `~/.cache` becomes `<home>/.cache`;
  three new tests. `tests/test_hand_gate.py`: its `under ~` expectation becomes `under <home>`.

## The home mark

`<home>`, matching `<path-to-clone>`'s shape. `~` followed by any path reads `~/<dir>/`, which
`test_nothing_local`'s `~/[\w-]+/` catches; `<home>/<dir>/` matches none of `PATTERNS`. Nothing
parses the mark: the board and `sdlc.py` read a record's `VERDICT:`/`CHANGE:`/`GATE:` lines, not
its paths, and only the two tests above pin the old mark's text.

## Work order

1. **The mark.** Red: a `_placeholders()` result for a path under home but outside the clone, and
   for a cut-short clone path, is checked against `test_nothing_local.PATTERNS` (loaded by path)
   and fails with `~`. Green: `HOME_MARK = "<home>"` in both scripts; update the two pinned
   expectations and REFERENCE.md.
2. **Replies.** Red: a fake `claude` reply quoting the clone's path and the home directory, filed
   by `cmd_agent` as a builder report and as a spec draft, holds neither path. Green: one `_placeholders`
   call in `cmd_agent`.

## Tests

- `test_a_path_under_home_is_filed_in_a_form_the_scan_accepts`: Outcome 2.
- `test_every_reply_is_filed_without_this_machine_s_paths`: Outcome 1, and Outcome 3's case (an
  agent quoting `git worktree list` output, which names the main checkout and a worktree).
- `test_a_read_naming_a_mark_is_still_a_read`: a read naming a mark owes no `exit:`.
- `tests/test_hand_gate.py`'s pins: the copy stays the factory's.

## Rollback

Nothing outside the code: `git revert` undoes it. Records already committed keep `~`, as the
intent's constraints ask.
