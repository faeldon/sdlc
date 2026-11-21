I reran every command the report rests on, each now with its exit, so the report below stands with full evidence. The six CI failures on `main` are fixed at their causes and the work is uncommitted. The Linux fix was tested in a Linux container. The Windows fixes were tested on macOS by setting up the same conditions, not on Windows. Only the Windows job on the push that lands this can prove those.

| Failure (job) | Cause | Fix |
|---|---|---|
| Two `UnicodeDecodeError` tests (Windows) | The two tests copied `templates/spec.md` with a plain `write_text`, so its `—` was written as the Windows byte 0x97. The script reads UTF-8 correctly, so there was no script bug. | The tests now name `encoding="utf-8"`. `test_windows.py` now also scans the body of every test marked `portable`, which is why it missed this before. |
| Hand-gate hash (Windows) | **A real bug a Windows host would hit.** Windows runners set `core.autocrlf=true`, so checking the branch out again rewrites files with CRLF. The hash was over the bytes on disk, so it changed. | `_hand_digests()` in `sdlc.py`, and its copy in `factory.py`, now hash each file as git stores it (`git hash-object --stdin-paths`). `docs/REFERENCE.md` updated. |
| Mend test (Windows) | The fake `claude` the test used is a shebang script, which Windows can't run. | The test replaces `factory._claude` inside the test process instead, and stays `portable`. |
| Upstream test (Windows) | Same with the fake `gh`, so the runner's real `gh`, which isn't logged in, answered. | A `_logged_in()` helper stands in for the GitHub tracker's `gh` calls and supplies the login. |
| Port test (Linux) | **Not a race; it fails on every Linux run.** Linux refuses to bind a port held only by a TIME_WAIT left by a server that didn't set `SO_REUSEADDR`; macOS allows it. So a free port read as lost. | `_lost()` now checks `/proc/net/tcp` and `tcp6`: if only TIME_WAIT entries hold the port, it isn't lost. |

I also took in both nits:
- **2026-11-21-21:** `_SCP_RE` now also matches a remote with an undotted host, like `git@localhost:x/y`.
- **2026-11-21-23:** the unverified claim about setup-uv's cache token is gone from the `check.yml` comment.

**Tests added or changed:**
- `test_every_portable_test_names_its_encoding`, with a self-test showing it catches each pattern and skips `os.open`.
- `test_the_build_hash_survives_a_crlf_checkout`, which also checks that `factory.py`'s copy gives the same hash.
- `test_only_time_wait_reads_the_proc_tables`.
- An undotted-host case in the scp-remote test.
- The rewritten mend and upstream tests.

Each new or changed test fails against HEAD's code or tests and passes with this change. For the mend and upstream tests, the failing run uses the old fakes made non-executable, which is what happens on Windows.

**Other files:**
- **`plan.md`:** written before the code, then updated where the build departed: the `os.open` exclusion, the REFERENCE.md edit, and the mend test's red step.
- **`checks.md`:** one check, that the workflow no longer mentions a cache token.
- **`notes.md`:** three unticked items:
  - Have a landing or `status` say when CI on the base branch is red.
  - 275 unencoded `read_text`/`write_text` calls remain in tests Windows doesn't run.
  - Hand-gate records written before this change will read stale once after updating.

