VERDICT: PASS

The kept change is done. `is_read()` now swaps `HOME_MARK` and `CLONE_MARK` for plain words before it tokenises (`factory.py:1349-1350`), and `test_a_read_naming_a_mark_is_still_a_read` covers the case the round named: a reply whose read names `<home>` and prints a line, with no `exit:`, passes `read_evidence()`.

## Notes

- Probed `is_read()` directly on the cases that matter:
  - `ls ~/.nvm/bin` and `ls <home>/.nvm/bin` both read True, as do `ls <path-to-clone>/x` and `cat <home>/a >/dev/null`.
  - A redirect to a real file stays a non-read: `cat <home>/a >out`, `cat <home>/a >>out`, and `cat <home>/a > <home>/b` are all False.
  - A mark cannot hide a redirect: `cat x >/dev/null<home>`, `cat x >'<home>'` and `echo <home>>out` are all False.
  - `<home>/bin/tool` as a program name is False, since it isn't on the allowlist.
- Good: the swap runs after `_substitutes()`, so it can't create a substitution, and it touches only the two exact marks. Any literal `<` or `>` left in a command still tokenises as before.
- Good: the new test checks both marks, the read with its missing `exit:`, and that a real redirect beside a mark is still a non-read. That is the regression the rework could have introduced.
- Ran `uv run --group dev pytest -q tests/test_factory.py -k "evidence or is_read or read or home or 135"`: 36 passed, 244 deselected. I did not run the full suite or `./check.sh`.
- Not reviewed: `docs/REFERENCE.md`, `scripts/sdlc.py` and `tests/test_hand_gate.py` also show as modified in `git status`, but they are outside this round's reworked paths, so I left them alone.
