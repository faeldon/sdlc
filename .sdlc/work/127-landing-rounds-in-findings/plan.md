---
id: 127
slug: landing-rounds-in-findings
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 127 — A landing's review rounds go into findings.md · plan

> How the change is built, written after reading the code: the files, the order of work in
> vertical slices, the test each requirement gets, and what a revert wouldn't undo.

## Files to change

- `plugins/factory/scripts/factory.py`
  - `read_rounds()`: takes the round folder's kind (`round`, the default, or `land`), so the
    landing's `reviews/land-<n>/` are read with the same parsing (verdict, `CHANGE:`,
    `PREEXISTING:`, `NIT:`, the verifier's answers via `read_verified()` with its landing
    `where`). Each round dict carries its `kind`. `_no_verdict()` names the folder of its kind.
  - `agent_findings()`: unchanged rules over build and landing rounds together. `carried` (what
    stays `recorded`) is the last complete build round's kept changes, plus the last landing
    round's kept ones (a kept landing change no later round fixed is never claimed `fixed`). Each
    item carries its round's folder (`round-<N>` or `land-<n>`). The same `(role, text)` in a
    build and a landing round is one finding, the first (open question 2).
  - `finding_section()`: `Evidence:` falls back to the item's own folder; `Class:` says
    `<role> review, round <N>` for a build round and `<role> review, landing round <n>` for a
    landing round.
  - `cmd_land_close()`: after its by=auto refusals and before `_record_move()`/`_amend_record()`,
    when any landing round holds a review, `write_findings(folder, build + landing rounds)`, so
    the amend takes it into the landing's commit (open question 1: `land --close`, never
    `land-verdicts`, which only reads). With no landing review, carry's file is left as it is.
- Reused as is: `write_findings()` (rewrites only `By: <role>` sections), `_rounds_at_depth()`,
  `read_verified()`, `_amend_record()`, `land_message()` (no `Sdlc-Findings`).
- `plugins/factory/README.md`, `docs/REFERENCE.md`: say the landing adds its rounds.

## Work order

1. Slice 1: the landing writes its rounds' findings at `land --close`, committed. Test first in
   `tests/test_land.py`: a rebased change whose landing round 1 holds a kept change, a dropped
   change, a pre-existing line and one pre-existing line a build round raised too; the base moves
   (`land --close` says `moved` and amends the record in), round 2 passes, and the close lands.
2. Slice 2, the rerun: folded into the same test through the `moved` path, which runs
   `land --close` twice. The second run changes one section only, the kept change, `recorded`
   while no later landing round followed it and `fixed` once round 2 did; ship's own section is
   kept as written. (Planned as a separate `test_factory.py` test; the landing test reaches it
   end to end, so none was added.)
3. Docs: `plugins/factory/README.md`, `docs/REFERENCE.md`.

## Tests

- `test_a_landing_writes_its_rounds_findings_into_its_commit` (test_land.py): each finding once,
  its landing `Class:`, `fixed` / `wrong` with the verifier's why / `recorded`; the build and
  landing duplicate counted once; the rerun rewrites only what moved and keeps ship's section; the
  file reads clean through `sdlc.py`'s parser; the landed commit has no `Sdlc-Findings`.

## Rollback

Nothing outside git: findings.md is in the change's folder and lands in its commit. `git revert`
undoes it.
