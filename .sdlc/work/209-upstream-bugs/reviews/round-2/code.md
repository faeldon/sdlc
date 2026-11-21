VERDICT: PASS

The one change kept last round is now done. `_PATH_RE`'s `abs` lookbehind no longer excludes a `:`, and a new `_SCP_RE` catches `user@host:path` remotes. I ran the real `_cut_host()` on these inputs:

- `file:/Users/<name>/secret/a.txt` gives `file:<path>`.
- `host:/home/<name>/y` gives `host:<path>`.
- `a:b/c` gives `a:<path>`.
- `git@github.com:acme/private.git` gives `<remote>`.
- `x@h.com:/srv/r.git` gives `<remote>`.
- `see /sdlc:close ok` is left alone, as it should be.

`tests/test_upstream.py::test_upstream_cut_places_a_path_after_a_colon_and_an_scp_remote` covers the same cases. The round-2 gate record (`build/round-2.gate.md`) is PASS.

## Notes
- Done well: `_cut_host()` holds URLs first, then scp remotes, then paths, with private-use placeholders so a later pass can't match inside an earlier one's output. Its final safety check reads around the placeholders.
- Ran: a throwaway script under `/tmp` that called `_cut_host()` on the inputs above. I did not run the pytest test or the gate; I relied on the gate record.
