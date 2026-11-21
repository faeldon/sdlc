VERDICT: PASS

Both fixes do what the landing note says, and the change's tests pass. I did not run the end-to-end `/sdlc:bug` path. I read `host_specifics()` and `_cut_host()` and ran the upstream tests.

## Notes
- **Medium 1, short and common names:**
  - `add()` now keeps names of two or more characters. The `UPSTREAM_COMMON` skip applies only when the placeholder is in `UPSTREAM_GENERIC`, so a common word that is the host's folder, owner or user is still cut.
  - The safety check treats names shorter than `UPSTREAM_SHORT` as whole words only. `qz` inside `quiz` neither triggers the field being left out nor gets cut.
- **Medium 2, `..` in a relative path:** a relative path is kept as written only when no segment is `..` and it exists under `PLUGIN_DIR`. Any other relative path goes through `_layout()` and becomes `<path>` (or a `.sdlc/` layout path). That covers `scripts/../../secret/notes.txt`.
- **Tests:** `tests/test_upstream.py` passes (18 passed), including the two new tests the builder wrote. The landing round's gate record ran the whole suite, so I did not rerun it.
- **checks.md, "The docs say what filing upstream does":** I read it without running it. It greps for strings in REFERENCE.md, README.md, AGENTS.md and FEATURES.md, which this round's diff does not remove. I expect it to pass.
- **Open Lows:** the dotless ssh alias and the host marker matched anywhere in the body are recorded as open Lows and not fixed here. That matches what the person asked for, so they are not findings.

## Evidence
$ cat .sdlc/work/209-upstream-bugs/build/land-1.md | head -60
(builder's report; its evidence shows the two new tests failing before the fix and the gate green, 3725 passed)
exit: 0

$ tail -5 .sdlc/work/209-upstream-bugs/build/round-*.gate.md
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_upstream.py 2>&1 | tail -4
..................                                                       [100%]
18 passed in 13.49s
exit: 0

$ sed -n 9800,10080p scripts/sdlc.py
(read `host_specifics()`, `_cut_path()` and `_cut_host()`)
exit: 0

$ cat .sdlc/work/209-upstream-bugs/checks.md
(read: one check, the docs greps)
exit: 0
