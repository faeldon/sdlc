VERDICT: PASS

The rebased diff covers all 14 requirements. I found nothing Critical or Required. I did not run any tests; the builder's `land-1.md` reports a green `./check.sh` (2156 passed, 9 skipped). My review is from reading the diff.

## Notes

- **Light depth (R1–R8):** `light_reviewers()` is a single function, and it returns the host's own list unchanged when `[light] reviewers` was set. `depth()` subtracts the tier-aware list in its `beyond` check, so a Tier 2's own `test.md` can't make the run full in round 2 (R6). `_rounds_at_depth()` reads the tier once for `loop_state`, `carry` and `land-verdicts`. `start` reports `light.reviewers` for the change's tier.
- **`chosen` and decision D2:** A host list naming no known reviewer counts as unset, so `chosen` stays false. That matches D2's answer.
- **Fixture key (R9–R11):** `_inside()` rejects non-strings, absolute paths, drive anchors and `..`, including Windows-style paths. The `{fixture}`-without-`fixture` warning is in place. `shots()` copies the fixture fresh before the server starts. If the fixture is missing, it records a problem and starts no server, so the existing "never runs blind" refusal applies.
- **`serve.sh` and `build.sh` (R12):** Both are consistent with each other. `build.sh` writes `drafts/` inside the copy, and its glob `[0-9]*-*/` doesn't match that folder, so a rerun can't re-ingest it.
- **Landing conflicts:** Per `land-1.md`, the builder kept both sides' register removals and restored entry 66's `Raised` line. The conflicts were only in `inbox.md` and `tests/test_board.py`.
- **Process-file edits:** `land-accept.md` and `runs/reviewer-code.sessions` are modified, and `land-1.gate.md` and `runs/land-resolved` are untracked. These are factory process files, not part of the code change.

Nits:
- `factory.py`: the `_fixture_copy` chmod pass walks the whole copy with `rglob("*")` before each removal. That is fine for a small fixture, but it would add up if a host's fixture were large.
- `factory.py`: `proc = None if problem else subprocess.Popen(...)` inside a `# fmt: skip` block is dense. An early `if problem` branch would read better.

Done well: each spec requirement has a named test that fails without the code, and the plugin copies the fixture without learning anything about what the host serves, so a new `[ui]` key keeps today's behaviour when unset.
