---
id: 165
slug: scorecard-waves
tier: 1
impact: none
stage: shipped
created: 2026-11-19
opened: 2026-11-18T23:20Z
updated: 2026-11-19
shipped: 2026-11-19
idea:
depends_on:
serves: none
---

# 165 — The scorecard's wave plan lives in its doc

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`docs/RETRO-SCORECARD.md` ends with a four-step *Suggested order* (S7 and S1 first; then S2, S3,
S4, S11, S12, S13; then S5, S6, S8, S9, S10; then S14–S16), written before any of it was built.
The plan the work actually follows has since been refined into waves 0–6 and lives only in a
supervisor session's memory: waves 0 and 1 landed as 160, 161, 162, 163 and 164; wave 2 onwards
splits the remaining seeds and refactors differently; and the register's 60 open ideas, bugs and
nits are each placed with the change that touches their files. A fresh session or a fresh clone
can't see any of it. Two seeds filed since the doc landed are missing from its tables: comment
health (2026-11-19-9) and the feature map (2026-10-25-3), which gives S5 its list.

## Outcome

- *Suggested order* is replaced by a *Waves* section: waves 0–6 in order. Waves 0 and 1 are marked
  done, each seed or refactor beside the change that landed it (R1 = 160, S7 = 161, S1 = 162,
  R4 = 163, R2 = 164). Wave 1½ (two bug fixes before wave 2) and waves 2–6 list their changes and,
  under each, the register entries it takes in, by id. Wave 6 is the backlog outside the scorecard.
- The *Data* seed table gains **S17**, comment health (2026-11-19-9, after S8), and S5's row names
  the feature map (2026-10-25-3).
- Every register entry open when this lands is named in exactly one wave, checked by hand against
  `sdlc.py status --all` at ship.
- Nothing else in the doc changes: the pillars, metrics and Hosts section stay as they are.

## Affected

- **Area:** this repo's design docs.
- **Files & components:** `docs/RETRO-SCORECARD.md` only.
- **Downstream:** the person planning the next wave, and a session drafting that wave's intents.
  No host reads it; no code or test parses it.
- **Contracts:** *Nothing about a project or a workspace* (`tests/test_nothing_local.py`): no
  machine path and no bare `work/NNN` citation; change numbers and register ids are fine.

## Constraints

- The doc is this repo's design reference, not a register: an entry's state stays in
  `.sdlc/work/inbox.md`, and the doc names ids only, never copies an entry's text.
- Lines wrap near 100 columns, as the rest of the file does: no new style nits.

## Open questions

- Whether 2026-11-19-1 and -2 (nits restating D3 and D1, which the person decided at 162) sit under
  R6 to be retired as answered, or are left out of the plan.

## Approach

Replace `### Suggested order` with `### Waves`: a short paragraph saying a wave's changes name these
entries in their intents, so landing retires them, then one subsection per wave as the plan has it.
Wave 1½ is bug -95 with idea -91, and bug -103 with idea -66. Wave 2 is S2+S12+S13, S3, S11, R3, R6
and the style pay-down (idea -89), each with its ids. Waves 3–6 are the same in shape. Add S17's row
to the *Data* table and name the feature map in S5's row. Re-check the ids against `sdlc.py status
--all` on `main` just before ship, since nits may be filed meanwhile, and put any new one in its
wave. The seeds stay in the register, so the intent carries no `idea:` line: listing an entry in a
plan doesn't build it.

The wave plan to write down (ids without a date are 2026-11-18-<n>):

- **Wave 0, done:** R1 = 160, S7 = 161.
- **Wave 1, done:** S1 = 162, R4 = 163, R2 = 164.
- **Wave 1½:** bug -95 + idea -91; bug -103 + idea -66.
- **Wave 2:** S2+S12+S13 takes -64, -65, -97. S3 takes -92, -86, -87. S11 takes -107. R3 takes
  -68, -69, -80, -84, -70, -71, -85, -98 and idea -67. R6 takes 2026-11-19-1 to -4 and -100. The
  style pay-down (-89) takes -81, -82, -75, -77, -78, -83, -96, 2026-11-19-5, -76 and -108, and
  lands last in the wave.
- **Wave 3:** S4; S5 with the feature map 2026-10-25-3 and the process map 2026-10-25-1; S6 with
  -93; S8; S17 (2026-11-19-9, after S8); S9; S10.
- **Wave 4:** S14 with -105.
- **Wave 5:** S15, S16, and R5 with the tests pay-down (-88) and the pruning pass (-90), taking
  -79, -101, -104, -109 and 2026-11-19-6 to -8.
- **Wave 6, outside the scorecard:** 2026-10-25-23, 2026-10-27-10, 2026-10-26-11, 2026-10-26-13,
  2026-10-26-10, 2026-11-10-2, -74, 2026-11-13-1, -99, 2026-10-24-6.
