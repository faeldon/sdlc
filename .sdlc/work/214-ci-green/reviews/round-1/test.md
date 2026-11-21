VERDICT: PASS

The change is covered. Each failure in the plan's cause table has a test that fails without its fix, and I found no test that can't fail.

## Notes

- **Gate:** `build/round-1.gate.md` shows `3848 passed, 29 skipped`. I did not rerun the suite. I ran three named groups in the foreground: `tests/test_windows.py`, `test_the_build_hash_survives_a_crlf_checkout` and `test_only_time_wait_reads_the_proc_tables`. Together they gave `111 passed`.
- **Encoding:** `test_every_portable_test_names_its_encoding` is parametrized over every test file, so it can fail. `test_an_unencoded_read_in_a_portable_test_is_caught` pins each shape it catches. It covers the `os.open` pass-over, a binary `open`, a positional encoding and a module-level `pytestmark`.
- **Hand-gate hash:** the CRLF test sets `core.autocrlf=true` and asserts the checkout really wrote `\r\n`. It checks the hash is unchanged in both the `sdlc` and `factory` copies, and that a real edit still moves it. It reproduces on macOS, so it can fail.
- **Mend test:** the `_claude` stand-in needs no shebang binary, so it runs on Windows. It asserts one call with `--resume s-b`, which shows the second mend is refused rather than skipped.
- **Upstream:** `_logged_in()` replaces the shebang `gh` fixture. The new undotted host case, `git@localhost:x/y`, covers the `_SCP_RE` nit.
- **Port:** `test_only_time_wait_reads_the_proc_tables` covers TIME_WAIT alone, an IPv4 listener, an IPv6 listener, no entry and no table.
- **`checks.md`:** the one check is `! grep -q "cache token" .github/workflows/check.yml`.
  - I did not run it, as instructed.
  - It fails only if the claim is put back, and it changes no files.
  - I expect it to pass on the current tree.
- NIT: tests/test_factory_ui.py:474: `_lost()`'s new `and not _only_time_wait(port)` branch is proved only by the existing socket test, which exercises it on Linux only. No test combines a refused bind with a stubbed table; the container run is the only proof. {tests S low}
- NIT: tests/test_hand_gate.py:145: the `_hand_digests()` fallback is untested. It hashes a path holding a newline with sha256, and covers a failed `hash-object`. {tests S low}
