DECISION: READY

**Why:** Every requirement (R1–R8) has code and a test, and the reviewers found no Critical or High issue. The gate record for the build is `GATE: PASS` from `./check.sh` (3860 passed). The fix removes the `stacked == pre` shortcut in `_train_gate()` and reuses the existing gate, eject and ledger paths. It reads the check from the base branch's config. Nothing in the reviews suggests the spec was wrong. No reviewer ran the new tests themselves: the code and test reviewers relied on the green gate record, and the behaviour reviewer's run of 13 named tests passed.

**Open items:**
- NIT (code reviewer): the `plugins/factory/skills/land/SKILL.md` lines edited in Steps 3 and 4 run past the file's roughly 100-column wrap. Cosmetic.
- NIT (test reviewer): `tests/test_train.py:1546` uses `# fmt: skip` only to keep a parametrize table on one line. Cosmetic.

Neither NIT is in `notes.md`, so no change needs to carry them forward.

**Decisions to confirm:** none. There is no `decisions.md`, no blocking decision and no open default.

**For the person at ship:**
- Look first at `_train_gate()` and `_ungated()` in `plugins/factory/scripts/landing.py`, and then at `land_question()` and `cmd_land_check()`.
- Every one-change landing now runs the base's check once more, which takes minutes on a large suite. The spec accepts this cost, and the person's existing yes to "gated once at the tip" already covers it.
- Retro's `land_gates` count rises by one per one-change landing.
- On a base with no `[commands] check`, the question now says "not gated, since <base> names no [commands] check". The security reviewer notes such a landing can still approve itself (`by=auto`) when no change carries a risk signal.
- No published interface is touched beyond what the approved spec's *Contracts touched* names. That section lists the `land_question()` wording on a base with no check, the `ungated` key and the ledger check for a train of one.

- IMPACT: patch — a one-change landing is now gated at its committed tip, and a landing with no check says so. Nothing anyone holding the previous release must do differently.

**Undone items:** `notes.md` doesn't exist, so there are none.
