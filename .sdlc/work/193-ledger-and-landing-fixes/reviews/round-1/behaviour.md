VERDICT: PASS

The change does what the intent's Approach describes, on the paths I could run. I found no failures.

## Notes
- **`checks.md`:** the change has none, so there is nothing to read or expect.
- **Decision question kept whole:** `raised_decisions()` returned `I reworded more than R7 and R9 list: the first thing second thing`, with both options and the why. 187's D3 lost exactly this.
- **Decision raised twice:** I fed it two identical `- DECISION:` blocks, which `raised_decisions()` returns as two tuples. I did not run `decisions` itself against a ledger. The dedupe lives in `cmd_decisions`, so the "lands once" outcome rests on the change's own tests, which passed.
- **Old ledgers still read:** `cmd_decisions` matches a raise by its first line alone as well, so ledgers written before this change keep reading. This is from the diff and the passing tests, not a run.
- **Read-only list:** `grep --der`, `--dere` and `--dereference-recursive=1` are refused. `--de`, which GNU grep treats as ambiguous, and `--dir` and `-r` pass, so the list only gets stricter at the intended prefixes.
- **Docstrings and `land` description:** the `land` description now names the slow gate at the tip and the approver's judgement of changed acceptance checks. The `landing.py` docstrings are updated.
- **AGENTS.md wrap nit (-70):** no edit, and the plan says the lines were already within the wrap at the base. The only line over 100 bytes (line 12) is over only because of its multi-byte arrows.
- **Gate:** `build/round-1.gate.md` says `GATE: PASS`.

## Evidence
$ cat .sdlc/work/193-ledger-and-landing-fixes/build/round-1.gate.md | head -5
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ git diff $(git merge-base HEAD main) -- plugins
(diff of factory.py, landing.py and the land SKILL.md, as read above)
exit: 0

$ git diff --stat $(git merge-base HEAD main) -- AGENTS.md; awk 'length>100{print FILENAME": "NR": "length}' AGENTS.md
AGENTS.md: 12: 103
exit: 0

$ sed -n 12p AGENTS.md
stages (intent → spec → plan → build → ship → close), with a person's approval at every stage
exit: 0

$ uv run --group dev python -I - (loads factory.py and calls raised_decisions on a scratch reply holding a multi-line decision and a duplicated one)
('builder round 1', 'blocking', 'I reworded more than R7 and R9 list: the first thing second thing', [{'option': 'a', 'notes': 'pro'}, {'option': 'b', 'notes': 'con'}], 'because', 'I reworded more than R7 and R9 list:')
('builder round 1', 'blocking', 'Same q?', [...a, b...], 'w', 'Same q?')
('builder round 1', 'blocking', 'Same q?', [...a, b...], 'w', 'Same q?')
exit: 0

$ uv run --group dev python -I - (loads landing.py and calls read_only_command on six grep commands)
grep --der x . `--der` makes grep follow symlinks, which can lead out of the checkout
grep --dereference-recursive=1 x `--dereference-recursive=1` makes grep follow symlinks, which can lead out of the checkout
grep --de x . None
grep --dere x . `--dere` makes grep follow symlinks, which can lead out of the checkout
grep -r x . None
grep --dir x None
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py -k "continu or twice or raised or reworded"
........                                                                 [100%]
8 passed, 391 deselected in 30.47s
exit: 0
