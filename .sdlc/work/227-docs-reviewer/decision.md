DECISION: READY

**Why:** Round 2 is all `VERDICT: PASS`. The one change kept from round 1 is made: `skills/ship/docs.md` and `docs/REFERENCE.md` now say the `Docs review:` line is asked only of a change that has a `findings.md`. That matches `cmd_ship`, and `tests/test_findings.py` pins it. The gate passed, and the behaviour reviewer ran `tests/test_factory_docs.py` (27 passed). I found no open Critical or High finding, no disagreement, and no departure from the spec. The only open item is the D1 default, which the person confirms at the landing.

**Open items:**
- NIT (code reviewer): `plugins/factory/scripts/factory.py:1010`, `docs_review` re-reads every listed doc on each `_rounds_at_depth()` call. It is low-risk and optional.

**Decisions to confirm:**
- CONFIRM: D1: The build asks for the `Docs review:` line only when the change has a `findings.md`, so a hand-built change with none ships as before. Round 2 wrote this into `skills/ship/docs.md:27` and `docs/REFERENCE.md:161`. The landing's question can show the choice, and the person's yes there is enough. If they pick "always" instead, those two places and the test must change with it.

**For the person at ship:**
- Look first at `scripts/sdlc.py` around line 4187, where `cmd_ship` makes the docs line conditional on `findings.md`.
- Then look at `plugins/factory/scripts/factory.py`, `docs_review` and `_docs_applies`. Both copies join a run by the same rule, and `test_ship_and_the_factory_join_by_the_same_rule` pins that.
- Then look at the doc edits: the REFERENCE key, the factory README reviewer rows and the build skill sentence.
- The change touches no published interface that the person hasn't approved.

- IMPACT: minor — someone holding the previous release newly gets a docs review pass in ship and the factory, and nothing they already do changes.

No `notes.md` exists, so there are no undone items to dispose of.