- DECISION: [default] Fix the Linux port failure in `factory.py` by reading `/proc/net/tcp`, not only in the test. Going ahead unless told otherwise.
  - OPTION: script fix via `/proc` — a Linux host whose dev server sets no `SO_REUSEADDR` is no longer misread as having lost its port; about 20 lines, Linux only. In one rare case a port also held by another process's bound but not listening socket reads as free.
  - OPTION: test-only fix (the test's listener sets `SO_REUSEADDR`) — smaller, but `_binds()` stays wrong on Linux and its docstring stays false.
  - WHY: the intent's constraint that a script bug a host would hit is fixed in the script.
- DECISION: [default] Hash the hand gate's build with `git hash-object`, so hand-gate records written before this change read stale once. Going ahead unless told otherwise.
  - OPTION: `hash-object` — stable when a checkout only rewrites line endings, on every host; each existing green hand gate needs one `sdlc.py gate` rerun.
  - OPTION: hash the raw bytes with CRLF normalised — keeps the old hashes for LF-only trees, but gets `.gitattributes` eol and clean filters wrong.
  - WHY: the hand gate is meant to hash the build as git stores it.
- DECISION: [default] Widen `test_windows.py` to the body of each portable test only, not to every test and helper. Going ahead unless told otherwise.
  - OPTION: portable tests' bodies only — 6 edits, and it covers what CI's Windows job runs; helpers those tests call aren't scanned.
  - OPTION: every test file — catches helpers too, but means 275 edits to tests Windows never runs.
  - WHY: the intent asks to widen the check to the read it missed, which was in a portable test's body.

- UNTESTABLE: none

## Evidence

$ gh run view 44894639869 --log-failed | grep -o "FAILED tests/[^ ]*"
FAILED tests/test_factory_ui.py::test_a_server_that_answered_and_closed_first_has_not_lost_its_port
FAILED tests/test_factory_agent.py::test_the_builder_s_evidence_is_mended_once_a_round
FAILED tests/test_hand_gate.py::test_the_build_hash_moves_on_a_rebase_onto_a_moved_base
FAILED tests/test_sdlc.py::test_check_leaves_out_the_template_plan_during_a_live_upgraded_build
FAILED tests/test_sdlc.py::test_a_live_first_build_hides_no_other_problem
FAILED tests/test_upstream.py::test_upstream_repo_comes_from_the_manifest
exit: 0

Red, in a scratch copy at /tmp/214-red, holding HEAD's code or tests:

$ uv run --group dev pytest -q -p no:cacheprovider tests/test_hand_gate.py -k crlf   (HEAD's sdlc.py and factory.py)
E       AssertionError: assert 'c10daf2c954037af' == '7bc984ad92451261'
exit: 1

$ uv run --group dev pytest -q -p no:cacheprovider tests/test_upstream.py -k scp_remote   (HEAD's sdlc.py)
E         At index 0 diff: 'cloned git@localhost:<path>' != 'cloned <remote>'
exit: 1

$ uv run --group dev pytest -q -p no:cacheprovider tests/test_factory_ui.py -k proc_tables   (HEAD's factory.py)
E       AttributeError: module 'factory_under_test' has no attribute '_only_time_wait'
1 failed, 18 deselected in 1.26s
exit: 1

$ uv run --group dev pytest -q -p no:cacheprovider tests/test_windows.py -k encoding   (HEAD's test_sdlc.py, test_readiness.py, test_factory_agent.py)
E       AssertionError: test_factory_agent.py: text read or written with no encoding at [661]
exit: 1

$ env PATH=/tmp/214-bin:/usr/bin:/bin uv run --group dev pytest -q -p no:cacheprovider tests/test_factory_agent.py -k evidence_is_mended   (HEAD's test, fakes chmod 644)
E       AssertionError: {'change': '008-reopen-drafts', 'task': 'mend', 'role': 'builder', 'model': 'opus', ...}
exit: 1

$ env PATH=/tmp/214-bin:/usr/bin:/bin uv run --group dev pytest -q -p no:cacheprovider tests/test_upstream.py -k comes_from_the_manifest   (HEAD's test, fakes chmod 644)
E       AssertionError: {'available': False, 'why': "gh isn't installed", 'own_repo': False, 'repo': 'someone/upstream', ...}
exit: 1

$ docker run … ghcr.io/astral-sh/uv:python3.12-bookworm-slim … pytest -q tests/test_factory_ui.py -k "port or proc_tables"   (Linux, HEAD's factory.py)
FAILED tests/test_factory_ui.py::test_a_server_that_answered_and_closed_first_has_not_lost_its_port
FAILED tests/test_factory_ui.py::test_only_time_wait_reads_the_proc_tables - ...
2 failed, 3 passed, 14 deselected in 0.51s
exit: 1

Green, in the worktree:

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
338 files already formatted
exit: 0

$ uv run --group dev pytest -q tests/test_windows.py -k "encoding or unencoded"
75 passed, 34 deselected in 0.57s
exit: 0

$ uv run --group dev pytest -q tests/test_hand_gate.py
54 passed in 17.03s
exit: 0

$ env PATH=/tmp/214-bin:/usr/bin:/bin uv run --group dev pytest -q tests/test_factory_agent.py -k evidence_is_mended
1 passed, 100 deselected in 1.53s
exit: 0

$ env PATH=/tmp/214-bin:/usr/bin:/bin uv run --group dev pytest -q tests/test_upstream.py
18 passed in 6.11s
exit: 0

$ uv run --group dev pytest -q tests/test_factory_ui.py
19 passed in 8.48s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_windows.py tests/test_hand_gate.py tests/test_factory_agent.py tests/test_upstream.py tests/test_factory_ui.py tests/test_sdlc.py tests/test_readiness.py
627 passed in 12.00s
exit: 0

$ uv run --group dev pytest -q -n auto -m portable
1008 passed, 29 skipped in 25.86s
exit: 0

$ docker run … ghcr.io/astral-sh/uv:python3.12-bookworm-slim … pytest -q tests/test_factory_ui.py tests/test_hand_gate.py tests/test_upstream.py tests/test_windows.py tests/test_factory_agent.py   (Linux, this change)
301 passed in 16.58s
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 214
  "passed": true,
  "problems": []
exit: 0

$ uv run --quiet --script scripts/sdlc.py vet --strict
    none ✅
exit: 0
