DECISION: ESCALATE

**Why.** The change itself is ready to land. Both round-1 reviewers returned `VERDICT: PASS` and `build/round-1.gate.md` is green (`./check.sh`, 3461 passed). `notes.md` gives a reason for each of the ten files the intent named and each file on the current drift list. No test was deleted, so no coverage moved. The one thing holding it is D1, an open default. It decides what this repo's retro counts as tests (whether `evals/` is in), and that is a measurement-policy call only the person can make.

**Open items**
- None. No CHANGE is unresolved in round 1 (code: PASS, behaviour: PASS).

**Decisions to confirm**
- ESCALATED: D1: `retro.test_paths` decides what this repo's retrospective counts as a test. The second option, `["tests/", "evals/"]`, would change retro's totals and its file counts by kind. Choosing between them is a call about how the repo measures itself, so it is the person's, not one the approver can settle. The intent says nothing about it: its Affected names only `tests/` and the board fixture, not `.sdlc/config.toml`. The code reviewer's agreement is not the person's word.

**For the person at ship**
- Look first at the `.sdlc/config.toml` diff: one new line in `[retro]`, `test_paths = ["tests/"]`. This is what D1 covers. It is outside the intent's Affected list, and `plan.md` (*Files to change*) explains why it is there.
- Then `tests/test_hand_gate.py`: `test_hand_gate_reads_none_current_and_stale` now asserts `command` and `summary`. The builder showed it failing with `command` removed from `hand_gate()` and passing once restored.
- The change touches no published interface. `retro.test_paths` is an existing key, and only this repo's own config sets it.
- Retro reads the main checkout's config, so `tests.drifted` will only stop naming `skills/spec/SKILL.md` after this lands (`notes.md`).

- IMPACT: none — only this repo's own `.sdlc/config.toml` and one test assertion change; nothing a host receives is different.

**Each undone item's disposition**
- UNDONE: Retro's `tests.drifted` takes a test's code to be every code file its last change touched, so a test edited beside `sdlc.py` or `retro.py` drifts for good (`test_metrics.py`, `test_function_heat.py`), and an exact golden (`close-output.json`, `land-fix.txt`, `land-record-cases.json`) is named though it can't drift silently. A narrower notion of a test's code (the files it loads, or a host's list of goldens) would make the list worth acting on. → seed: Narrow retro's tests.drifted to a test's own code and skip exact goldens
