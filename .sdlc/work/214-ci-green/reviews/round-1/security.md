VERDICT: PASS

## Notes

This change opens no exploitable hole. No Critical, High or Medium findings.

**Trust boundaries the diff touches:**
- **Hand-gate build hash** (`scripts/sdlc.py:3076`, its copy in `plugins/factory/scripts/factory.py:3073`).
  - The paths come from git's own list of changed paths, and they go to `git hash-object --stdin-paths` on stdin. None is an argument, so a path starting with `-` can't act as a flag. A path holding a newline or CR falls back to sha256, so it can't split into two entries.
  - Without `-w` the command writes no object.
  - Any clean filter it runs needs a driver set in git config, not in the tree. `git status` and `git add` would run the same filter, so this adds no new way to run code.
  - Tampering: could a branch pass an old green record with changed content? Only through an edit that git's eol handling normalises away, which is a line-ending-only difference and the point of the change. `.gitattributes` is itself a changed path and is hashed too, so changing it moves the hash.
  - Symlinks are followed, as `read_bytes()` followed them before, so nothing changed there.
  - D2/D4: old records go stale once. That fails closed: a rerun is needed, nothing is trusted that shouldn't be.
- **`_only_time_wait()`** (`factory.py:5873`):
  - It reads `/proc/net/tcp*`, which is kernel state, not input anyone else controls. Parsing is defensive: a short line is skipped and a missing table returns False.
  - It only narrows `_lost()`, so the worst case is one server restart that doesn't happen, not an escalation.
  - D1's edge case (a TIME_WAIT plus a bound, non-listening socket reads as free) is a liveness quirk, not a security issue.
- **`_SCP_RE` widening** (`sdlc.py:9845`):
  - It redacts more of what an upstream bug report would publish, such as `git@localhost:x/y`. That is a gain for the "nothing local in public text" rule.
  - No catastrophic backtracking: the regex's two host parts can't match the same text, because `\.` separates them.
- **CI workflow** (`[review] sensitive`): only the comment changed. `permissions: contents: read` and the action pins (`actions/checkout@v4`, `astral-sh/setup-uv@v6`) are as they were. No new secret, token scope or trigger.
- **Tests**:
  - `test_upstream.py` replaces the machine's `gh` login with a stand-in that returns the fake token `gho_x`. No real credential is in a fixture, and the test no longer depends on the runner's login, which also keeps a real token out of the test's reach.
  - Fixture writes pass `newline="\n"`.

**Secrets and dependencies:** no secret anywhere in the diff or the change folder's artifacts, and no new dependency.

**Checked:**
- The full non-test diff and the test diffs for `test_upstream.py`, `test_factory_ui.py` and `test_hand_gate.py`.
- Where `_SCP_RE` is used (it feeds the upstream redaction).
- The workflow's `uses:` and permissions lines.
- The round-1 gate record (validation passed).
- `decisions.md` D1–D4: all security-neutral or fail-closed, and none needs a security decision.

I ran nothing beyond read-only `git diff`/`grep`.

- NIT: plugins/factory/scripts/factory.py:3073: `_hand_digests` is now a 15-line copy of `sdlc.py`'s, kept the same by hand. Pin the two bodies equal in `tests/test_hand_gate.py`, as the repo's other copies are pinned, so a fix to one can't skip the other {tests S med}
