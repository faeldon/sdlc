VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:1060 (`_awk_reads`): the check for `system(` is a literal substring, so `awk 'BEGIN{system ("rm f")}'` passes `is_read()`. awk allows whitespace between a builtin's name and its `(`, so the program runs `rm`, and with any output line shown it owes no `exit:`. Fix: match `system\s*\(` with a regex, and add a row to `NON_READS`.
- CHANGE: plugins/factory/scripts/factory.py:1163 (`is_read`, redirect branch): `target.isdigit()` is accepted for every output redirect, not only `>&`. `cat a >2` and `cat a > 1` therefore pass as reads while writing a file named `2` or `1`. Only the `>&` form (`2>&1`, `>&2`) names a descriptor. Fix: accept a digit target only when the token is `>&`, and add `cat a >2` to `NON_READS`.
- CHANGE: plugins/factory/scripts/factory.py:1089 (`READS`): `rg` is a plain read, but `rg --pre <cmd>` runs an arbitrary program on each file, and `rg --pre ./x y` passes today. Fix: take `rg` out of the plain set and refuse `--pre` and `--pre-glob`, or drop `rg` from the allowlist. Add a `NON_READS` row.

All three are gaps in the spec's own rule: "a command it misjudges as a read would let a claim go unrecorded, so the allowlist is closed". The fixes are small. Each adds a table row.

## Notes

- **Requirement coverage:** R1–R8 each have code and a test that would fail without it.
  - R2 and R3 are covered by `test_a_read_showing_its_output_needs_no_exit` and `test_a_silent_read_still_needs_its_exit`.
  - R4 has the new `pytest | grep` case.
  - R5 has `test_119s_landing_replies_pass`.
  - R6 has `test_a_builders_read_needs_no_exit`.
  - R7 has `NO_EXIT` moved onto `uv run pytest -q`, with its guard test `test_no_exit_is_not_a_read`.
  - R8 has the new assert in `tests/test_skills.py`, plus the prompt, README and AGENTS.md edits.
- **Optional:** `git` allows `diff --ext-diff` and `--textconv`, which can run a configured external program. This is a minor extension of the same class as the `rg --pre` finding.
- **Optional:** `test_119s_landing_replies_pass` needs `uv`, so it is skipped without it. The `is_read()` table test is `portable`, so the core judgment is still covered on Windows.
- **Done well:**
  - The change stays inside `read_evidence()` plus one new pure function, so the callers and the mend routing are untouched.
  - It excuses a read only when it printed a line, so a silent `cmp` or `grep -q` still owes its exit.
  - `_substitutes()` correctly leaves single-quoted `$(` alone.
  - The 109 tests were moved onto a real non-read instead of being weakened.
- **Ran:** `pytest -n auto tests/test_factory.py tests/test_land.py tests/test_skills.py tests/test_board.py` gave 748 passed and 13 skipped. I also probed `is_read()` directly, which is how I found the three holes above. I did not run `./check.sh`.
