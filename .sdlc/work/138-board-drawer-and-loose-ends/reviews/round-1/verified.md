- KEPT: code: C1: scripts/sdlc.py:7613-7618: `unpushed_closes()` returning None, or the broad `except`, leaves every dangling issue with `waits_on_push: false`, so an issue an unpushed commit closes can be offered to triage again. Triage can't tell "read failed" from "nothing waits".
- KEPT: ux: C2: scripts/board.html:572: a whitespace-only `.md` file has truthy `doc.text`, so `md` is true and `paint()` draws an empty `div`. The "This file is empty." note only shows for `""`.
- KEPT: ux: C3: skills/triage/SKILL.md:57: the bullet tells the person to say the issue is "flagged `waits_on_push`", which is a field name, and its sentence "One an unpushed commit closes waits only on the push" reads badly. It should say in plain terms that the issue is waiting on the push.

## Notes
I only read the code and ran nothing. I did not read step 6 of the triage skill, so I did not check C3's request that step 6's report carry the same line. The wording defect in the bullet is clear from line 57 alone.
