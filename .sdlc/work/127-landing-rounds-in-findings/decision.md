DECISION: ESCALATE

**Why.** The work is done. Round 2 passed, the gate passed (2337 passed, 13 skipped), and the one kept change from round 1 (the AGENTS.md line on who writes `findings.md`) was fixed. But the builder made three choices you were never asked about. They are still unticked defaults in `decisions.md`, and the whole build depends on them, so you need to confirm them before this lands.

**Open items**
- None. Round 1's one CHANGE (code reviewer, AGENTS.md:195) is fixed, and round 2's code review passed.
- These minor notes stay open and are recorded in `findings.md` as F2–F5:
  - F2 (code): `land --close` treats any landing round with a review as complete. It doesn't check that `land-verdicts` returned `pass`; it relies on the land skill to have done that.
  - F3 (code): if `carry` runs again after a landing has started, it drops the landing's sections from `findings.md`. The next `land --close` puts them back.
  - F4/F5 (code): the note in `templates/findings.md` still names only `carry` as a writer. This is the same item as the one in `notes.md`.

**Decisions to confirm**
- D1: the landing's findings are written at `land --close`, not at `land-verdicts` when it returns `pass`.
- D2: a finding raised with the same role and text in both a build round and a landing round counts once, under the round that raised it first.
- D3: a change the verifier kept in the last landing round, with no round after it, reads `recorded`, never `fixed`. It reads `fixed` once a later landing round follows it.

**For the person at ship**
- Start with `cmd_land_close()` in `plugins/factory/scripts/factory.py`.
  - Check that `write_findings()` runs after the by=auto refusals and before `_record_move()` and `_amend_record()`.
  - Check F2: it accepts a landing round as soon as it has any review.
- Then look at how `agent_findings()` builds `carried` and removes duplicates across build and landing rounds. That is where D2 and D3 are implemented.
- Last, `test_a_landing_writes_its_rounds_findings_into_its_commit` in `tests/test_land.py`.

- IMPACT: patch — `findings.md` now also holds the landing's review rounds, so the record and retro's counts get more complete; nothing new to run and nothing anyone has to change.

- UNDONE: `templates/findings.md`'s note (and its copy `FINDINGS_HEAD`) still says only "the factory's `carry` writes its agents' findings into it"; it could name the landing too. Left out: the note is pinned to the template, ships to hosts, and needs `sdlc.py record`. → seed: findings.md template note names the landing as a writer
