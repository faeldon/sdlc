VERDICT: PASS

The end-to-end path holds: every `--help` output for `sdlc.py` and `factory.py` is byte-identical before and after the move. The gate record is green.

## Notes
- `checks.md` does not exist for this change, so there are no acceptance checks to read.
- Spec R7 is the end-to-end path. I ran `--help` on the merge-base copy and on this build for `sdlc.py` (bare, `close`, `publish`, `release`, `new`, `inbox-commit`) and `factory.py` (bare, `land`, `land-check`, `train`, `resolve`, `land-verdicts`). All 12 are identical.
- The gate record (`build/round-1.gate.md`) says `GATE: PASS` with `./check.sh` at exit 0, so I did not run the full suite.
- `scripts/closing.py` and `plugins/factory/scripts/landing.py` both exist.
- The pytest filter matched one test, which passed: `landing_code_is_reviewed`.
- I did not confirm that `[review] sensitive` lists both new modules. My `grep -A4` showed only the first four entries of the list.
- I did not run the close handoff or a train landing. Those are R11's and the spec's first real exercise of the move, and they only happen at close.
- `decisions.md` has D1 and D2, both builder defaults awaiting the person. Neither is a failure.

## Evidence
$ cat .sdlc/work/153-risky-code-in-its-own-modules/build/round-1.gate.md | head -8
GATE: PASS
## Attempt 1
Verdict: PASS
Command: ./check.sh
Build: d4d9e693d41083d1
Exit: 0
exit: 0

$ git merge-base HEAD main
8af76668c846d104ea25b059494f2b9446626a9b
exit: 0

$ (scratch archive of the base) for each command: compare `sdlc.py <c> --help` and `factory.py <c> --help` on base vs this build
same sdlc (bare), close, publish, release, new, inbox-commit
same factory (bare), land, land-check, train, resolve, land-verdicts
ls: scripts/closing.py, plugins/factory/scripts/landing.py
30:sensitive = [
31-  ".claude-plugin/",
32-  ".claude/settings.json",
33-  "scripts/trackers/",
34-  "check.sh",
.                                                                        [100%]
1 passed, 358 deselected in 8.62s
exit: 0
