DECISION: ESCALATE

**Why.** Round 1 of the code review passed, the gate is green (2338 passed), and the reviewer found code and a test for every Outcome line in `intent.md`. It escalates because four decisions in `decisions.md` (D1–D4) are still unticked: the build rests on defaults you haven't confirmed. D1 also decides how the landing's WAIT dialog shows what a yes approves. The reviewer couldn't confirm that the dialog renders `preview` on the `yes` option at all, and if it doesn't, the main fix in this change doesn't reach you.

**Open items**
- [nit] `plugins/factory/skills/land/SKILL.md:76`: the Step 1 sentence "Under each change, what the yes approves for it…" runs past the ~100-column wrap (raised by code; F1, minor).
- [nit] `plugins/factory/skills/land/SKILL.md:102`: the question still says "as shown", and only Step 2 says this now means the `preview` text (raised by code; F2, minor).

**Decisions to confirm**
- D1: `shown` is passed as the `preview` of the `yes` and `yes, with a fix` options. The question's text is unchanged. The other options were putting it in the question's text or only above the dialog.
- D2: each change's whole intent (title, Problem, Outcome) goes in Step 1 above the dialog. The dialog's `shown` holds only its title, however big the batch.
- D3: Problem and Outcome are quoted in full, with no length cap.
- D4: `shown` also holds checks, cases and `How to recover:` lines, not only dispositions and assumed decisions.

**For the person at ship**
- Look first at Step 2 of `plugins/factory/skills/land/SKILL.md` (around lines 102–112): how `shown` is passed as `preview`, and the text fallback that prints `shown` right before the question.
- Then check that the question passed to the dialog is still `land_question()`'s exact text.
- In `factory.py`, check that `land_shown()` and `intent_parts()` write nothing, and that `cmd_land_check()` only adds the `intent` and `shown` fields.
- The quickest way to settle D1 is one live landing of a batch with a seed, a bug and a drop. It shows whether the preview is visible inside the dialog.

- IMPACT: patch — the landing gate shows each change's intent and what its yes will file inside the dialog. `land-check` gains two output fields, and what a yes approves is unchanged, so nobody has to do anything differently.

There is no `notes.md` in the change folder and the builder reported nothing left over, so there are no UNDONE lines. The prompt names no irreversible paths, so there are no RECOVER lines. The plan's rollback is a plain `git revert`.
