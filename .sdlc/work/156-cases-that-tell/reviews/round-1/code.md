Reviewing the round 1 diff is nearly done. I read `scripts/sdlc.py`, `factory.py`, the skills, the graders and the docs against the spec, and I found nothing that needs a change, so the verdict is PASS.

VERDICT: PASS

## Notes

- NIT: scripts/sdlc.py:3877: `ceiling = int((5 - spent) * 100) / 100` can lose a cent to float error (for example 4.35 becomes 4.34). That is harmless, because it only errs low. Using `Decimal`, or `math.floor(x * 100 + 1e-9)`, would be more exact. {robustness S low}
- NIT: plugins/factory/skills/land/SKILL.md:~103: the decline path runs `--skip "declined at landing"`, so the note never carries the person's own reason. This is the builder's D1 default, and the spec's R16 says "their reason". It matches the repo's rule that a person's words stay off command lines, and it is an open default the person can overrule. {docs S low}
- DECISION notes: I reviewed against D1, D2 and D3 as the builder assumed them and have no objection to any of them. D3 (a rerun's ceiling is the cap less everything spent so far) is the safer reading of the intent's cost constraint.

**Done well**
- Every requirement has code behind it.
  - **Verdict logic:** it lives in the pure helper `case_verdicts()`, with environment cases handled and never rerun.
  - **Note line:** `cases_note()` composes it once, and `factory.py` writes it as given.
  - **Pinned copies:** `cases_failures()` and `CASES_RE` are copied into `factory.py` as the contract requires.
- The temporary-workspace removal is guarded: only an `e-*` folder directly in the resolved temp dir or `/tmp` is deleted, and anything else is listed under `left`.
- Landing order is clean.
  - **Cases before the question:** `factory.py cases` runs in Step 1, before the landing question.
  - **Fallback and no rule:** the train's `before: cases` fallback is kept, and neither `cases` nor `--skip` gets an `allowed-tools` rule.
  - **Contract edit:** `AGENTS.md`'s *Writes before a WAIT* names the new exception.
- The grader change drops the tool-specific `reads-behaviour` and grades the outcome with an `llm` grader instead.
- The docs now match the code. `CONTRIBUTING.md`'s *The skills' cases*, the factory README, ship's `cases.md` and release's `SKILL.md` all describe the rerun, the environment class and the kept traces.

**Checks run**
- I ran no tests. The gate record `build/round-1.gate.md` shows `./check.sh` green.
- I did not run the paid `run-cases` check the spec names.
