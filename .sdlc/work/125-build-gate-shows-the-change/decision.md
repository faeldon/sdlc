DECISION: ESCALATE

**Why.** The build is done and the reviewer passed it. The code reviewer passed round 1, the full `./check.sh` gate passed (2350 passed, exit 0), and both checks in `checks.md` pass now and fail against the old skill text. The reviewer found only nits. But five decisions in `decisions.md` are still unticked, so the build rests on assumptions you haven't confirmed. One of them (D3/D5) goes against what the intent says: the intent says the template sentences leave the skill, and one fill-in reference form stays. The change also edits a skill's WAIT step at Tier 1, on the argument that what the yes approves doesn't change. And the script says `1 round` where the old sentence said `1 rounds`, which breaks the intent's "word for word" rule.

**Open items**
- F1 (code): `_listed([])` returns `no reviewer`, so the question reads "no reviewer review it in up to 3 rounds", which is bad grammar (factory.py:830).
- F2 (code): `build_question()` writes `1 round` where the old template wrote `1 rounds`, against the intent's "word for word" constraint. It is noted in `notes.md`.
- F3 (code): `test_the_script_gates_each_build_before_any_reviewer` only checks that `", with no gate configured"` appears somewhere in `factory.py`. That is a weak test.

**Decisions to confirm**
- D1: Step 1 quotes all of Problem and Outcome, with no length limit and no pointer to the file.
- D2: A restart or upgraded run shows only the intent's title, not its Problem and Outcome.
- D3: Step 2 keeps the question's fullest plain form as a reference, because `test_every_gate_offers_two_to_four_answers` needs one. Every other template sentence was removed.
- D4: `/sdlc-factory:spec`'s gate question stays worded in the skill for this change.
- D5: The code reviewer backs D3, but wants the reference marked in the skill as a form never to fill in or ask. It also says you should confirm it, since it goes against "templates leave the skill".

**For the person at ship**
- Read `plugins/factory/skills/build/SKILL.md` Steps 1–2 first. Check that Step 1 really quotes the intent before the machinery, and that the kept reference form can't be read as one to fill in (D3/D5).
- Then compare `build_question()` in `factory.py` with the removed template sentences. Look at the `1 round` and `no reviewer` wording, and check that the gate, sensitive-path and `[ui]` parts read the base branch's config.
- Lastly, decide whether a WAIT step change at Tier 1 is acceptable here.

- IMPACT: minor — `factory.py start` prints a new `question` field, and the build gate now shows what the change is for before you approve it; what the yes approves is unchanged.

- UNDONE: `/sdlc-factory:spec`'s WAIT still words its question in the skill (`Write this as .sdlc/work/NNN-<slug>/spec.md and advance the change to stage: design?`), but its only placeholder is the folder name, so there is nothing a model could get wrong in it; left out of this change, per the intent's scope. → seed: The factory's spec gate asks a question worded by the script
- UNDONE: `build_question()` writes `1 round` where the old template would have read `1 rounds`; only a host setting `rounds = 1` or `[light] rounds = 1` sees it. → dropped: already done in this change on purpose (it fixes the grammar), and it is shown at ship as F2
