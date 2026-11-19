VERDICT: PASS

The change does what its intent says. The gate record is green. The two new unreachable-index tests pass, and so does the drawer browser test (2 passed, 12.84s).

## Notes
- **Check "The drawer test bounds only a hang, never a poll's speed":** I expect it to pass. `page.set_default_timeout(PATIENT)` appears once in `tests/test_board_browser.py`, and `timeout=` appears nowhere in it. I read the check's two conditions with grep counts rather than running its command.
- **Adoption tests:** `_uv` retries with `--offline` only when uv's own "unreachable index" error shows up. It skips, naming the network, only when the offline retry also fails. With the network up the behaviour is unchanged, so a missing dependency still fails. `test_with_the_index_unreachable_a_copy_of_the_script_runs_from_uvs_cache` covers the warm-cache path, and `test_with_the_index_unreachable_and_nothing_cached_the_test_skips_naming_the_network` covers the skip path.
- **Intent's open question:** the drawer flake is a timing wait, not a focus race. The old step used a 10-second timeout, and the change replaces it with a 120-second hang bound.
- **Not run:** a loaded-gate scenario (`pytest -n auto` beside other gates). A load flake can't be reproduced in this run.

## Evidence
$ cat .sdlc/work/186-gate-reliability/build/round-1.gate.md | head -12
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
Seconds: 156.3
Tree: unchanged
exit: 0

$ uv run --group dev pytest -q -rs tests/test_adoption.py -k "index_unreachable" tests/test_board_browser.py
2 passed, 13 deselected in 0.58s
exit: 0

$ uv run --group dev pytest -q -rs tests/test_board_browser.py
2 passed in 12.84s
exit: 0

$ grep -c 'timeout=' tests/test_board_browser.py; grep -c 'page.set_default_timeout(PATIENT)' tests/test_board_browser.py
0
1
exit: 0
