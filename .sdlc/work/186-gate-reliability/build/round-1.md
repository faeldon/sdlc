I've fixed both gate failures from 181, test files only, and left them uncommitted. One result is unproven, though: the new cached-run test passed before my fix, because it only fails once uv's cached index answers are stale (about 10 minutes).

**Change 186: the gate fails only on the code (Tier 1, no `plan.md`: it touches two test files)**

**Slice 1: adoption tests with no network** (`tests/test_adoption.py`)
- The three places that ran `uv run --script` now share one runner, `_uv()`. When uv says it couldn't reach the package index, the script never ran. The runner then runs it once more with `--offline`, from uv's cache.
- If the cache doesn't hold the packages either, the test skips. `pytest -rs` shows: `no network: the package index can't be reached (error: Failed to fetch: …), and uv's cache lacks the script's dependencies`.
- `_by()` gained an `env=` argument so a test can cut the network.
- Two new tests:
  - `test_with_the_index_unreachable_a_copy_of_the_script_runs_from_uvs_cache`: proves a copy of the script still runs from the cache with every request refused. This is the one that only fails on a stale cache. I saw that failure by hand earlier: a fresh copy behind a dead proxy exited 2 with `Failed to fetch`. No uv setting forces staleness, and `--refresh` can't be combined with `--offline`.
  - `test_with_the_index_unreachable_and_nothing_cached_the_test_skips_naming_the_network`: proves the skip and its reason. It failed before the fix (`DID NOT RAISE Skipped`) and passes after.
- I also checked the whole outcome by hand:
  - **No network, empty cache:** the network-dependent tests skip with that reason (1 passed, 12 skipped).
  - **No network, warm cache:** all 13 pass.
  - **Network up, undeclared dependency:** a copy that imports a package it doesn't declare still fails (`ModuleNotFoundError`, exit 1), so the constraint holds.

**Slice 2: the drawer focus test** (`tests/test_board_browser.py`)
- I couldn't make it fail under load: 60 of 60 runs passed across 18 workers, and 60 of 60 again under 54 CPU hogs.
- The board sets focus synchronously inside each event handler. The only time limits in the test were the 10-second wait for a poll to rebuild the cards and Playwright's 30-second defaults. 181's failing gate ran 537s against a normal 158s, which fits a long stall.
- I reproduced the failure with a throwaway test that holds every poll after the first for 11 seconds. It failed with `Page.wait_for_function: Timeout 10000ms exceeded`.
- The fix: the page now uses one limit of 120 seconds (`PATIENT`) everywhere, and the 10-second wait is gone. The throwaway test passes with it and is deleted. Keeping it would add about 15 seconds to every gate, so `checks.md` checks the limit instead.
- Answer to the intent's open question: it was a time limit, not a focus race in the board.

**`checks.md`:** one check, "The drawer test bounds only a hang, never a poll's speed". It exits 0 now and fails on the old code.

**`notes.md`:** one unticked line. `tests/test_train.py` also runs a copy of the plugin through `uv run --script`, so a gate with no network can fail it the same way; it could share `_uv()`.

- DECISION: [default] Should the drawer test wait up to 120s for the page instead of 10s for a poll and 30s for everything else? Going ahead with 120s unless told otherwise.
  - OPTION: 120s on every page step — no load or stall a gate meets should hit it; a truly broken board costs two minutes before it fails
  - OPTION: no limit at all — never fails on time; a broken board hangs the gate with no output
  - OPTION: keep 10s and make the test trigger the poll itself — shorter; still fails when a poll is slow, which is the failure we saw
  - WHY: the intent asks the test to wait on the state, not on time; a long bound only stops a hang

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_adoption.py -k unreachable   (before the fix)
E       Failed: DID NOT RAISE Skipped
1 failed, 1 passed, 11 deselected in 3.14s
exit: 1

$ uv run --group dev pytest -q -rs tests/test_adoption.py -k unreachable   (after the fix)
2 passed, 11 deselected in 2.82s
exit: 0

$ HTTPS_PROXY=… HTTP_PROXY=… ALL_PROXY=http://127.0.0.1:9 (and lowercase) NO_PROXY= UV_HTTP_RETRIES=0 UV_CACHE_DIR=$(mktemp -d) .venv/bin/pytest -q -rs tests/test_adoption.py
SKIPPED [12] tests/test_adoption.py:65: no network: the package index can't be reached (error: Failed to fetch: https://pypi.org/simple/python-frontmatter/), and uv's cache lacks the script's dependencies
1 passed, 12 skipped in 0.89s
exit: 0

$ (same proxies) uv run --offline --group dev pytest -q -rs tests/test_adoption.py
13 passed in 21.39s
exit: 0

$ .venv/bin/python /tmp/missing186.py   (a plugin copy whose sdlc.py imports undeclared tomli_w, run through _uv with the network up)
exit 1 ModuleNotFoundError: No module named 'tomli_w'
exit: 0

$ uv run --group dev pytest -q -n 18 tests/test_zz_flake_scratch.py   (60 drawer runs, then again beside 54 CPU hogs; scratch file since deleted)
60 passed in 28.94s
60 passed in 36.85s
exit: 0

$ uv run --group dev pytest -q tests/test_zz_flake_scratch.py   (polls held 11s; before the fix)
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 10000ms exceeded.
1 failed in 15.53s
exit: 1

$ uv run --group dev pytest -q tests/test_zz_flake_scratch.py tests/test_board_browser.py   (after the fix)
3 passed in 19.16s
exit: 0

$ sh -c "<checks.md's sh block>"
exit: 0

$ uv run --group dev pytest -q -rs tests/test_adoption.py tests/test_board_browser.py tests/test_nothing_local.py
23 passed in 33.42s
exit: 0

$ uv run --quiet --group dev ruff check tests/
All checks passed!
exit: 0

$ uv run --quiet --group dev ruff format --check tests/
95 files already formatted
exit: 0
