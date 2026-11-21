VERDICT: PASS

No Critical or Required findings. All six CI failures are fixed at their cause, and each fix has a test.

## Notes
- NIT: scripts/sdlc.py:3076: `_hand_digests` runs `git hash-object` once per call and ignores its stderr. If it fails, the fallback silently hashes raw bytes, so a git failure could make a record read stale only on the next run. That is safe, but a one-line comment saying so would help. {docs S low}
- NIT: tests/test_windows.py:~300: `_unencoded` skips an `open` whose mode is not a constant, so it counts that call as `"r"`. That is acceptable for now. A dynamic mode could be flagged instead. {robustness S low}

**Done well:**
- The Windows `UnicodeDecodeError` was a test bug (the fixtures wrote with the default encoding), and the change fixes it there. The check now scans the bodies of portable tests, and its self-test pins each pattern, including the `os.open` exclusion.
- The hand-gate hash was a real script bug on hosts with `core.autocrlf`. The fix is in both `sdlc.py` and `factory.py`, and the new test asserts the two copies agree. `docs/REFERENCE.md` is updated.
- The Linux port failure was a real `_binds` bug, not a race. The `/proc/net/tcp` fix is tested through injectable tables, so the test also runs on Windows and macOS.
- The `check.yml` change only trims a comment, and the other nit was taken in with a test.

**Ran:** nothing myself. `build/round-1.gate.md` records `GATE: PASS` (`./check.sh`, exit 0).

**Unsettled:** the Windows fixes were not run on Windows, which the builder also says. Only CI on the landing push will show them passing there.
