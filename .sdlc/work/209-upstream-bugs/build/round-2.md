Round 1's kept change and the nit are both fixed, each with a test I first saw fail for the reported reason. The full gate passes (3695 passed, 29 skipped), and everything is still uncommitted.

- **KEPT C1 (paths after `:` and scp remotes reached the body):** fixed in `scripts/sdlc.py`.
  - `_PATH_RE`'s lookbehinds no longer skip a path that follows a `:`. URLs are replaced before the path pass runs, so `https://` pieces are unaffected.
  - A new `_SCP_RE` turns any `user@host:path` into `<remote>`, whether or not it is one of the repo's configured remotes.
  - New test: `test_upstream_cut_places_a_path_after_a_colon_and_an_scp_remote`. `host:/srv/drafts/x/y` now becomes `host:<path>`, and `git@example.test:me/secret.git` becomes `<remote>`. The same test checks that a URL, `/sdlc:close` and a Windows path are still handled as before.
- **Nit (`@name` would notify GitHub users):** in the three prose sections and the exit line, an `@name` is now put in backticks, which GitHub doesn't treat as a mention. Emails are left alone. The command and output are already in code blocks, where GitHub never notifies anyone. New test: `test_upstream_body_pings_no_one`.
- **Gate failure on the way:** the first full run failed `test_nothing_local`, because my new test path looked like a home directory. I changed it to `/srv/drafts/...`.
- **`plan.md`:** the "As built" section now has a line for each fix.
- **`notes.md`:** nothing new.

No new decisions this round; the four defaults from round 1 are still open.

## Evidence

$ uv run --group dev pytest -q tests/test_upstream.py -k "colon or pings"   (before the fix)
2 failed, 14 deselected in 1.65s
exit: 1

$ uv run --group dev pytest -q tests/test_upstream.py tests/test_archive.py::test_intake_flags_an_issue_from_a_host
17 passed in 7.39s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 209   (first run)
1 failed, 3694 passed, 29 skipped in 232.78s
FAILED tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden
exit: 1

$ uv run --group dev pytest -q tests/test_nothing_local.py tests/test_upstream.py
24 passed in 11.51s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 209
All checks passed!
344 files already formatted
3695 passed, 29 skipped in 267.70s (0:04:27)
✔ Validation passed
✔ Validation passed
exit: 0
