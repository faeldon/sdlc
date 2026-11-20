---
id: 202
slug: defaults-to-landing
kind: plan
created: 2026-11-20
updated: 2026-11-20
---

# 202 — An escalation of assumed defaults alone goes to the landing's question · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `CONFIRM_RE` beside `SETTLED_RE`/`ESCALATED_RE`;
  `approver_weighing()` returns a third value, `confirms` (id → reason, first of each);
  `cmd_decisions` counts a CONFIRM in the "named twice" rule (an id CONFIRMed and ESCALATED is
  listed in `unsettled`, a SETTLED beside a CONFIRM is refused as today) and never marks it;
  `cmd_ask` adds each item's `confirm`; `UNCARRIED`, the problem's opening; new
  `intent_closes(folder)` (the intent's `closes:` as
  text, `""`/`[]` as none) and `no_confirm_why(sensitive, closes)` (the reasons CONFIRM is barred,
  shared by the prompt and the check); `weigh_text(ledger, sensitive, closes)` picks `weigh` or
  `weigh-no-confirm`; the approve branch of `_task` passes `state["sensitive"]` and the intent's
  closes; the approver's mend picks `mend.md`'s `confirm` part when the state's problems hold an
  `UNCARRIED` one; `PROMPT_PARTS` gains both parts; the module docstring's word on defaults.
- `plugins/factory/scripts/run_state.py`: `uncarried(folder, ledger, decision, sensitive,
  closes)` → `[(id, why)]`, called by `loop_state()` after `read_decision()`; each becomes a
  problem (`uncarried_text()`: `factory.UNCARRIED`, the id and why; here, not in `factory.py`,
  since only this module calls it, `tests/test_modules.py`) registered under `mendable["approver"]`, so
  `runs/mended` limits it to once a round.
- `plugins/factory/scripts/landing.py`: `land_parts()`'s `assumed` entries gain `default` (first
  `- OPTION:`) and `reason` (the approver's CONFIRM reason); `land_shown()` prints
  `D2: <q> — assumed: <default> (the approver: <reason>)`, each part only when present.
- `plugins/factory/prompts/common.md`: `weigh` offers the three lines; new `weigh-no-confirm`
  (`ids why`).
- `plugins/factory/prompts/mend.md`: new `confirm` part (`problems`).
- `plugins/factory/agents/approver.md`: *Weigh each open default* gives CONFIRM and when READY may
  carry it; *How to decide* no longer says any default escalates.
- `skills/ship/factory.md` Step 4: the CONFIRM reason shown beside each open default; the approval
  confirms it.
- Docs (R12): `plugins/factory/README.md` *Default* bullet, `plugins/factory/skills/build/SKILL.md`
  decisions paragraph and Step 4, `plugins/factory/skills/decide/SKILL.md` description,
  opening and the item's fields (`confirm`), `AGENTS.md` factory paragraph's mend list.
- Tests: `tests/test_factory_decisions.py` (R2, R3, R5, R10), `tests/test_prompts.py`
  + recorded copies `approve-defaults.txt` (re-recorded), `approve-defaults-bare.txt`
  (re-recorded), new `approve-defaults-sensitive.txt`, `approve-defaults-closes.txt`,
  `mend-confirm.txt` (R4, R3's mend prompt), `tests/test_land.py` (R7, R8, R9, and the existing
  settled test's `assumed` shape), `tests/test_sdlc.py` (R6), `tests/test_skills.py` (R1's doc, R11, R12, beside the approver's
  and ship's other doc tests).

Reused, not re-derived: `depth()`'s `sensitive` (already in the loop state), `read_ledger()`'s
`options`, `frontmatter()`, `prompt_part()`, the mend machinery (`mended()`, `mend_round()`),
`_dispose()`'s `CONFIRMED` tick and `land_signals()`'s assumed signal (unchanged, pinned).

## Work order

1. **Reading CONFIRM (R2).** Test first: a CONFIRM line leaves D2 open and assumed; CONFIRM +
   ESCALATED is named twice. Then `CONFIRM_RE`, `approver_weighing()`'s third value,
   `cmd_decisions`.
2. **The approve prompt (R1, R4).** Golden copies first (re-record `approve-defaults*`, new
   sensitive and closes cases), then `weigh`/`weigh-no-confirm`, `intent_closes()`,
   `no_confirm_why()`, `weigh_text()`'s new signature and the approve branch.
3. **The check and its mend (R3, R5).** Tests on `loop_state` for the four uncarried cases, the
   second time a rerun, an ESCALATE untouched; then `uncarried()`, the problem text, the mend
   part and its golden case.
4. **Core pins (R6).** `needs_of`/`column`/`decide_step` test on a READY with assumed defaults: no
   code change expected.
5. **The landing (R7, R8, R9).** Tests on `land-check` and `land` for a READY change whose default
   is CONFIRMed; then `land_parts()` and `land_shown()`.
6. **`ask` (R10).** Test then the `confirm` field.
7. **Docs (R1 doc, R11, R12).** Tests then the approver doc, ship's side file, README, build and
   decide skills, the docstring, AGENTS.md.

## Tests

- R1: `test_the_approver_doc_offers_confirm` (test_skills); golden
  `approve-defaults.txt`.
- R2: `test_a_confirm_line_leaves_the_default_open`, `test_a_confirm_and_an_escalated_line_are_named_twice`.
- R3: `test_ready_with_an_uncarried_default_is_mended` (parametrized: unlined, escalated,
  sensitive, closes), `test_a_confirmed_default_on_a_plain_change_is_done`,
  `test_a_second_uncarried_ready_is_a_rerun`; golden `mend-confirm.txt`.
- R4: golden `approve-defaults-sensitive.txt`, `approve-defaults-closes.txt`.
- R5: `test_confirm_on_an_escalate_still_needs_deciding`.
- R6: `test_ready_with_assumed_defaults_is_ready` (test_sdlc).
- R7: `test_carried_defaults_keep_the_gate_the_persons` (test_land).
- R8: `test_the_landing_shows_each_assumed_default_with_its_default` (test_land).
- R9: `test_the_landing_yes_confirms_carried_defaults` (test_land).
- R10: `test_decide_answers_a_ready_changes_carried_defaults`.
- R11: `test_ship_shows_carried_defaults` (test_skills).
- R12: `test_no_doc_says_any_default_escalates` (test_skills).

## Rollback

`git revert` undoes it all: no data is written outside the repo. A change built while this was in
force may hold `- CONFIRM:` lines in its `decision.md`; after a revert they are read as nothing, so
its open defaults count as escalated again, and its READY reads as it did before this change
(no stop). Nothing to undo by hand.
