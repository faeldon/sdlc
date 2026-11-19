## Rework report: 182, round 2

I made the one kept change and the nit. The tests that cover the edited files pass (568 and 457); I didn't run the full suite, which the gate does next. Everything is uncommitted, and `plan.md` and `notes.md` are unchanged.

- KEPT (code, docs/REFERENCE.md:544): done. The look line now reads `` `- ESCALATED: look: <what to look at> — <why>` ``, still filed as `(approver round <R>, look)`, and it now says the decide question quotes the target before ` — `. Nothing in `docs`, `plugins`, `skills`, `tests` or `README.md` still uses the old `look: <why>` form.
- Nit (code, approver.md:44): done. The sentence now reads "a destructive operation, a secret, or a published interface the person hasn't approved", so "hasn't approved" applies only to the published interface.

No new decisions this round; D-lines from round 1 stand as raised.

- UNTESTABLE: none

## Evidence

$ grep -rn "look: <why>" docs plugins skills tests README.md
(no output)
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_skills.py tests/test_prompts.py tests/test_land.py tests/test_nothing_local.py
568 passed in 82.76s (0:01:22)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_defaults.py tests/test_nits.py tests/test_findings.py tests/test_retro.py tests/test_release.py
457 passed in 25.67s
exit: 0
