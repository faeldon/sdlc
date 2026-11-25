---
id: 235
slug: tests-robustness-nits
tier: 2
impact: patch
stage: shipped
created: 2026-11-23
opened: 2026-11-23T01:36Z
updated: 2026-11-26
shipped: 2026-11-26
idea: 2026-11-22-50
depends_on:
opened_by: autopilot
---

# NNN — Pay down the tests and robustness nits

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The register holds 24 open `tests` nits and 7 open `robustness` nits. Both counts are past the
process doc's threshold of 5. The oldest is from 2026-11-20. The retrospective of 2026-11-22 raised
this seed (2026-11-22-50) to pay them down in one change. Each nit must be checked against the code
first, and any the code has moved past is retired as stale.

The `tests` nits, each with the file it names:

- 2026-11-20-45, `tests/test_train.py`: the `[edit]` and `[mv]` cases both stray on
  `.gitignore`. Nothing pins on its own that a staged rename's old path is named when only the new
  path is owned.
- 2026-11-20-48, `tests/test_factory_decisions.py`: the "closes" case writes `closes: [12]` by
  string-replacing `idea:` in `intent.md`.
- 2026-11-20-54, `tests/test_suite_shape.py`: the check reads `node.args.args` only, so it misses
  a keyword-only fixture. `BUILT_IN` is also a list kept by hand.
- 2026-11-20-59, `tests/test_records_ledger.py`: the two-writers test covers `factory.py`'s writer
  only, not core's copy under the same lock.
- 2026-11-20-62, `tests/test_records_ledger.py`: the writer test runs 400 locked appends. A
  smaller count would still prove whole lines.
- 2026-11-21-6, `tests/test_skills.py`: `test_idea_and_bug_offer_an_origin_line` only asserts
  that `Origin: self` is absent.
- 2026-11-21-10 and 2026-11-21-11, `tests/test_update.py`: the fake `claude` opens its log and
  rows files without `encoding="utf-8"`. These two are the same finding from two rounds.
- 2026-11-21-13, `tests/test_retro_hosts.py`: no fixture lists a path under `.claude/worktrees/`,
  so R3's `own` case is never exercised.
- 2026-11-21-14, `tests/test_retro_hosts.py`: the `!` exclusion is tested only against a path that
  doesn't exist.
- 2026-11-21-15, `tests/test_retro_hosts.py`: R12 is not checked against the report's indicators
  block.
- 2026-11-21-17, `tests/test_setup_lifecycle.py`: the R5 test never forces a `ValueError`
  (`UnicodeDecodeError`).
- 2026-11-21-19, `tests/test_skills.py`: the triage skill's `Origin: host` instruction has no text
  test.
- 2026-11-21-27, `tests/test_train.py`: no case pins that a bare `-d dereference-recurse` grep
  pattern is refused, the trade-off D2 accepts.
- 2026-11-21-31, `tests/test_skills.py`: `PREVIEW_NAMES` words are matched as substrings, so
  `path` or `tag` matches any text containing them.
- 2026-11-21-39, `plugins/factory/scripts/factory.py`: `_hand_digests` copies `sdlc.py`'s by hand,
  and no test in `tests/test_hand_gate.py` pins the two bodies equal.
- 2026-11-21-40, `tests/test_factory_ui.py`: `_lost()`'s `and not _only_time_wait(port)` branch
  has no test that combines a refused bind with a stubbed table.
- 2026-11-21-41, `tests/test_hand_gate.py`: the `_hand_digests()` fallback is untested.
- 2026-11-22-4, `tests/test_base_ci.py`: no test calls `base_ci()` outside a repo and asserts that
  it writes nothing.
- 2026-11-22-5, `tests/test_base_ci.py`: only the `test_windows.py` scans cover the `os.replace`
  temp-file write and `newline="\n"`.
- 2026-11-22-28, `tests/test_autopilot.py`: the end-to-end test asserts on the literal
  `"→ decided by autopilot: keep it"` rather than a shared constant tied to `BUILDER_RAISES`.
