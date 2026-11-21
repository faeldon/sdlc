VERDICT: PASS

The kept change was made. `_PATH_RE` now places a path after a `:`, and a new `_SCP_RE` cuts `user@host:path` remotes. `test_upstream_cut_places_a_path_after_a_colon_and_an_scp_remote` pins both:
- `host:/srv/drafts/x/y` becomes `host:<path>`.
- `git@example.test:me/secret.git` becomes `<remote>`.
- `/sdlc:close` is left alone.
- A Windows drive path is cut.
- A URL is cut.

Without the new patterns, the first two assertions would fail.

## Notes

- Gate record `build/round-2.gate.md`: GATE: PASS, `3695 passed, 29 skipped`. I did not run the whole suite.
- I ran `uv run --group dev pytest tests/test_upstream.py -q -n0` in the foreground: 16 passed.
- Checks in `checks.md`: one section, "The docs say what filing upstream does". It is a set of `grep -q` calls on the R15 doc lines. I expect it to pass on the change and fail on a revert, and it leaves the tree unchanged. I did not run it.
- NIT: tests/test_upstream.py:417: `_SCP_RE` only matches a dotted host, so `git@localhost:x/y` is not cut, and no test names that boundary {robustness S low}
