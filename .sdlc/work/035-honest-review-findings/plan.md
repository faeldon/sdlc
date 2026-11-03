---
id: 035
slug: honest-review-findings
kind: plan
created: 2026-11-03
updated: 2026-11-03
---

# 035 — Review findings a person can trust · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

One refinement of the spec's Design, found reading the code: the `Sdlc-Findings` line is drafted
in Step 4, before the WAIT, so `findings.md` must already hold every disposition then. Ship writes
it complete after its review (Important ones `open`, a nit or pre-existing one proposed
`recorded`, earlier ones the diff no longer shows `fixed`); an "edit the message" answer that
dismisses one has ship rewrite the file and ask again. The WAIT approves the file as it stands,
and Step 6 writes nothing to it.

## Files to change

- `guide/review.md`: Pass 1 root-cause bullet (R2); Pre-existing defined (R4); reporting rules for
  evidence `path:line`, the bug's class, count first and "nothing to fix" (R1), three ranks;
  `### Paths this repo's review skips` slot under `## Reporting rules` (R3).
- `defaults/REVIEW.md`: `## Reporting rules` > `### Paths this repo's review skips` prompt; the
  failure-classes prompt says what failure looks like (R3).
- `templates/findings.md` (new): the shape of `findings.md` (R7), per `test_defaults.py`'s rules.
- `scripts/sdlc.py`:
  - `FINDINGS = "findings.md"`, `FINDING_RANKS`, `FINDING_PASSES`, `DISPOSITIONS`,
    `DISMISSALS`, `FINDING_RE` (`## F<n>. [rank] [pass] title`), beside `CHECKS`.
  - `findings_entries(folder)` (`entries`, `problems`, `open`), read as text, never raising, in the
    pattern of `acceptance()` and `nit_entries()`.
  - `findings_trailer(entries)`: `important`, `nit`, `preexisting`, the four passes, then each
    disposition as `pass:n,…` or `0` (R10).
  - `_findings_report(path)` and `cmd_findings(root, ident)` (read-only JSON: counts, `trailer`,
    `open`, `problems`; exit 1 on problems or open), a `findings` subparser, added to `READ_ONLY`
    (so `ALLOW_RULES`), and a `findings` part in `cmd_preflight` (R9).
  - `check`'s audit: a malformed `findings.md` reported like `checks.md` (not `open`).
  - `cmd_ship`: refuses while a finding is `open`, beside the undone refusal; no file, no refusal
    (R11).
  - `ship_question(..., bugs)`: a `the bugs shown filed in <register>` clause beside nits;
    `--bugs` on `preflight` (R5).
  - `DOC_TEMPLATES` gains `findings.md`; `ARTIFACT_ORDER` places it after `checks.md`.
  - `metrics_summary()`: each group's `findings` holds `important`, `nit`, `preexisting`,
    `passes`, `dispositions` (by pass, only from trailers carrying them) and `answered` (R12).
- `skills/ship/SKILL.md`: Step 3 writes `findings.md` (the named exception, said plainly), reading
  an earlier one first (R8: ids kept, `fixed` marked, a dismissed one never raised again); Step 4
  runs `sdlc.py findings <NNN>`, opens with its counts, takes the trailer from it, and proposes
  pre-existing findings as `[bug]` entries; Step 5 passes `--bugs`; Step 6 appends them; one new
  `Bash(...)` rule for `findings`.
- `skills/retro/SKILL.md`: `metrics`' findings carry dispositions; noise is `wrong` against all
  answered, read beside `answered` (R13).
- `docs/REFERENCE.md`, `guide/process.md` (the review's ranks and answers), `AGENTS.md` (the
  exception, a line on `findings`) (R14).
- `.claude/settings.json`: the `findings` allow rule, as 030 added `preflight`'s.
- `.sdlc/setup.json`: `scripts/sdlc.py record` rerun after the guide and defaults edits.
- `.sdlc/work/inbox.md`: 2026-11-03-2 and -3 deleted at ship (R15).
- Tests: `tests/test_findings.py` (new), `tests/test_preflight.py`, `tests/test_retro.py`,
  `tests/test_skills.py`, `tests/test_defaults.py`, `tests/test_sdlc.py`.

## Work order

1. Guide and defaults (R1–R4 text, the R3 slot), `record`, then `test_defaults.py` and `drift`.
2. `templates/findings.md`, constants, `findings_entries()`, `findings_trailer()`, with unit tests
   (malformed section, unknown rank, pass or disposition, dismissal without reason, open, ids).
3. `findings` command, `READ_ONLY`, the preflight part, `check`'s audit, the settings rule; tests.
4. `cmd_ship`'s refusal; `ship_question`'s `--bugs`; tests.
5. `metrics_summary()`'s extension; a retro test with an old and a new trailer.
6. Ship and retro skills; skill tests (rule present and used, one WAIT, trailer wording).
7. REFERENCE, the process guide, AGENTS.md; `./check.sh`.

## Tests

- R1, R2, R4: `test_defaults.py` asserts the rules' phrases in `guide/review.md`.
- R3: `test_every_prompt_sits_in_a_guide_slot` and the drift-clean gate.
- R5: `test_preflight.py`, the question's clause with and without `bugs`.
- R7: the template shape test (by glob), and `findings_entries` reading the template as an
  unfilled file without raising.
- R8: a skill text test for "never raised again" and "fixed" in Step 3.
- R9, R10: `test_findings.py`: counts, problems, the trailer string, and
  `metrics.parse_trailers()` on an old and a new trailer.
- R11: `test_sdlc.py`: ship refuses an `open` finding, and ships without `findings.md`.
- R12: `test_retro.py`: one old-trailer and one new-trailer change; `answered == 1`.
- R6, R13: `test_skills.py`, phrases in ship and retro.
- Manual: `sdlc.py findings 035` on this change's own file at ship.

## Rollback

`git revert` of the ship commit undoes it all. Not covered: hosts that ran `/sdlc:setup` meanwhile
keep the `findings` allow rule (harmless; uninstall removes it); `findings.md` files committed by
other changes stay in their history; seeds 2026-11-03-2 and -3 would have to be refiled by hand.
