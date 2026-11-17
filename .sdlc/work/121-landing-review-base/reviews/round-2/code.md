VERDICT: PASS

The kept finding is fixed. `_land_diff()` returns None when `git merge-base` finds nothing, and both `land-review` and `land-verify` return `_NO_FORK` in that case. The tip is never named in a prompt, and the refusal is a string, which `_land_task`'s callers already treat as a stop.

## Notes

- Checked the rework against the settled points only. The fallback `or base` is gone. `_git()` returns None on a failed command, so the no-fork path reaches the refusal. The mend path at line 2450 passes a refusal string through unchanged, so a no-fork state can't be turned into a prompt there either.
- The refusal text matches the wording you gave: `no fork point between <base> and HEAD: the landing can't be reviewed`.
- `test_a_landing_review_with_no_fork_point_is_refused` covers both tasks and asserts on the refusal string. Under the old `or base` fallback it would fail, because a prompt naming the tip would come back instead.
- `test_a_landing_review_reads_the_change_from_its_rounds_own_base` still checks the moved-base case, including that `land-close` reports `moved`.
- Nit: the `_land_diff()` docstring runs to four lines of rationale. The code is clear without them, so consider trimming it to the first two sentences.

## Tests and checks run

- `uv run --group dev pytest tests/test_land.py -q -n auto`: 51 passed.
- The two new tests run on their own: 2 passed.
- `ruff check` on `factory.py` and `test_land.py`: passed. `ruff format --check`: both files already formatted.
- Not run: the full `./check.sh` gate and the rest of the suite (for example `test_skills.py` and `test_windows.py`). The change touches only the factory script and its tests, so I did not expect them to be affected, but I haven't confirmed it.
