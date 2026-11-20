
I drafted the spec for 190. I resolved one open question from the code, proposed answers to the two the intent left open, and found one thing to check by hand before ship.

**Resolved from the code**
- **Is the rating part of the approval's answer, or a dialog of its own?** It's part of the approval's dialog, as a second question after the approval. A dialog before or after the WAIT would add a stop that metrics counts outside the gate. Metrics reads the first answer as the approval (`metrics._answers()[0]`, `metrics.py` around line 946), so the approval has to come first.
- **Which rating scale?** I proposed 1 to 4 (`4 smooth / 3 fine / 2 rough / 1 in the way`). A dialog question can't offer more than four answers (`test_every_gate_offers_two_to_four_answers`), and the trend needs numbers. The labels are the person's call. Changing them changes only R1's wording and R4's `EXPERIENCE_LABELS`.
- **Nit 2026-11-19-18** is taken in as R14. The three keys 168 added are `work_mix`, `time_to_users` and `follow_through`.

**Left for the person**
- **The line rides in the rating question's Other** ("3, the reviews dragged"). A question that only takes free text isn't possible, since each needs 2–4 options. If a separate line is wanted, the only shape left is a third question with placeholder options, and the spec rejects it.
- **Does the harness keep the questions in order?** The design assumes a two-question dialog lists the approval's answer first in `toolUseResult.answers`. R11 tests the shape the code reads, but no recorded transcript proves it. Before ship, check one real two-question transcript. If the order isn't kept, the fix is a metrics change with its own review.
- **AGENTS.md** should name the experience draft beside the insights draft in its *Retrospectives* paragraph. It's a one-clause doc fix, not a policy change. Say if you'd rather leave AGENTS.md alone in this change.
