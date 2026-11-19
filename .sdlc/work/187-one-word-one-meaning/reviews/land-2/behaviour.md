VERDICT: PASS

The change does what the intent says. `sdlc.py vet --strict` runs and reports 0 problems, and `sdlc.py check` is refused by argparse. The arbiter's agent and prompts sit under its name. The board's tracks and labels read `arbitrate` and `acceptance`.

I found no stray `sdlc.py check` or "verifier" left in the tree. The ones that remain are deliberate: REFERENCE.md's release note for hosts, the `RENAMED` maps in `factory.py` and `factory_records.py` that read old records, and one old retro table.

- PREEXISTING: tests/test_archive.py:2642: four `test_close_output_is_unchanged` cases (shipped, dropped, rerun, pushed) fail here. They also fail on a plain extract of the base commit `1829d95`, so this change did not cause them. It is the failure recorded in `build/land-1.gate.md`; the `gh` fixture looks like the cause (that record shows a real `gh` scope error), but I did not confirm it.

## Notes
- `build/round-1.gate.md` is `GATE: PASS` (`./check.sh`, exit 0). `build/land-1.gate.md` is `GATE: FAIL` with the four tests above, the same ones that fail on the base. There is no gate record for landing round 2, so I could not check that round's full suite.
- checks.md, "The two test nits are gone": I expect it to pass. `grep` finds neither `179 R1` in `tests/test_metrics.py` nor `# 183` in `tests/test_skills.py`.
- checks.md, "The arbiter's agent and prompts sit under its name": I expect it to pass. `arbiter.md`, `arbitrate.md` and `land-arbitrate.md` exist, and the old `verifier.md`, `verify.md` and `land-verify.md` are gone. `build/land-accept.md` also records exit 0 for it.
- checks.md, "The release says what a host must change": I expect it to pass. `intent.md` has `impact: minor`, and REFERENCE.md carries the `check`→`vet` note, the `vet --strict` instead line, the `[models] arbiter` line and "setup proposes it on its next run". `land-accept.md` records exit 0 for it.
- I did not run the board in a browser. I confirmed its renamed tracks and labels by reading the diff of `scripts/board.py`.

## Evidence
$ head -12 .sdlc/work/187-one-word-one-meaning/build/round-1.gate.md
GATE: PASS … Command: ./check.sh … Exit: 0
exit: 0

$ uv run --quiet --script scripts/sdlc.py vet --strict
■ Problems: 0 / none ✅
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
sdlc.py: error: argument cmd: invalid choice: 'check' (choose from status, new, vet, ship, …)
exit: 2

$ ls plugins/factory/agents plugins/factory/prompts
agents/arbiter.md and prompts/arbitrate.md, land-arbitrate.md present; no verifier.md, verify.md or land-verify.md
exit: 0

$ git grep -niE "sdlc\.py check|verifier" -- . ':!.sdlc/work'
Only REFERENCE.md's release note, the `RENAMED` maps in `factory.py` and `factory_records.py`, comments in `board.py`, and an old retro table.
exit: 0

$ cat .sdlc/work/187-one-word-one-meaning/build/land-1.gate.md
GATE: FAIL … 4 failed, 3433 passed, 29 skipped (the four `test_close_output_is_unchanged` cases)
exit: 0

$ uv run --group dev pytest tests/test_archive.py -q -k test_close_output_is_unchanged
4 failed, 1 passed, 164 deselected
exit: 1

$ git archive 1829d95… | tar -x -C /tmp/base187; (in /tmp/base187) uv run --group dev pytest tests/test_archive.py -q -k test_close_output_is_unchanged
4 failed, 1 passed, 164 deselected (the same four, on the base commit)
exit: 1

I also ran `grep` over `intent.md` and `docs/REFERENCE.md`, `ls` on the change's folders and a `git diff` of `scripts/board.py`; all are reads and exited 0.