- 2026-11-22-31, `tests/test_factory_loop.py`: the test sets `start` on a round by hand rather than
  going through `cmd_restart`.
- 2026-11-22-33, `tests/test_autopilot.py`: no case gives a WAVE or LEAVE line an empty reason.
- 2026-11-22-34, `tests/test_autopilot.py`: no case puts a heading-less `LEAVE` before any group.

The `robustness` nits:

- 2026-11-20-46, `plugins/factory/scripts/run_state.py`: `uncarried()` reports `named` only when
  the id is also CONFIRMed. A SETTLED-but-unticked default then reads as "no `- CONFIRM:` line",
  and the mend text points at the wrong fix.
- 2026-11-21-5, `scripts/closing.py`: `origin_trailer()` and `fix_trailers()` catch every
  `Exception`. A coding error there would quietly make origins unknown on every close.
- 2026-11-21-8, `scripts/sdlc.py`: `update_line` returns None when sdlc is read from a folder, so
  a stale `sdlc-factory` install is never mentioned either.
- 2026-11-21-18, `scripts/sdlc.py`: `UPSTREAM_MARKER` is not matched only on the body's first
  line, which is how R12 describes it.
- 2026-11-21-20, `scripts/sdlc.py`: a dotless ssh-alias remote (`user@alias:path`) is not turned
  into `<remote>`.
- 2026-11-21-30, `scripts/sdlc.py`: `--preview` parses `--question`'s clause flags and ignores
  them without saying so.
- 2026-11-22-32, `plugins/factory/skills/autopilot/SKILL.md`: the skill doesn't say to
  single-quote a goal given in the person's own words, so `$`, backticks and `"` in it are not kept
  literal.

## Outcome

Each of the 31 nits above is either fixed in this change or retired as stale, with the reason
written down. A stale nit is one the code has already moved past. Every fixed or retired nit is
held in the change's `entries.md`, so close takes it out of the register. Each `tests` fix is a
test that fails on the gap the nit names and passes with it closed. Each `robustness` fix changes
the code or the skill text the nit names, and a test pins the new behaviour wherever one can.
`./check.sh` passes.

## Affected

- **Area:** the test suite, and small edits to core and factory scripts and one factory skill.
- **Files & components:** the tests named above; `scripts/sdlc.py` (`update_line`, the upstream
  marker match, remote redaction, `preflight --preview`'s flags); `scripts/closing.py`
  (`origin_trailer()`, `fix_trailers()`); `plugins/factory/scripts/run_state.py` (`uncarried()`);
  `plugins/factory/scripts/factory.py` (only if pinning `_hand_digests` needs it);
  `plugins/factory/skills/autopilot/SKILL.md`; `.sdlc/work/inbox.md`, through `entries.md` only.
- **Downstream:** the update hook's one line, ship's preview, upstream bug bodies, close's origin
  trailers, and the approver's mend text. Every other edit is to tests.
- **Contracts:** `scripts/closing.py` is in `[review] sensitive`, so autopilot holds this change
  for the person. Copies pinned across `sdlc.py` and `factory.py` (`_hand_digests`) must stay
  equal. The register is filed and retired only through `entries.md` at close.

## Constraints

- Keep to the 31 nits listed. The `docs` nits (2026-11-22-49) and the `style` and `refactor` nits
  (2026-11-22-51) are other seeds, even where they name the same files.
- Don't narrow `closing.py`'s handling so far that a git or read failure fails a close. Measuring
  and trailers never refuse.
- Every edit to a test or script keeps the Windows rules: `encoding="utf-8"` and `newline="\n"`.

## Open questions

- Which of the 31 nits has the code already moved past? This is answered by checking each nit
  against the code at spec time.
- For 2026-11-21-8, should a factory row be checked when sdlc is read in place, or should the nit
  be retired as following D2?
- For 2026-11-21-30, should `--preview` refuse the clause flags or document that it ignores them?
