DECISION: READY

**Why:** All six CI failures are fixed at their cause, and each has a test that fails without its fix. All four round-1 reviewers returned PASS, and the gate (`./check.sh`) is green. No Critical or High finding is open. The Windows fixes could not be run here, so CI on the landing push is the only proof for them.

**Open items:**
- None blocking.
- NIT (security reviewer): the `_hand_digests` copy in `factory.py` is not pinned equal to the one in `sdlc.py`. The code reviewer says the new CRLF test already asserts the two copies agree on the hash.
- NIT (code reviewer): a comment in `_hand_digests` should say the fallback to hashing raw bytes is safe.
- NIT (code reviewer): `_unencoded` treats an `open` with a non-constant mode as `"r"`.
- NIT (test reviewer): the `_lost()` branch and the `_hand_digests` fallback are covered only indirectly or not at all.

**Decisions to confirm:**
- SETTLED: D1: The intent's Constraints require a script bug a host would hit to be fixed in the script. The code reviewer confirms `_binds()` was a real bug, not a race, and the test reviewer confirms `test_only_time_wait_reads_the_proc_tables` covers it. The security reviewer notes the fix only narrows `_lost()`.
- SETTLED: D2: The intent fixes script bugs in the script. The code reviewer confirms the hash was a real bug on hosts with `core.autocrlf`, and the security reviewer says old records going stale once fails closed. `docs/REFERENCE.md` is updated, and the CRLF test pins it.
- SETTLED: D3: The intent asks only to widen the check to the read it missed, which was in a portable test's body. The test reviewer confirms `test_every_portable_test_names_its_encoding` covers every test file's portable tests. The 275 non-portable calls are carried forward in `notes.md`.
- SETTLED: D4: This is the same decision as D2, worded twice, and it is settled for the same reasons.

**For the person at ship:**
- `scripts/sdlc.py` `_hand_digests` (about line 3076) and its copy in `plugins/factory/scripts/factory.py` (about line 3073).
- `factory.py` `_only_time_wait()` and `_lost()`.
- The `test_windows.py` widening.
- The `_SCP_RE` widening in `sdlc.py`.
- The `check.yml` change only removes a comment. It is a sensitive path, but the permissions, pins and triggers are unchanged.
- After the push, confirm both CI jobs pass with `gh run list --branch main`.
- No published interface needing approval is touched.

- IMPACT: patch — Windows and Linux failures are fixed, and a hand-gate record written before this change reads stale once and needs one `sdlc.py gate` rerun.

**Undone items:**
- UNDONE: Say when CI on the base branch is red, in a landing's look or in `status`, so the local gate isn't the only word (the intent's third open question; a seed of its own). → seed: Show a red CI on the base branch in the landing's look and in status
- UNDONE: 275 `read_text`/`write_text` calls in non-portable tests and helpers name no encoding. They don't run on Windows today; a test moved into `portable` gets caught by the new check, but a helper it calls doesn't. → seed: Scan the helpers portable tests call for unencoded reads and writes
- UNDONE: A hand-gate record written before this change names a build hashed the old way, so a green hand gate reads stale once after the update and wants `sdlc.py gate` rerun. Worth a line in the release notes. → dropped: `docs/REFERENCE.md` already says so, and the release's changelog is drawn from the change's impact.
