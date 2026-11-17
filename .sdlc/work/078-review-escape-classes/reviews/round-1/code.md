VERDICT: CHANGES

- CHANGE: .sdlc/REVIEW.md:50: The bullet says "The escapes from 047 and 050 are pinned by `test_a_question_ends_with_a_question_mark_its_answers_after_it_or_not` and `test_a_skill_the_session_starts_counts_as_typed`." The commit history doesn't support that mapping. The question test came in d34c428, the 050 change, and its parametrised cases cite 049. The skill test came in 47031e0, which is change 052's fix (its Important finding, per the intent's own list). Nothing in the history ties either test to 047's escape. Correct the attribution so each named test is credited to the change whose finding it pins, and say "no test pins 047's escape" if none does. This is a text edit only.

## Notes

- The first bullet's rule says a change to how an event is read "carries a test built from a real transcript's entries." The two tests it cites are built from hand-written events. The `tests/test_metrics.py` docstring says every fixture is "built here under a made-up path." The rule and the cited tests disagree, so either soften the rule to "built from the shape of a real transcript's entries" or name a fixture that really is recorded. The bullet's rule is decisions.md's D1 default, which the person hasn't answered, so flag it for them.
- Spec open question 1 (does each bullet name its test) is answered yes for both bullets, and the second bullet's named tests exist. Its mention of "git's quoted path against its `-z` output" is not visibly pinned by `test_a_non_ascii_hotspot_on_the_base_branch_is_not_gone`, which exercises the numstat/path-listing quoting match only. Consider naming only what the test covers.
- `test_paths_shown_are_posix` (tests/test_windows.py:310) exercises `sdlc._shown` on one constructed path. It passes trivially on darwin and only bites on Windows, so the bullet's "pinned by" claim holds only in CI's Windows job. Worth saying so in the bullet.
- inbox.md's entry 2026-11-17-2 changed to `[building]` with a "Building in ..." line. That's expected for a change in flight and matches AGENTS.md's claim rule, so it needs no action.

## Done well

- The two bullets are in the list's register, cite changes by id, name no host, and don't restate `guide/review.md`.
- Both tests the second bullet cites exist, and the bullet names the escape each is about.
- `checks.md`'s acceptance check (`grep` for both bullet headings) passes against the current REVIEW.md.

## Tests and commands run

- `uv run --group dev pytest -q tests/test_defaults.py tests/test_metrics.py tests/test_windows.py tests/test_retro.py -k "defaults or question_ends or counts_as_typed or paths_shown_are_posix or non_ascii_hotspot"`: 129 passed, 238 deselected. The `-k` filter is broad, so this is not the full gate.
- The acceptance check from `checks.md`: exits 0.
- Not run: the full `./check.sh`, and the `test_defaults` block-under-heading check beyond the selected run.
