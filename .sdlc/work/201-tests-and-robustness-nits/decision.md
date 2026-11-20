DECISION: READY

**Why.** Both round-1 reviewers passed the change, and the gate record shows a green `./check.sh`: 3557 passed, 29 skipped. The two behaviour changes in `scripts/retro.py` are the only ones the intent allows, and each is pinned. The builder's evidence shows each new test failing against the old code or a deliberately broken copy of the guard, which meets the intent's rule that a changed test must fail without the code it covers. I found no departure from the spec or plan, and nothing in the reviews says the intent was wrong.

**Open items.**
- None. The code reviewer's two NITs are already recorded in `findings.md` (F1, F2) as `recorded`, not as changes asked for. I checked F2 against `notes.md`: all 20 nits that 191 had already settled are there, each naming the test that settles it.

**Decisions to confirm.**
- No blocking decisions are unticked.
- SETTLED: D1: The intent's Outcome asks for "one helper or fixture" against the commonest kind of `tests` nit. The unused-built-in-fixture check is the commonest kind the gate can judge, and `notes.md` (*The guard against the commonest kind*) says why the alternatives fall short. The round-1 code review confirms the guard tests its own detector both ways. It is test-only and touches no scope, policy or published interface.

**For the person at ship.**
- Look first at `scripts/retro.py`: the `rating in EXPERIENCE_LABELS` check in `_last_experience`, and the `_num()` calls in `_experience_text`. These are the only shipped behaviour changes.
- Then look at `tests/test_suite_shape.py`, the new guard. Per F1, it reads only `node.args.args`, so a keyword-only fixture slips past it.
- Then `tests/uv_run.py`'s `UNCACHED` phrases.
- No published interface is touched.

- IMPACT: patch — a hand-edited retro rating outside the whole numbers 1 to 4 now reads back as no rating instead of a wrong one. Nothing else anyone receives changes.

**Undone items.**
- None. `notes.md` has no unticked `- [ ]` lines.
