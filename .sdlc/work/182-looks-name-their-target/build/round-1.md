## Build report: 182, looks name their target (Tier 1)

Both slices are built and the targeted tests pass: 5 named tests, and 568 across the four affected test files. I didn't run the full suite; the gate runs it next. Everything is uncommitted.

**Approach.** The intent touched four files, so I wrote a short `plan.md` (which files change, in what order, which test proves what, how to roll back). No code changed, only prose and tests. `factory.py`, `factory_records.py` and `REASON_RE` are untouched: the target is part of the reason's free text, which `REASON_RE` already reads whole. `prompts/approve.md` doesn't word an escalation rule, so I left it alone.

**Slices:**
1. **The approver's rule** (`plugins/factory/agents/approver.md`):
   - "Published interface" in the ESCALATE list now reads "a published interface the person hasn't approved".
   - A new paragraph, *What the person already approved is no look*. An interface the spec's *Contracts touched* names, or one the person's own `→ decided:` answer settles, is listed under *For the person at ship*, with no ledger line and no ESCALATE on that ground alone. At Tier 1 the source is the intent's *Affected* contracts or its Approach. A settled or assumed default never counts as the person's approval.
   - These stay looks whatever the spec says: a Critical or High finding still open, a disagreement, a departure from the spec, a requirement with no test, a destructive operation, a secret.
   - A look's form is now `- ESCALATED: look: <what to look at> — <why>`. *For the person at ship* also lists the approved interfaces and says where each was approved.
2. **Decide's look question** (`plugins/factory/skills/decide/SKILL.md`, Step 1):
   - The question names the target: the reason's text before ` — `, or the whole reason when there is no ` — `.
   - It says what each answer records: `seen` means acknowledged and accepted as built, with nothing verified; `checked something` records what the person verified.
   - The answers and the WAIT are unchanged. The decide bullet in `plugins/factory/README.md` says the same in a clause.

**Tests** (`tests/test_skills.py`):
- `test_the_approver_raises_a_look_only_for_what_no_one_approved` checks the rule about what's already approved, that those interfaces go under *For the person at ship*, the list of things that always stay looks, and the target-first form.
- `test_decide_names_what_a_look_asks_to_see` checks that the question names the target and says what `seen` and `checked something` record.
- I changed one existing test on purpose: `test_the_approver_gives_every_reason_a_line_with_its_kind` (from 145) pinned the old wording `` `- ESCALATED: look: <why>` ``. It now expects the new form; the `look:` kind and the line shape are the same. It fails without that update.
- Both new tests failed before the wording changes, for the expected missing-text reason.

**`plan.md`:** written this round and the build follows it, with no departures. **`notes.md`:** nothing added.

- DECISION: [default] Is a look "covered" when the spec names the interface under *Contracts touched* (at Tier 1, the intent's *Affected* contracts or its Approach) **or** when a person's `→ decided:` answer settles it? Going ahead with either one, but never a settled or assumed default.
  - OPTION: either the spec's contracts or the person's answer — both are the person's own approval; it moves the most stops that were never needed
  - OPTION: only the spec's *Contracts touched* — simplest to check; misses an interface the person approved in a decision
  - OPTION: only the person's words in `decisions.md` — clearest record of consent; 177's looks, approved in its spec, would still stop
  - WHY: the intent's Constraints say "the approved spec or the person's answers"
- DECISION: [default] Give a look a fixed `<target> — <why>` form inside the reason text, without a new parsed field? Going ahead with the fixed prose form.
  - OPTION: target-first prose, split at ` — ` — no parser change, so `REASON_RE` and the "no factory.py change" constraint hold; an approver that forgets the form still yields a readable question, just with the whole reason
  - OPTION: a parsed target field — decide could quote it exactly; changes `REASON_RE` and its pinned copy, which the intent rules out
  - WHY: the intent's constraint that how `factory.py` parses decisions doesn't change

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_skills.py -k "no_one_approved or what_a_look_asks"   (before the wording)
FAILED tests/test_skills.py::test_the_approver_raises_a_look_only_for_what_no_one_approved
FAILED tests/test_skills.py::test_decide_names_what_a_look_asks_to_see - asse...
2 failed, 416 deselected in 0.40s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_skills.py tests/test_prompts.py tests/test_land.py tests/test_nothing_local.py   (before updating the 145 assertion)
FAILED tests/test_skills.py::test_the_approver_gives_every_reason_a_line_with_its_kind
1 failed, 567 passed in 26.17s
exit: 1

$ uv run --group dev ruff format tests/test_skills.py && uv run --group dev ruff check tests/test_skills.py
1 file reformatted
All checks passed!
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_skills.py tests/test_prompts.py tests/test_land.py tests/test_nothing_local.py
568 passed in 20.30s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -k "no_one_approved or what_a_look_asks or every_reason_a_line or asks_each_look or weighs_each_open_default"
5 passed, 413 deselected in 0.04s
exit: 0
