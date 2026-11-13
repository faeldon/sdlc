---
id: 055
slug: gates-in-dialogs
kind: plan
created: 2026-11-13
updated: 2026-11-13
---

# 055 — Ask every gate's question in a dialog · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `skills/{intent,spec,ship,close,drop,idea,bug,triage,retro,release,publish,setup,uninstall}/SKILL.md`:
  one shared paragraph in each WAIT section (ask with `AskUserQuestion`, the explicit-yes rule, the
  text fallback), `AskUserQuestion` in `allowed-tools`; publish's questions read `(no / yes)`; a
  variant question without answers gets `(yes / no)`.
- `plugins/factory/skills/{spec,build,eval,review}/SKILL.md`: the same (build already lists the
  tool).
- `scripts/metrics.py`: the `answer{reply, waited}` event in `read_events()`; `_membership()`'s close
  scan ends at a dialog approval; `summarize()` holds a dialog in a gated span as a stop the answer
  fills, picks the gate among answered stops, makes an unpicked dialog a `question`, and counts the
  dialog's wait as the person's (the turn's duration already leaves it out); `_revised()` and `rework()` count a dialog `revise`;
  docstrings.
- `tests/test_skills.py`: dialog, 2–4 answers, no recommended yes, publish no-first.
- `tests/test_metrics.py`: `result()` takes `toolUseResult`; the dialog gate, clock, close window,
  empty answer and revise tests.
- `docs/REFERENCE.md`: ship's question as a dialog. `guide/review.md` only if its gate line says how
  a gate is asked (then `sdlc.py record`). `AGENTS.md`: the Skills invariants bullet.

## Work order

1. Metrics and their tests: the existing cases unchanged, the new ones pass.
2. Skills: the shared paragraph, `allowed-tools`, publish's order, the variants; then the
   test_skills tests.
3. Docs: REFERENCE, AGENTS, the guide if it applies.
4. `./check.sh`.

## Tests

- R1, R3, R4: `test_every_wait_asks_in_a_dialog`.
- R2: `test_every_gate_offers_two_to_four_answers`.
- R6, R7: `test_every_gate_offers_two_to_four_answers` (no "Recommended"), `test_publish_offers_no_first`.
- R8: the existing ship-question tests, unchanged.
- R9: an intent span with a clarifying dialog and a gate dialog answered `yes` gives gate 1
  (approve) and question 1.
- R10: a dialog answered after 40 minutes is `away`, not `agent`.
- R11: a close approved by dialog ends its window at the next typed entry.
- R12: `tests/test_metrics.py`'s existing cases pass untouched; an errored or empty dialog adds no
  answer.
- R13: the graders unchanged, `test_a_stop_case_keeps_every_never_write_grader` pinning that no case grants the dialog; at ship, a scoped `run-cases 055`, with
  whether the run took the dialog or the fallback noted in `findings.md`.
- R14: read by the review.
- Manual: on a phone, `/sdlc:idea` on a scratch entry shows a dialog; `no` writes nothing.

## Rollback

`git revert <sha>` of the change's commit undoes all of it: skills, metrics, graders, docs. Nothing
is written outside the repo. `Close` commits made while it was live carry the same trailer keys, so
reverting leaves them readable; their gate counts were read from dialog answers and stay as written.
