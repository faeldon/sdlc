Every reply an agent sends back is now cleaned of this machine's paths before it's written to the change's folder, and the home directory is written as `<home>` instead of `~`. The full gate passes: 2407 passed, 13 skipped. Everything is left uncommitted for `/sdlc:ship`.

I wrote a `plan.md` (this is Tier 1, but the change touches more than a couple of files). The build matches it.

**Slices**
1. **The home mark.** `HOME_MARK` is now `<home>` in `factory.py` and in its copy in `sdlc.py`. With `~`, any path under the home directory, including one cut short in output, came out as `~/<dir>/…`, which `test_nothing_local` rejects. `<home>/<dir>/…` matches none of its patterns. Nothing reads the mark itself; the board and `sdlc.py` only read the `VERDICT:`, `CHANGE:` and `GATE:` lines. Updated to match:
   - the two tests that expected `~`: the gate-record test in `tests/test_factory.py` and the `under ~` line in `tests/test_hand_gate.py`;
   - the hand-gate paragraph in `docs/REFERENCE.md`;
   - both functions' docstrings.
2. **Replies.** `cmd_agent` runs the reply through `_placeholders(reply, root)` once, before either write. That one call covers the review, verifier, approver and builder files and the spec draft with its questions (`_file_draft()`). Only paths change, so a `CHANGE:` line keeps naming its file.

**Tests added** (both failed on the old code for the expected reason before the fix)
- `test_a_path_under_home_is_filed_in_a_form_the_scan_accepts`: a path under home but outside the clone, and a cut-short clone path, come out matching none of `test_nothing_local.PATTERNS`.
- `test_every_reply_is_filed_without_this_machine_s_paths`: a fake `claude` reply quotes `git worktree list` (the main checkout and the worktree) and a `which node` path under home. Both the builder's report and the spec draft show `<path-to-clone>` and `<home>`, never the paths, and the planted `- CHANGE:` line comes through unchanged. This is the 131 landing case.

**One edit outside the code:** the gate's scan failed on this change's own `intent.md`. Lines 34–35 quoted the very machine path they describe. I replaced the two quotes with `/Users/<name>/<dir>/s...` and `~/<dir>/…`; the meaning is the same.

**`notes.md`:** nothing left. One thing I didn't change: a spec draft with two or more lines starting with `<path-to-clone>` or `<home>` would read as an unfilled scaffold (`PROMPT_RE`). That risk already existed for `<path-to-clone>`.

- DECISION: [default] Home mark is `<home>` (the intent's first open question). It matches `<path-to-clone>`, and a bare `~` with nothing after it is impossible to guarantee once a path follows. Going ahead with `<home>` unless told otherwise.
- DECISION: [default] Paths only, no check against `.sdlc/terms.local` (second open question). That file is local to the main checkout, and a term found in a reply has no mark to put in its place. Going ahead with paths only unless told otherwise.
- DECISION: [default] The agents' prompts are unchanged (third open question). The script's replacement is the whole fix, because a prompt can't be enforced. Going ahead unless told otherwise.

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k "path_under_home or every_reply_is_filed or records_no_path"
FAILED tests/test_factory.py::test_the_gate_records_no_path_of_this_machine
FAILED tests/test_factory.py::test_a_path_under_home_is_filed_in_a_form_the_scan_accepts
FAILED tests/test_factory.py::test_every_reply_is_filed_without_this_machine_s_paths
3 failed, 276 deselected in 2.71s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py tests/test_hand_gate.py -n auto
314 passed in 12.54s
exit: 0

$ ./check.sh
246 files already formatted
2407 passed, 13 skipped in 152.94s (0:02:32)
✔ Validation passed
✔ Validation passed
exit: 0
