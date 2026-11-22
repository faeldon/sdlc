DECISION: READY

**Why:** All three round-1 reviews are `VERDICT: PASS`. The gate record is a green `./check.sh` (4038 passed, `claude plugin validate --strict` passed). Every requirement R1–R12 has a named test, and the reviewers found no Critical, High or Required problems. The build follows the spec and `plan.md`, and nothing suggests the spec was wrong. `landing.py`, `guide/` and `defaults/` are untouched, as R12 requires.

**Open items**
- NIT (code reviewer): `factory.py:3013`: the `again` loop recomputes `_nit_path` for each pair of nits, which is tidier to compute once per role. It is a minor refactor on tiny sets.
- NIT (code reviewer): `sdlc.py:7776`: the nit branch of the claim check needs a short comment saying it is deliberately separate from `_claimed_by`.
- NIT (test reviewer): `tests/test_factory_loop.py:921`: the restart is modelled by hand in the filing test. `cmd_restart` is exercised only in the R4 prompt test.
- Unconfirmed by the behaviour reviewer: whether the paragraph around `docs/REFERENCE.md:518` now covers nits. The code reviewer's grep found no stale mentions.

**Decisions to confirm**
- SETTLED: D1: `_nit_section()` is a naming choice inside a pinned copy of the factory's reader. R9 asks for a copy and says it never imports, the R9 test pins both readers agreeing, and the code review found no clash with core's `_section()`.
- SETTLED: D2: the wording is internal to the new `review` part (R4). The spec fixes its behaviour, the `review-earlier` prompt fixture pins the wording, and `test_a_review_names_its_roles_earlier_nits` covers its behaviour, including the restart case that motivated naming the round.

**For the person at ship**
- Look first at `agent_findings()` in `plugins/factory/scripts/factory.py`, where the new disposition order decides what is filed. It reverses 129 R5, which the spec names. Then look at the `_inbox_commit()` nit claim check in `scripts/sdlc.py`.
- Check `docs/REFERENCE.md` near line 518 for the register paragraph (R11).
- Published interfaces touched: none beyond what the spec's *Contracts touched* names, and all are approved there. `inbox-commit` now retires a nit with its three reasons and no new trailer. `/sdlc:idea` keeps its one WAIT.

- IMPACT: minor — someone holding the previous release can now retire a nit through `/sdlc:idea` as `duplicate`, `stale` or `wontfix`. The factory also files fewer nits (only the last round's, at `med` value).

Undone items: `notes.md` does not exist, so there are none.
