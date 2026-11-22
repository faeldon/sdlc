I've built 225 in `tests/test_ci.py`, the only file it touches. The check now reads a quoted `uses:` value the way YAML does, and the three tests in `tests/test_ci.py` pass. The change is uncommitted, waiting for `/sdlc:ship`. It's Tier 1 and touches one file, so there's no `plan.md`.

**What I built (one slice):**
- **Test first:** I added five quoted lines to `test_the_check_refuses_a_tag_or_branch_pin`:
  - a SHA pin in double quotes with `# v4.4.0`, which should pass;
  - the same in single quotes, which should pass;
  - a tag in double quotes (`"actions/checkout@v4"`), which should be refused;
  - a branch in single quotes (`'actions/checkout@main'`), which should be refused;
  - a SHA with mismatched quotes (`"…'`), which should be refused.

  The test failed for the reason expected: the two correctly quoted SHA pins were reported as unpinned.
- **Fix:** a new `QUOTED` pattern strips one matching pair of `"` or `'` from the value before `PINNED` checks it. The local-action skip (`./`) now looks at the unquoted value too.
- **Docstring:** `unpinned()` now explains why the version comment must be `# v<digits>`: Dependabot rewrites a comment in that form when it bumps the pin, and a looser one would be left behind and stop matching the SHA. `VERSION` itself is unchanged.
- **Tests:** the five new lines prove that a quoted SHA pin passes and that a tag or branch is still refused, quoted or not. The other two tests are unchanged and still pass, so the repo's own workflows are still all pinned. The module is still marked `portable`.

The `.yaml` glob nit was already handled by `workflow_files()`. All five nits (2026-11-22-6 to -10) are listed in the intent's "Nits taken in" line, so ship retires them. Nothing went into `notes.md`.

- DECISION: [default] Don't read flow-mapping `uses:` (`- { uses: a/b@v4 }`), the intent's open question. Going ahead without it unless told otherwise.
  - OPTION: leave it out — no workflow here uses that form and the check stays simple; a pin written that way would not be checked at all
  - OPTION: read it too — covers every form; adds a pattern for a form nobody writes here
  - WHY: no workflow in this repo uses that form, and the intent's Approach doesn't include it

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_ci.py   (before the fix)
FAILED tests/test_ci.py::test_the_check_refuses_a_tag_or_branch_pin - assert ...
1 failed, 2 passed in 0.24s
exit: 1

$ uv run --group dev pytest -q tests/test_ci.py
3 passed in 10.59s
exit: 0

$ uv run --group dev ruff check tests/test_ci.py && uv run --group dev ruff format --check tests/test_ci.py
All checks passed!
1 file already formatted
exit: 0

$ git diff --stat && uv run --group dev pytest -q -m portable tests/test_ci.py
 tests/test_ci.py | 24 ++++++++++++++++++++----
 1 file changed, 20 insertions(+), 4 deletions(-)
3 passed in 0.01s
exit: 0
