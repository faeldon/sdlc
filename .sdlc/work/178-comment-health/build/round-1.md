I built change 178 and left it uncommitted for `/sdlc:ship`. The new `.sdlc/comment-health.py` prints the four comment signals as indicator rows. All 17 of its tests pass, and so does the full gate.

On this repo's base branch it runs in about 2.6 s, well under the 60 s evidence timeout, and prints 33 rows:
- **Density:** 0.193 across all scripts, with no file outside 0.10–0.40.
- **Narration share:** 0.005.
- **Comment token share:** 0.294, about 98k estimated tokens. This matches the seed's "about 30%".
- **Docstring coverage:** 207 long functions, 0.957 with a docstring; 60 hot functions, 0.867.

**Slices built**
1. **Measures for one file** (R2, R7, R8, R11, R10): comments are read with `tokenize`, never by text. Directives, the PEP 723 block and a line-1 shebang don't count as comments. A file that doesn't parse gives no rows.
2. **Long functions** (R5): top-level functions and methods of top-level classes spanning 30 lines or more, with whether each has a docstring.
3. **Rows** (R1, R3, R4, R12): one fixed order. The band count is always printed, and a share of nothing isn't.
4. **Hot functions** (R6): loads `function-heat.py` by path and uses its `heat()`/`rank()`, keeping functions with a commit since the last retrospective. There is no copy of its code.
5. **`main()`** (R9, R10): lists files with `git ls-tree -z` on the base branch and reads them with `git show`. With no base branch it exits 1 with one line on stderr.
6. **Wiring** (R13, R14, R15): the `retro.indicators` entry in `.sdlc/config.toml` after function heat, the script added to `SCRIPTS` in `tests/test_windows.py`, and the scorecard's S17 row, Wave 3 line and a new *Supporting: comment health* entry with Cost as its guardrail.

**Tests added** (`tests/test_comment_health.py`, marked `portable`), each named in `plan.md` against its requirement:
- R1–R13 are each covered as the spec names them.
- `test_words_split_identifiers_and_drop_short_and_stopwords` was added beyond the spec.
- R14 is covered by the existing parametrised checks in `tests/test_windows.py`.
- R15 has no test, as the spec says. It is covered by an acceptance check in `checks.md`, which exits 0.

**What changed in `plan.md`:** the scaffold is replaced with the plan, plus a *Departures while building* section:
- A shebang counts as a directive. `scripts/sdlc.py` starts with one, but the spec's list doesn't name it.
- A function nested in a long one counts only as the function that holds it. That outer function is itself long, so the R5 test expects `outer`.
- `hot()` returns a list of docstring flags that `rows()` takes, so the rows can be tested without git.

**`notes.md`:** nothing left.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_comment_health.py
1 failed, 16 passed in 2.71s   (red before the config entry: test_this_repo_runs_comment_health)
exit: 1

$ uv run --group dev pytest -q tests/test_comment_health.py tests/test_function_heat.py tests/test_windows.py tests/test_nothing_local.py
78 passed in 12.25s
exit: 0

$ uv run --group dev ruff check .sdlc/comment-health.py tests/
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
314 files already formatted
exit: 0

$ sh -c "<checks.md's R15 block>"
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 178
All checks passed!
3261 passed, 29 skipped in 147.93s (0:02:27)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_comment_health.py
17 passed in 26.46s
exit: 0
