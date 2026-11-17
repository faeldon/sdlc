VERDICT: PASS

- PREEXISTING: scripts/factory.py (`gate` record): `.sdlc/work/082-parallel-gate/build/round-1.gate.md:104` and three more lines hold home-directory paths. They come from `claude plugin validate`'s output, which `factory.py gate` copies into the record. `test_nothing_in_the_repo_is_forbidden` reads that untracked, unignored file, so it fails now. Any later gate run in this worktree, ship's Step 1 included, will be red until the record is redacted or the scan skips it. Under `-n auto`, xdist's worker line adds more paths to a failing run's record, which notes.md already flags. The scan change itself behaves as specified. The cause is the gate record's contents, not this change's code.

## Notes

- **Spec path:** `./check.sh` should run in parallel and pass from the main checkout with `.sdlc/reports/` present. I did not rerun the full gate, since the script's own gate record already covers it. The record says PASS, though its Attempt 1 is a FAIL, a red gate that a later attempt overwrote. I ran only the scan tests.
- **Scan tests:** `pytest -n auto tests/test_nothing_local.py` gave 7 passed, 1 failed. The failure is the preexisting item above, which is only the gate record.
- **notes.md:** it reports 1849 tests passing under `-n auto` in 43 s, against 231 s serial. It also lists two unticked items, the `_free_port` race and the gate record carrying home paths, so ship will have to give each a disposition.
- **checks.md, "The gate runs pytest across the machine's cores":** I expect it to pass. I read the grep without running it, though I ran an identical grep on `check.sh` and it matched the line `uv run --quiet --group dev pytest -q -n auto`.
- **checks.md, "pytest-xdist is a locked test dependency, not a script one":** I expect it to pass. `pyproject.toml` has `"pytest-xdist>=3",`, `uv.lock` has the package entry, and `scripts/sdlc.py` has no mention of xdist.
- **checks.md, "CI's Linux job runs in parallel and the Windows job's run is unchanged":** I expect it to pass. `check.yml` has `pytest -q -n auto` and `pytest -q -m portable`.
- **Not run:** the full suite and `check.sh`, per the rules above.

## Evidence

$ cat build/round-1.gate.md (head and tail)
GATE: PASS
## Attempt 1
Verdict: FAIL
...
✔ Validation passed
exit: 0

$ grep -q '^uv run --quiet --group dev pytest -q -n auto$' check.sh; echo $?
0
exit: 0

$ grep -q '"pytest-xdist>=3",' pyproject.toml && grep -q '^name = "pytest-xdist"$' uv.lock && ! grep -q xdist scripts/sdlc.py; echo $?
0
exit: 0

$ grep -q 'run: uv run --group dev pytest -q -n auto$' .github/workflows/check.yml && grep -q 'run: uv run --group dev pytest -q -m portable$' .github/workflows/check.yml; echo $?
0
exit: 0

$ uv run --quiet --group dev pytest -q -n auto tests/test_nothing_local.py
FAILED tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden
1 failed, 7 passed in 12.43s
exit: 1 (the `exit 0` shown in the raw output is `tail`'s status)

$ uv run --quiet --group dev pytest -q tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden
E  '.sdlc/work/082-parallel-gate/build/round-1.gate.md:104: Validating marketplace manifest: <path-to-clone>/.claude/worktrees/082-parallel-gate/.claude-plugin/marketplace.json'
exit: 1 (taken from the failing assertion shown)
