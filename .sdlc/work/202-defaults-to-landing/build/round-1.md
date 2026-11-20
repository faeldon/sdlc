I built all 12 requirements and wrote `plan.md` first. Nothing is committed and `HEAD` hasn't moved. The full gate passed (3561 tests, ruff, format, `plugin validate --strict`). The approver can now carry a default to the landing with a `- CONFIRM: D<n>: <reason>` line. That line stays open in the ledger, the change can be READY, and the landing's yes confirms it as shown.

**Slices built**
1. **Reading CONFIRM (R2).** Added `CONFIRM_RE`. `approver_weighing()` now also returns the CONFIRM lines, by id. `cmd_decisions` never marks a CONFIRMed line. An id given two of SETTLED, ESCALATED and CONFIRM is reported as named twice.
2. **The approve prompt (R1, R4).** `common.md`'s `weigh` part offers the three lines. A new `weigh-no-confirm` part is used instead, saying why, when the diff touches a sensitive path or the intent has `closes:`. The reasons come from `intent_closes()` and `no_confirm_why()` in `factory.py`.
3. **The check and its mend (R3, R5).** `run_state.uncarried()` makes it a stop when a READY rests on an open default that has no CONFIRM, has an ESCALATED line, or has a CONFIRM that is barred. The stop names each id and why. The approver is asked again once a round through the new `mend.md` `confirm` part; a second time is a `rerun` stop. On an ESCALATE nothing changes.
4. **Core (R6).** No code change. A test now pins that a READY with assumed defaults is in Ready, with no decide step.
5. **The landing (R7–R9).** Each `assumed` entry gains `default` (its first option) and `reason` (the approver's CONFIRM). `land_shown()` prints `D1: … — assumed: 50 (the approver: …)`. The signals and the ledger ticks on the yes were already right, and tests now pin them.
6. **`ask` (R10).** Each item gains a `confirm` field.
7. **Docs (R1, R11, R12).** Updated `approver.md`, ship's `factory.md` Step 4, the factory README, the build and decide skills, the `factory.py` docstring and AGENTS.md's list of stops a run mends.

**Tests added, and what each proves**
- `test_a_confirm_line_leaves_the_default_open` and `test_a_confirm_and_an_escalated_line_are_named_twice` (R2).
- `test_ready_with_an_uncarried_default_is_mended`, run four ways: no line, ESCALATED, sensitive path, `closes:` (R3).
- `test_a_confirmed_default_on_a_plain_change_is_done` (R3).
- `test_a_second_uncarried_ready_is_a_rerun` (R3; it also checks the mend prompt names D1).
- `test_confirm_on_an_escalate_still_needs_deciding` (R5).
- `test_decide_answers_a_ready_changes_carried_defaults`, run for a kept and a changed answer (R10).
- New golden prompts `approve-defaults-sensitive`, `approve-defaults-closes` and `mend-confirm`; `approve-defaults` and `approve-defaults-bare` re-recorded and read (R1, R3, R4).
- `test_carried_defaults_keep_the_gate_the_persons`, `test_the_landing_shows_each_assumed_default_with_its_default` and `test_the_landing_yes_confirms_carried_defaults` (R7–R9).
- `test_ready_with_assumed_defaults_is_ready` (R6).
- `test_the_approver_doc_offers_confirm`, `test_ship_shows_carried_defaults` and `test_no_doc_says_any_default_escalates` (R1, R11, R12).
- Updated: three existing assertions that pinned the old shape of `assumed` and of `ask`'s items.

Every new test failed before its code went in, except the pins of existing behaviour (R6, R7, R9). I saw each pin fail against a deliberately broken copy of the code, then restored that code.

**Where the build departs from the spec, with `plan.md` updated to match**
- The doc tests for R1, R11 and R12 are in `tests/test_skills.py`, beside the approver's and ship's other doc tests.
- `uncarried_text()` is in `run_state.py`, not `factory.py`, because `tests/test_modules.py` requires a function only that module calls to live there.
- `weigh-no-confirm` is a whole alternative to `weigh` rather than a replacement for one clause. It repeats the shared sentences.

Nothing is left in `notes.md`.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "confirm_line or named_twice"
2 failed, 82 deselected in 1.08s
exit: 1

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "confirm_line or named_twice"
2 passed, 82 deselected in 1.44s
exit: 0

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "uncarried or confirmed_default or confirm_on_an"
5 failed, 2 passed, 84 deselected in 34.47s
exit: 1

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "uncarried or confirmed_default or confirm_on_an" -n auto
7 passed in 2.44s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_modules.py tests/test_prompts.py tests/test_factory_decisions.py
190 passed in 17.70s
exit: 0

$ uv run --group dev pytest -q tests/test_sdlc.py -k ready_with_assumed   (needs_of mutated to count READY)
1 failed, 288 deselected in 1.31s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_land.py -k "carried or each_assumed_default"
FAILED tests/test_land.py::test_the_landing_shows_each_assumed_default_with_its_default
1 failed, 4 passed in 4.88s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_land.py
90 passed in 78.05s (0:01:18)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory_decisions.py
93 passed in 12.51s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py
428 passed in 1.00s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_land.py -k "yes_confirms_carried"   (landing's tick mutated off)
FAILED tests/test_land.py::test_the_landing_yes_confirms_carried_defaults - A...
1 failed in 4.39s
exit: 1

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 202
All checks passed!
329 files already formatted
3561 passed, 29 skipped in 239.45s (0:03:59)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory_decisions.py tests/test_prompts.py tests/test_land.py tests/test_skills.py tests/test_sdlc.py -k "confirm or carried or uncarried or assumed_default or any_default_escalates or approve_defaults or mend or ask"
107 passed in 34.31s
exit: 0
