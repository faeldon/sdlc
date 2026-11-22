---
id: 227
slug: docs-reviewer
kind: plan
created: 2026-11-22
updated: 2026-11-22
---

# 227 — A docs reviewer checks that a diff leaves no doc saying something false · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `docs` in `ROLES`, `REVIEWERS`, `SCALED`; `JOINING`
  (`UI_REVIEWERS + ("docs",)`) where "joins on its own" is meant (`_depth_keys()`, `depth()`'s
  `beyond`); `ROLE_PASS["docs"] = "context"`; `CONTEXT_DEFAULT` (pinned copy of `sdlc.py`'s
  `CONFIG_KEYS["docs"]["context"]`); `_docs_at()` (base branch's `[docs]`, read as
  `_review_list()` reads `[review]`); `reviewed_docs()` (expand to tracked files, reusing
  `risk_paths()`); `docs_review()` (R4's five clauses); `_rounds_at_depth()` adds `docs`;
  `max_runs()` counts it; `docs_stale()` (doc lines naming a deleted/renamed path, read with
  `git diff --name-status -M`); `cmd_agent()` appends the docs and stale lines to the docs
  reviewer's prompt, as it appends the shots to a UI reviewer's.
- `plugins/factory/agents/reviewer-docs.md` (new): sonnet, `Read, Grep, Glob, Bash`, one pass.
- `plugins/factory/agents/reviewer-code.md`: pass 5 (Context) and the `[context]` tag go.
- `scripts/factory_records.py`: `REVIEWERS` gains `docs`.
- `scripts/sdlc.py`: `CONFIG_KEYS["docs"]["reviewed"] = []`; `AGENT_ROLES` gains `docs`;
  `SHIP_PASSES` gains `ship-docs`; `DOCS_RE` in `PASS_LINES`; `PASS_NAMES`, `PASS_OF`,
  `PASS_SAID`, `_passes_clauses()`' names; `_docs_list_at()` (base branch's `[docs]`) and
  `_docs_applies()` (clauses a, b, c, e); `_passes_report()` gains `docs`; `SHIP_BRANCHES`
  gains `docs.md`.
- `agents/docs.md` (new): core `sdlc:docs`, `Read, Grep, Glob`.
- `skills/ship/docs.md` (new side file) and `skills/ship/SKILL.md` Step 3 (names it, and splits
  the Context pass's questions when it applies).
- Docs: `guide/review.md` context row (then `sdlc.py record`), `docs/REFERENCE.md`
  (`docs.reviewed` in *The docs* and the example), `plugins/factory/README.md` (agents table row,
  reviewer-code's row loses context docs), `docs/FEATURES.md` (`docs.reviewed`, `sdlc:docs`),
  `plugins/factory/skills/build/SKILL.md` (the reviewers sentence), `AGENTS.md` (Ship paragraph).
- Tests: `tests/test_factory_docs.py` (new: R1–R8, R11 factory side), `tests/test_findings.py` /
  `tests/test_preflight*.py` (R9), `tests/test_skills.py` (R10), `tests/test_defaults.py`,
  `tests/test_feature_map.py` and a doc-pins test (R12); existing tests whose rounds now expect
  `docs` (any diff touching a path outside `tests/`) and the `max_runs` bounds are updated.

## Work order

1. Roster: `docs` in the three copies, `ROLE_PASS`, `SCALED`; `JOINING` warnings and `beyond`.
   Tests: model, finding_pass, warn-and-drop, light stays light.
2. The list: `CONTEXT_DEFAULT`, `_docs_at()`, `reviewed_docs()`. Tests: default, `site/`, a
   checkout edit changes nothing.
3. The join: `docs_review()` and `_rounds_at_depth()`, `max_runs()`. One test per clause, R11's.
   Then fix the existing factory tests this ripples into.
4. The prompt: `docs_stale()` and the `cmd_agent()` suffix; `reviewer-docs.md`; reviewer-code's
   pass 5 removed. Tests: prompt names the docs and stale lines; R7's grep test.
5. Ship: `sdlc.py`'s pass, side file, Step 3, `agents/docs.md`. Tests from R9/R10.
6. Docs and their pins (R12), `sdlc.py record`.

## Tests

- R1: `test_docs_runs_on_sonnet`, the existing pins (`test_board.py`, `test_findings.py`).
- R2: `finding_pass` parametrize row for `docs`.
- R3: warn-and-drop on `reviewers = ["code", "docs"]`; a light run that ran `docs` stays light.
- R4: one test per clause (a)–(e), the three (e) cases.
- R5: default list = `CONFIG_KEYS` copy (pin); `reviewed = ["site/"]` gives `site/a.md`; editing
  the checkout's config alone changes nothing.
- R6: the docs reviewer's prompt names the listed docs and the stale line.
- R7: `reviewer-code.md` holds neither `**Context.**` nor `[docs] context`.
- R8: `max_runs` tests updated (+1 a round).
- R9: preflight `passes.docs` applies on `src/a.py`, not on `tests/test_a.py`; question says
  `without the docs review (<why>)`; ship refuses the unsaid line.
- R10: Step 3 names `docs.md`; side-file rules already in `test_skills.py`.
- R11: `reviewers = ["code"]` and `src/a.py` → `docs` expected.
- R12: one assertion per doc edit, as the spec lists.

## Rollback

`git revert` undoes all of it: no data is written outside the repo. A host that set
`[docs] reviewed` keeps a key the reverted plugin ignores (it warns of an unknown key at most).

## Departures from the plan, as built

- **The docs reviewer's prompt** is appended in `cmd_agent()` (`docs_prompt()`), as the UI
  reviewers' shots are, not through a `prompts/` part.
- **Ship's `Docs review:` line is asked only of a `findings.md` that exists.** The docs pass applies
  to nearly every diff, so the security/behaviour rule (refuse an unsaid line, file or no file)
  would refuse every hand ship with no `findings.md`, a change the code already treats as
  predating the file (83 tests across close, archive, adoption). Raised as a `[default]` decision.
- **R12.2's test** reads a `[docs]` key as named when REFERENCE says `docs.<key>` or its `[docs]`
  example holds `<key> = `: `docs.read_before_design` and `docs.explore` appear only in the
  example today, so the spec's "already do" did not hold. `docs.reviewed` is pinned both ways.
- **R12.4**: `test_feature_map.py` doesn't map `CONFIG_KEYS`, so a new test asserts the
  `docs.reviewed` entry and a `ship-<name>` entry for each `PASS_NAMES` name.
- **Existing tests** whose rounds touch a path outside `tests/` now expect `docs`: `REVIEWED` in
  `test_land.py` and `test_train.py`, and the depth, gate, loop and UI tests' lists and
  `max_runs` bounds (+1 a round).
