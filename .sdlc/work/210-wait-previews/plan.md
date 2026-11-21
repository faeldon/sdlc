---
id: 210
slug: wait-previews
kind: plan
created: 2026-11-21
updated: 2026-11-21
---

# 210 — Each WAIT shows its draft in the dialog's preview · plan

> Written by the factory's builder after reading the code, against `spec.md`'s R1–R13. Read by
> the reviewers and the approver.

## Files to change

- `scripts/sdlc.py`: `PREVIEW_LINES = 40` and `_preview_cut(text, path)` (R4), beside
  `ship_question()`. `_diff_rows(root, path)` lifted out of `_risk_report()` (the one
  `changed_paths()` read against the merge base), which `_risk_report()` keeps using, so its
  JSON doesn't change. `_readable_findings(path)`, the findings.md refusal `cmd_ship_question()`
  had inline, shared with the preview. `ship_preview()` / `cmd_ship_preview()` beside
  `cmd_ship_question()`, reusing `_one_change()`, `findings_entries()`, `work_rel()`. `cli_preflight` gets `--preview`,
  refused together with `--question`; the clause flags are accepted with either (R7).
- `plugins/factory/scripts/factory.py`: the copies `PREVIEW_LINES` and `_preview_cut()`;
  the existing `_section(text, heading)` reused; `_requirements_preview(text, path)` and
  `_spec_preview(root, folder)`, added to `_file_draft()`'s dict (R5); `build_preview(start,
  check, spec)` beside `build_question()`, `spec` being `_upgraded_spec(root, folder)` for an
  upgraded run, set by `cmd_start` next to `question`, `preview: None` everywhere else (R6).
  Reuses `_scaffold()` for a spec.md that's still the scaffold.
- 20 `SKILL.md` WAIT paragraphs (`skills/{intent,spec,ship,close,drop,setup,release,publish,retro,
  uninstall,bug,triage,idea,update}`, `plugins/factory/skills/{spec,build,eval,review,land,
  decide}`): the preview clause, the cut sentence, the fallback (R1–R3, R8–R10). Ship's Step 5
  gains the `preflight <NNN> --preview` call (covered by its `preflight *` rule), its prose
  tightened; it still ends 3 lines over `test_ship_s_skill_stays_under_its_budget`'s 475, so the
  budget is 480 (a default decision in the report). The factory's build and spec skills name the
  new `preview` keys where they list `agent`'s and `start`'s JSON.
- `tests/test_skills.py`: `test_every_wait_asks_in_a_dialog` widened (R1–R3), and
  `test_every_wait_names_its_preview` (R9's table, R8's script outputs), `test_retros_rating_has_no_preview` (R10).
- `tests/test_preflight.py`: `--preview` (R7, R12).
- `tests/test_factory_agent.py`: the spec reply's `preview` (R5, R12).
- `tests/test_factory_depth.py`: `start`'s `preview` (R6), beside the build question's tests.
- `tests/test_modules.py`: the two `_preview_cut()` copies pinned, and both cut 41 / 40 lines (R4).
- `AGENTS.md` (*Skills* invariant), `docs/CONTRIBUTING.md` (**One approval per writing skill**),
  `docs/REFERENCE.md` (`preflight NNN --preview` beside `--question`) (R13).

## Work order

1. **The cut** (R4): `_preview_cut()` in both scripts, tested in `test_modules.py` (41 → 40 +
   `… 1 more line in <path>`; 42 → `… 2 more lines in <path>`; 40 untouched; no path →
   `, shown above`), the copies pinned by AST source equality.
2. **Ship's preview** (R7, R12): `preflight --preview`, through `cli_preflight`, tested by a
   scratch change with findings and a diff; `git status --porcelain` before and after; bad
   findings.md refused like `--question`; `--question --preview` refused.
3. **The spec reply's preview** (R5, R12): `_spec_preview()` in `_file_draft()`, tested through
   `cmd_agent` with the fake claude, a short and a 45-requirement draft.
4. **`start`'s preview** (R6): `build_preview()`, tested for the plain, gate, restart and upgraded
   forms, `--for spec` → null, a refusal → null.
5. **The skills** (R1–R3, R8–R11): the test first (red on all 20), then the paragraphs.
6. **The docs** (R13).

## Tests

- R1, R2, R3: `test_every_wait_asks_in_a_dialog` (the clause with a non-empty `<what>`, the cut
  phrase `keeps its approving part`, `right after what the preview holds`).
- R4: `test_preview_cut_keeps_forty_lines`, `test_preview_cut_is_a_pinned_copy` (test_modules).
- R5, R12: `test_spec_agent_reply_previews_requirements`, `test_a_long_spec_preview_is_cut` (a
  recheck's fresh preview too).
- R6: `test_start_build_previews_the_run`, `test_start_previews_no_gate`,
  `test_start_previews_a_restart`,
  `test_start_previews_an_upgraded_run`, `test_no_preview_for_spec_or_a_refusal`.
- R7, R12: `test_preflight_preview_lists_findings_paths_and_stamp`,
  `test_preflight_preview_without_findings_says_none`, `test_preflight_preview_is_cut_past_forty_lines`,
  `test_preflight_preview_writes_nothing`,
  `test_preflight_preview_refuses_a_bad_findings_md_as_the_question_does`,
  `test_preflight_preview_and_question_are_refused_together`.
- R8, R9: `test_every_wait_names_its_preview` (parametrized over GATED, each skill's key words
  in `PREVIEW_NAMES`), and `test_every_gated_skill_names_its_preview` (the table covers GATED).
- R10: `test_retros_rating_has_no_preview`.
- R11: the existing question/answer tests unedited; the spec's Verification `git diff | grep` run
  as an acceptance check in `checks.md`.
- R13: acceptance check grepping `preview` in the AGENTS.md *Skills* bullet and CONTRIBUTING.md's
  paragraph.

## Formats settled here

- The cut's closing line is singular for one: `… 1 more line in <path>`, else `… <k> more lines in
  <path>`; with no path, `… <k> more lines, shown above`.
- `preflight --preview`: `Findings:` then `F<n> <rank> → <disposition>: <title>` per finding (or
  `Findings: none`), `Paths:` then `<status> <path>` (`R <old> → <new>` for a rename), then the
  stamp line. Cut with no path: ship shows all of it above.
- `start`'s preview: `Gate: …`, `Rounds: full …; light …; at most <max_runs> agent runs`,
  `Models (full): role model, …`, `Models (light): …`, then `Restart: …` or `Upgraded: …` with
  spec.md's Requirements (cut against spec.md). A spec.md still the scaffold says so instead of
  quoting its prompts (see the report's decision).

## Rollback

`git revert` undoes it all: nothing is written outside the repo, no data or state file changes,
and no published name moves. The new JSON keys and the flag are additions; a revert removes them
with the skills that read them.
